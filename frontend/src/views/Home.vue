<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

// 路由实例
const router = useRouter();

// 用户信息
const userInfo = ref(null);

// 特点列表
const features = [
  {
    title: '数据集分析',
    description: '提供多种EEG数据集的浏览、可视化和分析功能',
    icon: 'DataAnalysis'
  },
  {
    title: '模型评测',
    description: '支持上传和评测EEG数据处理模型，提供全面的性能指标',
    icon: 'Connection'
  },
  {
    title: '预处理工具',
    description: '提供滤波、降噪、重采样等多种EEG数据预处理工具',
    icon: 'SetUp'
  },
  {
    title: '可视化展示',
    description: '多维度可视化展示EEG数据特征和模型结果',
    icon: 'PieChart'
  }
];

// 检查登录状态
const checkLoginStatus = () => {
  const storedUser = localStorage.getItem('userInfo');
  if (storedUser) {
    try {
      const parsedUser = JSON.parse(storedUser);
      if (parsedUser && parsedUser.isLoggedIn) {
        userInfo.value = parsedUser;
      }
    } catch (e) {
      console.error('解析用户信息失败', e);
    }
  }
};

// 跳转到登录页面
const goToLogin = () => {
  router.push('/login');
};

// 跳转到数据集页面
const goToDatasets = () => {
  router.push('/datasets');
};

// 初始化时检查登录状态
onMounted(() => {
  checkLoginStatus();
});
</script>

<template>
  <div class="home-container">
    <!-- 全屏背景视频层，放在最顶层 -->
    <div class="svg-poster-container">
      <video autoplay loop muted playsinline class="video-background">
        <source src="@/assets/background.mp4" type="video/mp4">
        <!-- 如果视频无法播放，则使用图片作为备选方案 -->
        <img src="@/assets/back1.png" class="svg-poster" alt="EEG 背景" />
      </video>
      <div class="poster-overlay"></div>
    </div>
    <!-- 顶部导航栏 - 移除背景和阴影 -->
    <header class="home-header">
      <div class="header-left">
        <img src="@/assets/eeg-logo.svg" alt="Logo" class="header-logo" />
        <h1 class="header-title">EEG数据分析交互式可视化平台</h1>
      </div>
      <div class="header-right">
        <template v-if="userInfo">
          <el-button type="primary" @click="goToDatasets">进入系统</el-button>
        </template>
        <template v-else>
          <el-button type="primary" @click="goToLogin">登录</el-button>
        </template>
      </div>
    </header>
    <!-- 主要内容区域 -->
    <main class="home-main">
      <!-- 欢迎区域 -->
      <section class="hero-section">
        <div class="hero-content">
          <h2 class="hero-title">脑电数据分析交互展示平台</h2>
          <p class="hero-subtitle">
            较为完备的EEG数据预处理、分析和模型评测平台，为脑电学习研究提供支持！
          </p>
        </div>
        <div class="hero-image">
          <img src="@/assets/eeg-logo.svg" alt="EEG Logo" class="eeg-logo" />
        </div>
      </section>
      <!-- 特点展示区域 -->
      <section class="features-section">
        <h2 class="section-title">系统特点</h2>
        <div class="features-grid">
          <div v-for="(feature, index) in features" :key="index" class="feature-card">
            <div class="feature-icon">
              <el-icon :size="40"><component :is="feature.icon" /></el-icon>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-description">{{ feature.description }}</p>
          </div>
        </div>
      </section>
    </main>
    <!-- 页脚 -->
    <footer class="home-footer">
      <p>© {{ new Date().getFullYear() }} EEG数据分析交互式可视化平台 版权所有</p>
      <div class="developer-contact">
        <span>联系开发者：</span>
        <a href="mailto:wangyanjun13@foxmail.com">wangyanjun13@foxmail.com</a>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: hidden;
}

/* 全屏背景视频层，放在最顶层 */
.svg-poster-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.svg-poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 视频背景样式 */
.video-background {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.poster-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.2) 0%,
    rgba(245, 247, 250, 0.6) 90%,
    rgba(245, 247, 250, 0.8) 100%
  );
}

/* 顶部导航栏 - 移除背景和阴影 */
.home-header {
  height: 70px;
  background-color: transparent; /* 透明背景 */
  box-shadow: none; /* 移除阴影 */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-logo {
  width: 40px;
  height: 40px;
  margin-right: 15px;
}

.header-title {
  font-size: 22px;
  color: #f1f1f1;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 1px 4px rgba(255, 255, 255, 0.7); /* 添加文字阴影增加可读性 */
}

/* 主要内容区域 */
.home-main {
  flex: 1;
  margin-top: 70px;
  position: relative;
  z-index: 10;
}

/* 欢迎区域 */
.hero-section {
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 10;
  margin-top: 80px;
  min-height: calc(100vh - 300px);
}

.hero-content {
  flex: 1;
  max-width: 600px;
  background-color: rgba(255, 255, 255, 0.85);
  padding: 40px;
  border-radius: 15px;
  box-shadow: 0 15px 35px rgba(2, 2, 2, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(12, 12, 12, 0.2);
  animation: fadeInUp 1s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-title {
  font-size: 42px;
  color: #f2f2f2;
  margin: 0 0 20px;
  font-weight: 600;
  line-height: 1.2;
  background: linear-gradient(45deg, #409EFF, #53a8ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 2px 10px rgba(64, 158, 255, 0.3);
}

.hero-subtitle {
  font-size: 18px;
  color: #606266;
  margin: 0 0 30px;
  line-height: 1.5;
}

.hero-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  /* 让图片区域更大 */
  min-width: 550px;
  min-height: 550px;
}

.eeg-logo {
  width: 300px;
  height: 300px;
  filter: drop-shadow(0 10px 20px rgba(64, 158, 255, 0.3));
  animation: pulse 4s ease-in-out infinite;
  transform-origin: center center;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1) rotate(0deg);
  }
  50% {
    transform: scale(1.05) rotate(2deg);
  }
}

/* 特点展示区域 */
.features-section {
  padding: 100px 40px 80px;
  background-color: rgba(255, 255, 255, 0.9);
  position: relative;
  z-index: 10;
  margin-top: 50px;
  border-radius: 30px 30px 0 0;
  box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(5px);
}

.section-title {
  font-size: 36px;
  color: #303133;
  text-align: center;
  margin: 0 0 60px;
  font-weight: 600;
  position: relative;
}

.section-title::after {
  content: "";
  position: absolute;
  bottom: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(90deg, #409EFF, #53a8ff);
  border-radius: 2px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  background-color: rgb(136, 178, 205);
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(94, 91, 91, 0.05);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border-top: 4px solid #409EFF;
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(255, 255, 255, 0) 50%);
  z-index: 0;
}

.feature-card:hover {
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 20px 40px rgba(64, 158, 255, 0.2);
}

.feature-icon {
  margin-bottom: 20px;
  color: #409EFF;
  background-color: #ecf5ff;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.feature-card:hover .feature-icon {
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.4);
}

.feature-title {
  font-size: 20px;
  color: #303133;
  margin: 0 0 15px;
  font-weight: 600;
  position: relative;
  z-index: 1;
}

.feature-description {
  font-size: 14px;
  color: #606266;
  margin: 0;
  line-height: 1.5;
  position: relative;
  z-index: 1;
}

/* 页脚 */
.home-footer {
  background-color: rgba(48, 49, 51, 0.9);
  color: #c0c4cc;
  padding: 30px;
  text-align: center;
  position: relative;
  z-index: 10;
  backdrop-filter: blur(5px);
}

/* 开发者联系信息 */
.developer-contact {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.developer-contact:hover {
  opacity: 1;
}

.developer-contact a {
  color: #a0cfff;
  text-decoration: none;
  transition: color 0.3s;
}

.developer-contact a:hover {
  color: #409EFF;
  text-decoration: underline;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .hero-section {
    flex-direction: column;
    padding: 0 20px;
    margin-top: 80px;
  }
  
  .hero-content {
    max-width: 100%;
    text-align: center;
    margin-bottom: 40px;
    padding: 30px;
  }
  
  .hero-buttons {
    justify-content: center;
  }
  
  .hero-title {
    font-size: 36px;
  }
  
  .eeg-logo {
    width: 250px;
    height: 250px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    margin-top: 80px;
  }
  
  .home-header {
    padding: 0 20px;
  }
  
  .header-title {
    font-size: 18px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    max-width: 500px;
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .hero-subtitle {
    font-size: 16px;
  }
  
  .eeg-logo {
    width: 200px;
    height: 200px;
  }
  
  .hero-content {
    padding: 20px;
  }
}

@media (max-width: 576px) {
  .hero-section {
    margin-top: 80px;
  }
  
  .home-header {
    padding: 0 15px;
  }
  
  .header-logo {
    width: 30px;
    height: 30px;
    margin-right: 10px;
  }
  
  .header-title {
    font-size: 16px;
  }
  
  .hero-title {
    font-size: 28px;
  }
  
  .eeg-logo {
    width: 150px;
    height: 150px;
  }
  
  .hero-buttons {
    flex-direction: column;
    gap: 10px;
  }
  
  .features-section {
    padding: 60px 15px 40px;
    margin-top: 30px;
  }
}
</style> 