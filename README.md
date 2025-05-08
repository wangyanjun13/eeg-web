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

## 前端代码更新流程 (简化版)

每次修改前端代码后，只需一条命令即可完成构建、部署和配置更新：

```bash
sudo ./eeg-service.sh deploy
```

这个命令将自动：
1. 使用合适的 Node.js 版本构建前端
2. 确保 Nginx 配置正确
3. 重启 Nginx 服务
4. 更新 Cloudflared 隧道配置
5. 完成所有必要的设置

**注意**：必须使用 `sudo` 运行此命令，才能正确配置所有服务。

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

3. **中国网络访问问题**:
   - 确保 Cloudflare 路由设置为亚太区域 (ap)
   - 如需手动修改, 登录 Cloudflare 控制台，在 "一步完成所有操作" > "网络" > "隧道" 中更新路由设置

访问地址:
- 前端: https://eeg-visualization-platform.site
- API: https://api.eeg-visualization-platform.site