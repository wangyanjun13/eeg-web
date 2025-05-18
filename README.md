# EEG 可视化平台

#### 技术栈
- 前端: Vue 3 + Vite
- 后端: Fastapi (Python)
- 缓存: Redis
- 数据集来源: https://openneuro.org/

## 基本操作指令
代码迭代更新：
修改后端代码后：sudo ./eeg-service.sh restart-prod
修改前端代码后：sudo ./eeg-service.sh deploy
修改完成后：sudo ./eeg-service.sh health 确保所有服务正常


1. **启动服务**:  sudo ./eeg-service.sh start-prod

2. **停止服务**:  sudo ./eeg-service.sh stop

3. **重启服务**:  sudo ./eeg-service.sh restart-prod
   _注: 此命令会自动重启前端、后端和 Cloudflared 隧道服务_

4. **查看服务状态**:  

./eeg-service.sh status

5. **查看日志**:

./eeg-service.sh logs


## 前端代码更新流程

每次修改前端代码后，只需一条命令即可完成构建、部署和配置更新：

给权限：  sudo chmod -R 777 /data/eeg-web/frontend/dist
sudo ./eeg-service.sh deploy

不管用的话：
   cd /data/eeg-web/frontend
   npm install
   npm run build

单独构建前端：  sudo ./eeg-service.sh build


## 后端代码更新流程

**安装新的Python依赖**:

sudo -E /data/venv/bin/python -m pip install -r backend/requirements.txt
sudo ./eeg-service.sh restart-prod

**修改后端代码后重启服务**:  sudo ./eeg-service.sh restart-prod



## 常见问题解决

1. **502 Bad Gateway 错误**或者XML XT错误:

   sudo ./eeg-service.sh update-cf prod
   sudo systemctl restart cloudflared


2. **前端不显示最新更改**:

   sudo ./eeg-service.sh deploy


后端日志：  tail -n 50 logs/backend.log

缺少依赖，安装相应的包：   sudo -E /data/venv/bin/python -m pip install 缺少的包名==版本号

重启后端服务： sudo ./eeg-service.sh restart-prod


4. **Python包安装问题**:
   - 确保使用正确的虚拟环境安装包：

     sudo -E /data/venv/bin/python -m pip install 包名==版本号

   - 不要使用 `pip` 或 `pip3` 直接安装，而是使用 `python -m pip`

访问地址:
- 前端: https://eeg-visualization-platform.site
- API: https://api.eeg-visualization-platform.site