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
   sudo ./eeg-service.sh status
   ```

5. **查看日志**:
   ```bash
   sudo ./eeg-service.sh logs
   ```

## Cloudflare 隧道管理

1. **更新隧道配置**:
   ```bash
   sudo ./eeg-service.sh update-cf prod
   ```
   _注: 此命令会自动重启 Cloudflared 服务_

2. **检查隧道状态**:
   ```bash
   sudo systemctl status cloudflared
   ```

3. **查看隧道日志**:
   ```bash
   sudo journalctl -u cloudflared -n 50 --no-pager
   ```

4. **手动重启隧道**（如果需要）:
   ```bash
   sudo systemctl restart cloudflared
   ```

## 开发流程

1. **代码修改**:
   - 直接修改前端或后端代码
   - 修改不会影响正在运行的服务

2. **前端构建**:
   ```bash
   sudo ./eeg-service.sh build
   ```
   _注: 此命令会构建前端代码生成生产版本_

3. **应用更改**:
   ```bash
   sudo ./eeg-service.sh restart-prod
   ```
   _注: 执行此命令后新代码才会生效_

访问地址:
- 前端: https://eeg-visualization-platform.site
- API: https://api.eeg-visualization-platform.site