import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import './style.css'

// 初始化主题
const initTheme = () => {
  try {
    // 尝试从本地存储获取用户主题设置
    const userSettings = localStorage.getItem('userSettings');
    let theme = 'light'; // 默认浅色主题
    
    if (userSettings) {
      const settings = JSON.parse(userSettings);
      theme = settings.theme || 'light';
    }
    
    // 应用主题
    const htmlElement = document.documentElement;
    htmlElement.classList.remove('theme-light', 'theme-dark');
    
    if (theme === 'system') {
      // 如果是跟随系统，检测系统主题
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      htmlElement.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
      
      // 监听系统主题变化
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        htmlElement.classList.remove('theme-light', 'theme-dark');
        htmlElement.classList.add(e.matches ? 'theme-dark' : 'theme-light');
      });
    } else {
      // 直接应用指定的主题
      htmlElement.classList.add(`theme-${theme}`);
    }
    
    // 添加过渡动画类
    htmlElement.classList.add('theme-transition');
    
    console.log('主题初始化完成:', theme);
  } catch (error) {
    console.error('主题初始化失败:', error);
    // 出错时使用默认浅色主题
    document.documentElement.classList.add('theme-light');
  }
};

// 在应用启动前初始化主题
initTheme();

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, {
  locale: zhCn,
})
app.use(router)

app.mount('#app')
