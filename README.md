# EEG 可视化平台

#### 技术栈
- 前端: Vue 3 + Vite
- 后端: Fastapi (Python)
- 缓存: Redis
- 数据集来源: https://openneuro.org/

## 基本操作指令

1. **启动服务**:
   ```bash
   sudo ./eeg-service.sh start-prod
   ```

2. **停止服务**:
   ```bash
   sudo ./eeg-service.sh stop
   ```

3. **重启服务**:
   ```bash
   sudo ./eeg-service.sh restart-prod
   ```
   _注: 此命令会自动重启前端、后端和 Cloudflared 隧道服务_

4. **查看服务状态**:
   ```bash
   ./eeg-service.sh status
   ```

5. **查看日志**:
   ```bash
   ./eeg-service.sh logs
   ```

## 前端代码更新流程

每次修改前端代码后，只需一条命令即可完成构建、部署和配置更新：

```bash
（  sudo chmod -R 777 /data/eeg-web/frontend/dist  ）
sudo ./eeg-service.sh deploy
```

这个命令将自动：
1. 使用合适的 Node.js 版本构建前端
2. 确保 Nginx 配置正确
3. 重启 Nginx 服务
4. 更新 Cloudflared 隧道配置
5. 完成所有必要的设置

单独构建前端：
```bash
sudo ./eeg-service.sh build
```

## 后端代码更新流程

1. **修改后端代码后重启服务**:
   ```bash
   sudo ./eeg-service.sh restart-prod
   ```

2. **安装新的Python依赖**:
   如果添加了新的依赖，需要先安装然后再重启服务：
   ```bash
   sudo -E /data/venv/bin/python -m pip install 新依赖包名称==版本号
   sudo ./eeg-service.sh restart-prod
   ```

3. **更新requirements.txt**:
   在添加新依赖后，记得更新requirements.txt文件：
   ```bash
   source /data/venv/bin/activate
   pip freeze > backend/requirements.txt
   ```

## 常见问题解决

1. **502 Bad Gateway 错误**:
   ```bash
   sudo ./eeg-service.sh update-cf prod
   sudo systemctl restart cloudflared
   ```

2. **前端不显示最新更改**:
   ```bash
   sudo ./eeg-service.sh deploy
   ```

3. **后端500错误**:
   - 检查日志文件找出具体错误：
     ```bash
     tail -n 50 logs/backend.log
     ```
   - 如果是缺少依赖，安装相应的包：
     ```bash
     sudo -E /data/venv/bin/python -m pip install 缺少的包名==版本号
     ```
   - 重启后端服务：
     ```bash
     sudo ./eeg-service.sh restart-prod
     ```

4. **Python包安装问题**:
   - 确保使用正确的虚拟环境安装包：
     ```bash
     sudo -E /data/venv/bin/python -m pip install 包名==版本号
     ```
   - 不要使用 `pip` 或 `pip3` 直接安装，而是使用 `python -m pip`

5. **中国网络访问问题**:
   - 确保 Cloudflare 路由设置为亚太区域 (ap)
   - 如需手动修改, 登录 Cloudflare 控制台，在 "一步完成所有操作" > "网络" > "隧道" 中更新路由设置

访问地址:
- 前端: https://eeg-visualization-platform.site
- API: https://api.eeg-visualization-platform.site