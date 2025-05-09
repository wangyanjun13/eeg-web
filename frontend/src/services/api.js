import axios from 'axios';

// 外网访问必须使用完整URL
const API_BASE_URL = 'https://api.eeg-visualization-platform.site';

// 创建 Axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`发送请求到: ${config.baseURL}${config.url}`, config.params || config.data);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器，处理响应数据和常见http错误
api.interceptors.response.use(
  (response) => {
    console.log(`收到响应: ${response.config.url}`, response.data);
    return response.data;
  },
  (error) => {
    console.error('API请求错误:', error);
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未授权，跳转到登录页
          localStorage.removeItem('token');
          window.location.href = '/login';
          break;
        case 403:
          // 权限不足
          console.error('权限不足');
          break;
        case 404:
          // 资源不存在
          console.error('请求的资源不存在');
          break;
        case 500:
          // 服务器错误
          console.error('服务器错误');
          break;
        default:
          console.error('请求失败');
      }
    }
    return Promise.reject(error);
  }
);

export default api; 