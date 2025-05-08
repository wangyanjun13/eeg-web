# EEG 可视化平台 - 简易部署指南

本文档提供了使用统一脚本部署和管理 EEG 可视化平台的简明步骤。

## 系统要求

- 操作系统: Ubuntu 22.04 或更高版本
- Python 3.8 或更高版本
- Node.js 14 或更高版本
- Redis (可选，推荐用于缓存)

## 目录结构

```
/data/
  ├── eeg_samples/    # EEG 数据目录
  └── eeg-web/        # 应用代码
      ├── backend/    # 后端代码
      ├── frontend/   # 前端代码
      ├── logs/       # 日志文件
      └── eeg-service.sh  # 统一管理脚本
```

## 一键式服务管理

我们提供了一个统一的脚本 `eeg-service.sh` 来管理整个平台。以下是常用命令：

### 安装依赖项

首次部署时，安装所有必要的依赖项：

```bash
cd /data/eeg-web
./eeg-service.sh setup
```

### 启动服务

启动前端和后端服务：

```bash
./eeg-service.sh start
```

启动后，服务将在后台运行，日志保存在 `logs/` 目录中。

### 检查服务状态

查看各服务的运行状态：

```bash
./eeg-service.sh status
```

### 查看日志

查看最新的服务日志：

```bash
./eeg-service.sh logs

# 查看更多日志行
./eeg-service.sh logs 50
```

### 停止服务

停止所有运行中的服务：

```bash
./eeg-service.sh stop
```

### 重启服务

重启所有服务：

```bash
./eeg-service.sh restart
```

## 访问平台

服务启动后，可通过以下地址访问平台：

- 前端界面: https://eeg-visualization-platform.site
- API 接口: https://api.eeg-visualization-platform.site

## 常见问题解决

### 1. 服务无法启动

查看日志以获取详细错误信息：

```bash
./eeg-service.sh logs
```

### 2. Redis 连接问题

如果遇到 Redis 连接问题，请检查 Redis 服务状态：

```bash
redis-cli ping
```

如果 Redis 未运行，可以启动它：

```bash
redis-server --daemonize yes
```

### 3. Cloudflared 配置

如需修改 Cloudflared 配置，编辑 `/etc/cloudflared/config.yml`：

```yaml
tunnel: <tunnel-id>
credentials-file: /etc/cloudflared/<tunnel-id>.json

ingress:
  - hostname: eeg-visualization-platform.site
    service: http://localhost:5173
  - hostname: api.eeg-visualization-platform.site
    service: http://localhost:8000
  - service: http_status:404
```

修改后重启 Cloudflared 服务：

```bash
sudo systemctl restart cloudflared
```

## 更新应用

当代码更新后，使用以下命令重启服务：

```bash
./eeg-service.sh restart
``` 