import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd())
  
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': {
          target: 'https://api.eeg-visualization-platform.site',  // 直接使用生产API地址
          changeOrigin: true,
          secure: true,
          rewrite: (path) => path
        }
      },
      hmr: {
        protocol: 'ws',
        host: 'eeg-visualization-platform.site',
        clientPort: 443,
        path: 'hmr/',
        overlay: false,
      },
      allowedHosts: [
        'eeg-visualization-platform.site', 
        'www.eeg-visualization-platform.site',
        'api.eeg-visualization-platform.site',
        'localhost',
        '100.111.181.42',
        '.eeg-visualization-platform.site'
      ],
      cors: {
        origin: '*',
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: '*',
        credentials: true
      },
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false
    }
  }
})
