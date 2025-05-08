#!/bin/bash

# 设置错误处理
set -e

WORKDIR="/data/eeg-web"
FRONTEND_DIR="$WORKDIR/frontend"
BACKEND_DIR="$WORKDIR/backend"
LOG_DIR="$WORKDIR/logs"

echo "===== 配置 EEG 可视化平台运行环境 ====="
echo "时间: $(date)"
echo "工作目录: $WORKDIR"

# 创建日志目录
mkdir -p $LOG_DIR

# 安装系统依赖
echo "正在安装系统依赖项..."
apt-get update
apt-get install -y python3 python3-pip python3-venv curl wget git redis-server

# 确保Redis服务启动
echo "配置并启动Redis服务..."
systemctl enable redis-server
systemctl start redis-server
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis服务运行正常"
else
    echo "❌ Redis服务启动失败，请检查日志"
    systemctl status redis-server
fi

# 安装Node.js和npm
echo "检查Node.js和npm安装状态..."
if ! command -v node &> /dev/null; then
    echo "安装Node.js和npm..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
else
    echo "Node.js已安装: $(node -v)"
fi
echo "npm版本: $(npm -v)"

# 设置npm镜像
echo "配置npm镜像..."
npm config set registry https://registry.npmmirror.com

# 安装后端依赖
echo "安装后端Python依赖..."
cd $BACKEND_DIR
pip3 install -r requirements.txt

# 安装前端依赖
echo "安装前端npm依赖..."
cd $FRONTEND_DIR
npm install

# 确保脚本有执行权限
echo "设置脚本执行权限..."
cd $WORKDIR
chmod +x start-server.sh stop-server.sh check-status.sh update-cloudflared.sh

echo "===== 环境配置完成 ====="
echo "现在您可以运行 ./start-server.sh 启动服务"
echo "或者运行 ./check-status.sh 检查系统状态" 