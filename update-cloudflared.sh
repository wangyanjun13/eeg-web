#!/bin/bash

# 该脚本用于更新 Cloudflared 配置，确保隧道正确指向服务

TUNNEL_UUID="6f98c3c1-9d2d-422a-a6d6-0e28cb21edd0"
CREDENTIALS_FILE="/etc/cloudflared/${TUNNEL_UUID}.json"
CONFIG_FILE="/etc/cloudflared/config.yml"
BACKUP_FILE="/etc/cloudflared/config.yml.bak"

# 当前服务器 IP 地址和端口
FRONTEND_PORT=5173
BACKEND_PORT=8000

echo "===== 更新 Cloudflare 隧道配置 ====="

# 检查 sudo 权限
if [ "$EUID" -ne 0 ]; then
    echo "需要 sudo 权限来修改 Cloudflared 配置"
    echo "请使用 sudo $0 运行此脚本"
    exit 1
fi

# 备份当前配置
if [ -f "$CONFIG_FILE" ]; then
    echo "备份当前配置到 $BACKUP_FILE"
    cp "$CONFIG_FILE" "$BACKUP_FILE"
fi

# 创建新的配置文件
echo "创建新的 Cloudflared 配置..."
cat > "$CONFIG_FILE" <<EOL
tunnel: ${TUNNEL_UUID}
credentials-file: ${CREDENTIALS_FILE}

ingress:
  - hostname: eeg-visualization-platform.site
    service: http://localhost:${FRONTEND_PORT}
  - hostname: api.eeg-visualization-platform.site
    service: http://localhost:${BACKEND_PORT}
    originRequest:
      connectTimeout: 30s
      noTLSVerify: true
  - service: http_status:404
EOL

echo "配置文件已更新，正在重启 Cloudflared 服务..."
systemctl restart cloudflared

# 检查服务状态
echo "等待服务启动..."
sleep 2
CLOUDFLARED_STATUS=$(systemctl is-active cloudflared)

if [ "$CLOUDFLARED_STATUS" = "active" ]; then
    echo "✅ Cloudflared 服务已成功重启"
else
    echo "❌ Cloudflared 服务启动失败，状态: $CLOUDFLARED_STATUS"
    echo "查看日志获取更多信息:"
    journalctl -u cloudflared -n 10
fi

echo "===== 配置更新完成 =====" 