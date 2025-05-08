# 构建阶段
FROM node:18 as build

WORKDIR /app

# 复制项目文件
COPY . .

# 设置 npm 镜像为阿里云镜像
RUN npm config set registry https://registry.npmmirror.com

# 安装依赖并构建项目
RUN npm install
RUN npm run build

# 部署阶段
FROM nginx:stable-alpine

# 从构建阶段复制构建结果到 nginx 目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 