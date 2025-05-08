#!/bin/bash

WORKDIR="/data/eeg-web"
FRONTEND_DIR="$WORKDIR/frontend"
BACKEND_DIR="$WORKDIR/backend"
DATA_DIR="/data/eeg_samples"
LOG_DIR="$WORKDIR/logs"
CLOUDFLARED_CONFIG="/etc/cloudflared/config.yml"
TUNNEL_UUID="6f98c3c1-9d2d-422a-a6d6-0e28cb21edd0"
CREDENTIALS_FILE="/etc/cloudflared/${TUNNEL_UUID}.json"
USE_PRODUCTION=false  # 使用生产模式的标志
VENV_PATH="/data/venv"  # Python虚拟环境路径

# 创建日志目录
mkdir -p $LOG_DIR

# 帮助信息
show_help() {
    echo "EEG可视化平台服务管理工具"
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start           - 启动前端和后端服务（开发模式）"
    echo "  start-prod      - 启动前端和后端服务（生产模式，使用Nginx）"
    echo "  stop            - 停止所有服务"
    echo "  status          - 显示服务状态"
    echo "  restart         - 重启所有服务"
    echo "  restart-prod    - 重启所有服务（生产模式）"
    echo "  logs            - 显示日志"
    echo "  setup           - 安装依赖项"
    echo "  update-cf       - 更新Cloudflared配置"
    echo "  build           - 构建前端生产版本"
    echo "  deploy          - 一键部署前端更新"
    echo "  nginx-setup     - 设置Nginx配置文件"
    echo "  help            - 显示帮助信息"
}

# 启动服务
start_services() {
    local mode=$1
    
    echo "===== 启动 EEG 可视化平台 ====="
    echo "时间: $(date)"
    
    if [ "$mode" = "prod" ]; then
        echo "模式: 生产模式（使用Nginx）"
        USE_PRODUCTION=true
    else
        echo "模式: 开发模式（使用Vite开发服务器）"
        USE_PRODUCTION=false
    fi
    
    # 检查并启动Redis
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "正在启动Redis服务..."
        redis-server --daemonize yes || echo "⚠️ Redis启动失败，将使用内存缓存模式"
    else
        echo "✅ Redis服务正常运行"
    fi
    
    # 停止已有服务
    stop_services quiet
    
    # 启动后端 - 使用setsid确保进程与终端分离
    echo "启动后端服务..."
    cd $BACKEND_DIR
    echo "使用Python虚拟环境: $VENV_PATH"
    (setsid $VENV_PATH/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > $LOG_DIR/backend.log 2>&1 </dev/null) &
    BACKEND_PID=$!
    echo $BACKEND_PID > $LOG_DIR/backend.pid
    echo "后端服务已启动，PID: $BACKEND_PID"
    
    # 等待后端启动
    echo "等待后端服务启动..."
    sleep 5
    
    # 启动前端服务
    if [ "$USE_PRODUCTION" = true ]; then
        # 检查Nginx是否安装
        if ! command -v nginx > /dev/null; then
            echo "⚠️ Nginx未安装，无法使用生产模式"
            echo "请先安装Nginx: sudo apt-get install nginx"
            exit 1
        fi
        
        # 检查前端构建是否存在
        if [ ! -d "$FRONTEND_DIR/dist" ]; then
            echo "⚠️ 前端构建目录不存在，先构建前端"
            build_frontend
        fi
        
        # 检查Nginx配置
        if [ ! -f "/etc/nginx/conf.d/eeg-frontend.conf" ]; then
            echo "⚠️ Nginx配置不存在，创建配置文件"
            setup_nginx
        fi
        
        # 确保Nginx运行
        echo "启动前端服务（Nginx）..."
        sudo systemctl restart nginx
        echo "前端服务已启动（使用Nginx）"
        
        # 更新Cloudflared配置
        if [ "$EUID" -eq 0 ]; then
            FRONTEND_PORT=80
            update_prod_cloudflared
        else
            echo "⚠️ 如需更新Cloudflared配置，请以root权限运行: sudo $0 update-cf"
        fi
    else
        # 启动开发服务器
        echo "启动前端服务（开发模式）..."
        cd $FRONTEND_DIR
        
        # 确保端口5173空闲
        echo "确保前端端口5173空闲..."
        fuser -k 5173/tcp 2>/dev/null || true
        sleep 2
        
        npm config set registry https://registry.npmmirror.com
        (setsid npm run dev -- --host > $LOG_DIR/frontend.log 2>&1 </dev/null) &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > $LOG_DIR/frontend.pid
        echo "前端服务已启动，PID: $FRONTEND_PID"
        
        # 等待前端启动完全，然后检测端口
        sleep 5
        
        # 检查前端实际运行端口
        check_frontend_port
    fi
    
    # 确认服务
    check_running_status
    
    # 显示访问信息
    echo "===== 服务启动完成 ====="
    echo "访问地址:"
    echo "  前端: https://eeg-visualization-platform.site"
    echo "  API: https://api.eeg-visualization-platform.site"
    echo ""
    echo "运行 '$0 status' 查看服务状态"
    echo "运行 '$0 logs' 查看日志"
}

# 设置Nginx配置
setup_nginx() {
    echo "===== 设置Nginx配置 ====="
    
    if [ "$EUID" -ne 0 ]; then
        echo "⚠️ 需要root权限设置Nginx"
        echo "请使用 sudo $0 nginx-setup 命令"
        return 1
    fi
    
    # 创建配置文件
    cat > /etc/nginx/conf.d/eeg-frontend.conf <<EOF
server {
    listen 80;
    server_name localhost eeg-visualization-platform.site www.eeg-visualization-platform.site;
    
    # CORS配置
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
    
    # 处理OPTIONS请求
    if (\$request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        add_header 'Content-Length' 0;
        return 204;
    }
    
    # gzip 配置
    gzip on;
    gzip_min_length 1k;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/javascript application/javascript application/json application/xml;
    gzip_vary on;
    
    # 静态资源
    location / {
        root $FRONTEND_DIR/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;  # 支持前端路由
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # 错误页面
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root $FRONTEND_DIR/dist;
    }
}
EOF
    
    echo "✅ Nginx配置已创建"
    
    # 检查配置语法
    if nginx -t; then
        echo "✅ Nginx配置语法正确"
        systemctl restart nginx
        echo "✅ Nginx已重启"
    else
        echo "❌ Nginx配置有语法错误，请检查配置"
    fi
}

# 更新生产模式Cloudflared配置
update_prod_cloudflared() {
    if [ "$EUID" -ne 0 ]; then
        echo "需要root权限来更新Cloudflared配置"
        return 1
    fi
    
    echo "更新Cloudflared配置（生产模式）..."
    
    # 备份当前配置
    if [ -f "$CLOUDFLARED_CONFIG" ]; then
        cp "$CLOUDFLARED_CONFIG" "${CLOUDFLARED_CONFIG}.bak"
    fi
    
    # 创建新的配置文件
    cat > "$CLOUDFLARED_CONFIG" <<EOF
tunnel: ${TUNNEL_UUID}
credentials-file: ${CREDENTIALS_FILE}

ingress:
  - hostname: eeg-visualization-platform.site
    service: http://127.0.0.1:80
    originRequest:
      originServerName: localhost
      noTLSVerify: true
  - hostname: api.eeg-visualization-platform.site
    service: http://127.0.0.1:8000
    originRequest:
      connectTimeout: 30s
      noTLSVerify: true
  - service: http_status:404
EOF
    
    echo "Cloudflared配置已更新，重启服务..."
    systemctl restart cloudflared
    
    # 检查服务状态
    sleep 2
    if systemctl is-active cloudflared > /dev/null; then
        echo "✅ Cloudflared服务已成功重启"
    else
        echo "❌ Cloudflared服务启动失败"
    fi
}

# 构建前端生产版本（安全且可靠的方法）
build_frontend() {
    echo "===== 构建前端生产版本 ====="
    echo "时间: $(date)"
    
    # 检查是否以 root 用户运行
    if [ "$EUID" -eq 0 ]; then
        echo "检测到您正在使用 root 权限运行构建命令"
        echo "为确保使用正确的 Node.js 版本，将使用临时目录构建方法"
        
        # 获取非 root 用户
        ACTUAL_USER=$(logname 2>/dev/null || echo "${SUDO_USER:-${USER}}")
        ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)
        
        # 创建临时构建目录
        BUILD_DIR="/tmp/eeg-build-$(date +%s)"
        mkdir -p $BUILD_DIR
        cp -r $FRONTEND_DIR/* $BUILD_DIR/
        chown -R $ACTUAL_USER:$ACTUAL_USER $BUILD_DIR
        
        echo "使用用户 $ACTUAL_USER 的环境构建前端"
        
        # 使用实际用户构建
        su - $ACTUAL_USER -c "cd $BUILD_DIR && \
            export NVM_DIR=\"$ACTUAL_HOME/.nvm\" && \
            [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && \
            npm config set registry https://registry.npmmirror.com && \
            npm install && \
            npm run build"
        
        BUILD_STATUS=$?
        
        if [ $BUILD_STATUS -eq 0 ]; then
            echo "✅ 前端构建成功，复制构建结果..."
            
            # 如果 dist 目录存在，先备份
            if [ -d "$FRONTEND_DIR/dist" ]; then
                echo "备份现有的 dist 目录..."
                mv $FRONTEND_DIR/dist $FRONTEND_DIR/dist.bak.$(date +%s)
            fi
            
            # 复制构建结果
            cp -r $BUILD_DIR/dist $FRONTEND_DIR/
            echo "✅ 前端构建完成，输出目录: $FRONTEND_DIR/dist"
            
            # 清理临时目录
            rm -rf $BUILD_DIR
            return 0
        else
            echo "❌ 前端构建失败，请查看上面的错误信息"
            rm -rf $BUILD_DIR
            return 1
        fi
    else
        # 非 root 用户直接构建
        echo "非 root 用户构建模式"
        
        # 设置 Node.js 环境
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        
        # 检查 Node.js 版本
        NODE_VERSION=$(node -v)
        echo "使用 Node.js 版本: $NODE_VERSION"
        
        # 检查 Node.js 版本是否满足要求
        if [[ "$NODE_VERSION" =~ ^v([0-9]+) ]] && [ "${BASH_REMATCH[1]}" -lt 14 ]; then
            echo "⚠️ 警告: 当前 Node.js 版本 ($NODE_VERSION) 低于项目所需的最低版本 (v14.18.0)"
            echo "尝试使用 nvm 切换到合适的版本..."
            
            if command -v nvm &> /dev/null; then
                nvm use 14 2>/dev/null || nvm use 16 2>/dev/null || nvm use 18 2>/dev/null || true
                NODE_VERSION=$(node -v)
                echo "现在使用 Node.js 版本: $NODE_VERSION"
            else
                echo "⚠️ nvm 未安装或未正确配置，继续使用当前版本"
            fi
        fi
        
        # 进入前端目录
        cd $FRONTEND_DIR
        
        # 设置 npm 镜像
        npm config set registry https://registry.npmmirror.com
        
        # 安装依赖
        echo "安装依赖..."
        npm install
        
        # 构建生产版本
        echo "构建生产版本..."
        npm run build
        
        if [ $? -eq 0 ]; then
            echo "✅ 前端构建成功，输出目录: $FRONTEND_DIR/dist"
            return 0
        else
            echo "❌ 前端构建失败，请查看错误信息"
            return 1
        fi
    fi
}

# 部署前端和更新所有服务（一步完成所有操作）
deploy_frontend() {
    echo "===== 一键部署前端更新 ====="
    echo "时间: $(date)"
    
    # 1. 构建前端
    build_frontend
    if [ $? -ne 0 ]; then
        echo "❌ 前端构建失败，部署中止"
        return 1
    fi
    
    # 2. 确保 Nginx 配置正确
    if [ "$EUID" -eq 0 ]; then
        if [ ! -f "/etc/nginx/conf.d/eeg-frontend.conf" ]; then
            echo "配置 Nginx..."
            setup_nginx
        fi
    else
        echo "⚠️ 需要 root 权限配置 Nginx"
        echo "请使用 sudo $0 deploy 命令进行完整部署"
        return 1
    fi
    
    # 3. 重启 Nginx
    if [ "$EUID" -eq 0 ]; then
        echo "重启 Nginx..."
        systemctl restart nginx
    else
        echo "⚠️ 需要 root 权限重启 Nginx"
        echo "请使用 sudo $0 deploy 命令进行完整部署"
        return 1
    fi
    
    # 4. 更新 Cloudflared 配置
    if [ "$EUID" -eq 0 ]; then
        echo "更新 Cloudflared 配置..."
        update_prod_cloudflared
    else
        echo "⚠️ 需要 root 权限更新 Cloudflared 配置"
        echo "请使用 sudo $0 deploy 命令进行完整部署"
        return 1
    fi
    
    # 5. 显示部署完成信息
    echo "===== 前端部署完成 ====="
    echo "访问地址: https://eeg-visualization-platform.site"
    echo "检查服务状态: $0 status"
    
    return 0
}

# 检查服务是否真的在运行
check_running_status() {
    # 检查后端是否真的在运行
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        BACKEND_RUNNING=true
    else
        BACKEND_RUNNING=false
        echo "⚠️ 后端服务可能未成功启动，查看日志: $LOG_DIR/backend.log"
    fi
    
    # 检查前端是否真的在运行
    if pgrep -f "npm run dev" > /dev/null; then
        FRONTEND_RUNNING=true
    else
        FRONTEND_RUNNING=false
        echo "⚠️ 前端服务可能未成功启动，查看日志: $LOG_DIR/frontend.log"
    fi
}

# 检查前端实际运行端口并更新Cloudflared配置
check_frontend_port() {
    if grep -q "Port 5173 is in use" $LOG_DIR/frontend.log; then
        if grep -q "Local:.*http://localhost:[0-9]\+" $LOG_DIR/frontend.log; then
            FRONTEND_PORT=$(grep "Local:.*http://localhost:[0-9]\+" $LOG_DIR/frontend.log | sed -E 's/.*http:\/\/localhost:([0-9]+).*/\1/')
            echo "检测到前端运行在端口 $FRONTEND_PORT，不是默认的5173"
            echo "需要更新Cloudflared配置，请运行: sudo $0 update-cf"
        fi
    fi
}

# 更新Cloudflared配置
update_cloudflared() {
    if [ "$EUID" -ne 0 ]; then
        echo "需要root权限来更新Cloudflared配置"
        echo "请使用 sudo $0 update-cf 命令"
        exit 1
    fi
    
    echo "===== 更新Cloudflared配置 ====="
    echo "时间: $(date)"
    
    # 检测前端实际运行端口
    if grep -q "Local:.*http://localhost:[0-9]\+" $LOG_DIR/frontend.log; then
        FRONTEND_PORT=$(grep "Local:.*http://localhost:[0-9]\+" $LOG_DIR/frontend.log | sed -E 's/.*http:\/\/localhost:([0-9]+).*/\1/')
        echo "检测到前端运行在端口 $FRONTEND_PORT"
    else
        FRONTEND_PORT=5173
        echo "使用默认前端端口 $FRONTEND_PORT"
    fi
    
    BACKEND_PORT=8000
    echo "后端端口: $BACKEND_PORT"
    
    # 备份当前配置
    if [ -f "$CLOUDFLARED_CONFIG" ]; then
        echo "备份当前配置到 ${CLOUDFLARED_CONFIG}.bak"
        cp "$CLOUDFLARED_CONFIG" "${CLOUDFLARED_CONFIG}.bak"
    fi
    
    # 创建新的配置文件
    echo "创建新的配置..."
    cat > "$CLOUDFLARED_CONFIG" <<EOF
tunnel: ${TUNNEL_UUID}
credentials-file: ${CREDENTIALS_FILE}

ingress:
  - hostname: eeg-visualization-platform.site
    service: http://127.0.0.1:${FRONTEND_PORT}
  - hostname: api.eeg-visualization-platform.site
    service: http://127.0.0.1:${BACKEND_PORT}
    originRequest:
      connectTimeout: 30s
      noTLSVerify: true
  - service: http_status:404
EOF
    
    echo "配置已更新，重启Cloudflared服务..."
    systemctl restart cloudflared
    
    # 检查服务状态
    echo "等待服务启动..."
    sleep 2
    if systemctl is-active cloudflared > /dev/null; then
        echo "✅ Cloudflared服务已成功重启"
    else
        echo "❌ Cloudflared服务启动失败"
        echo "查看日志: journalctl -u cloudflared -n 10"
    fi
}

# 停止服务
stop_services() {
    if [ "$1" != "quiet" ]; then
        echo "===== 停止 EEG 可视化平台 ====="
        echo "时间: $(date)"
    fi
    
    # 停止前端
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        PID=$(cat $LOG_DIR/frontend.pid)
        if ps -p $PID > /dev/null; then
            kill $PID
            echo "前端服务已停止 (PID: $PID)"
            # 等待进程真正结束
            sleep 2
            if ps -p $PID > /dev/null; then
                echo "前端进程未响应，强制终止..."
                kill -9 $PID
            fi
        fi
        rm -f $LOG_DIR/frontend.pid
    fi
    
    # 停止后端
    if [ -f "$LOG_DIR/backend.pid" ]; then
        PID=$(cat $LOG_DIR/backend.pid)
        if ps -p $PID > /dev/null; then
            kill $PID
            echo "后端服务已停止 (PID: $PID)"
            # 等待进程真正结束
            sleep 2
            if ps -p $PID > /dev/null; then
                echo "后端进程未响应，强制终止..."
                kill -9 $PID
            fi
        fi
        rm -f $LOG_DIR/backend.pid
    fi
    
    # 清理可能残留的进程
    echo "清理所有残留进程..."
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "npm run dev -- --host" 2>/dev/null || true
    pkill -f "node .*vite" 2>/dev/null || true
    
    # 确保端口释放
    if [ "$1" != "quiet" ]; then
        echo "确保端口5173已释放..."
        fuser -k 5173/tcp 2>/dev/null || true
        fuser -k 5174/tcp 2>/dev/null || true
        fuser -k 5175/tcp 2>/dev/null || true
        fuser -k 5176/tcp 2>/dev/null || true
    fi
    
    if [ "$1" != "quiet" ]; then
        echo "所有服务已停止"
    fi
}

# 检查状态
check_status() {
    echo "===== EEG 可视化平台状态 ====="
    echo "时间: $(date)"
    
    # 检查后端状态
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        BACKEND_PID=$(pgrep -f "uvicorn app.main:app")
        echo "✅ 后端服务: 运行中 (PID: $BACKEND_PID)"
    else
        echo "❌ 后端服务: 已停止"
    fi
    
    # 检查前端状态
    if [ "$USE_PRODUCTION" = true ] || systemctl is-active nginx > /dev/null; then
        echo "✅ 前端服务: 运行中 (使用 Nginx 服务)"
    elif pgrep -f "npm run dev" > /dev/null; then
        FRONTEND_PID=$(pgrep -f "npm run dev")
        echo "✅ 前端服务: 运行中 (PID: $FRONTEND_PID)"
    else
        echo "❌ 前端服务: 已停止"
    fi
    
    # 检查Redis状态
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis服务: 运行中"
    else
        echo "❌ Redis服务: 已停止"
    fi
    
    # 检查API连通性
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API连通性: 正常"
    else
        echo "❌ API连通性: 不可用"
    fi
    
    # 检查前端端口
    if [ "$USE_PRODUCTION" = true ] || systemctl is-active nginx > /dev/null; then
        echo "ℹ️ 前端模式: 生产模式 (Nginx)"
        # 检查Cloudflared配置是否匹配Nginx端口
        if [ -f "$CLOUDFLARED_CONFIG" ]; then
            if grep -q "service: http://127.0.0.1:80" "$CLOUDFLARED_CONFIG"; then
                echo "✅ Cloudflared配置: 正常 (Nginx 生产模式)"
            else
                echo "⚠️ Cloudflared配置: 不匹配 (需要更新)"
                echo "   运行 'sudo $0 update-cf prod' 更新配置"
            fi
        fi
    elif grep -q "Local:.*http://localhost:[0-9]\+" $LOG_DIR/frontend.log 2>/dev/null; then
        FRONTEND_PORT=$(grep "Local:.*http://localhost:[0-9]\+" $LOG_DIR/frontend.log | sed -E 's/.*http:\/\/localhost:([0-9]+).*/\1/')
        echo "ℹ️ 前端端口: $FRONTEND_PORT"
        
        # 检查Cloudflared配置是否匹配
        if [ -f "$CLOUDFLARED_CONFIG" ]; then
            if grep -q "service: http://127.0.0.1:$FRONTEND_PORT" "$CLOUDFLARED_CONFIG"; then
                echo "✅ Cloudflared配置: 正常 (与前端端口匹配)"
            else
                echo "⚠️ Cloudflared配置: 不匹配 (需要更新)"
                echo "   运行 'sudo $0 update-cf' 更新配置"
            fi
        fi
    fi
    
    echo ""
    echo "系统资源:"
    echo "  CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')%"
    echo "  内存: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    echo "  磁盘: $(df -h /data | grep /data | awk '{print $3 "/" $2 " (" $5 ")"}')"
}

# 显示日志
show_logs() {
    local num_lines=${1:-20}
    
    echo "===== 服务日志 ====="
    
    if [ -f "$LOG_DIR/backend.log" ]; then
        echo "后端日志 (最新${num_lines}行):"
        echo "-------------------"
        tail -n $num_lines $LOG_DIR/backend.log
    else
        echo "❌ 后端日志文件不存在"
    fi
    
    echo ""
    
    if [ -f "$LOG_DIR/frontend.log" ]; then
        echo "前端日志 (最新${num_lines}行):"
        echo "-------------------"
        tail -n $num_lines $LOG_DIR/frontend.log
    else
        echo "❌ 前端日志文件不存在"
    fi
}

# 安装依赖
setup_env() {
    echo "===== 安装依赖项 ====="
    
    # 安装后端依赖
    echo "安装后端依赖..."
    cd $BACKEND_DIR
    pip3 install -r requirements.txt
    
    # 安装前端依赖
    echo "安装前端依赖..."
    cd $FRONTEND_DIR
    npm config set registry https://registry.npmmirror.com
    npm install
    
    echo "依赖项安装完成"
}

# 主命令处理
case "$1" in
    start)
        start_services dev
        ;;
    start-prod)
        start_services prod
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services dev
        ;;
    restart-prod)
        stop_services
        start_services prod
        ;;
    status)
        check_status
        ;;
    logs)
        if [ "$2" ]; then
            show_logs $2
        else
            show_logs 20
        fi
        ;;
    setup)
        setup_env
        ;;
    update-cf)
        if [ "$2" = "prod" ]; then
            update_prod_cloudflared
        else
            update_cloudflared
        fi
        ;;
    build)
        build_frontend
        ;;
    deploy)
        deploy_frontend
        ;;
    nginx-setup)
        setup_nginx
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            echo "未知命令: $1"
            echo "运行 '$0 help' 获取帮助"
        fi
        ;;
esac 