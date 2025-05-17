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
    <!-- 顶部导航栏 -->
    <header class="home-header">
      <div class="header-left">
        <img src="@/assets/vue.svg" alt="Logo" class="header-logo" />
        <h1 class="header-title">EEG数据分析交互展示平台</h1>
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
          <h2 class="hero-title">脑电数据分析与模型评测系统</h2>
          <p class="hero-subtitle">
            专业的EEG数据处理、分析和模型评测平台，为脑电研究提供全方位支持
          </p>
        </div>
        <div class="hero-image">
          <!-- 这里可以放置一个脑电相关的示意图 -->
          <div class="placeholder-image">
            <el-icon :size="100"><DataAnalysis /></el-icon>
          </div>
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
      <p>© {{ new Date().getFullYear() }} EEG数据分析交互展示平台 版权所有</p>
    </footer>
  </div>
</template>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏 */
.home-header {
  height: 70px;
  background-color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  color: #303133;
  margin: 0;
  font-weight: 600;
}

/* 主要内容区域 */
.home-main {
  flex: 1;
  margin-top: 70px;
}

/* 欢迎区域 */
.hero-section {
  padding: 80px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-content {
  flex: 1;
  max-width: 600px;
}

.hero-title {
  font-size: 42px;
  color: #303133;
  margin: 0 0 20px;
  font-weight: 600;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 18px;
  color: #606266;
  margin: 0;
  line-height: 1.5;
}

.hero-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.placeholder-image {
  width: 300px;
  height: 300px;
  background-color: #f0f5ff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #409EFF;
}

/* 特点展示区域 */
.features-section {
  padding: 60px 40px;
  background-color: #f5f7fa;
}

.section-title {
  font-size: 32px;
  color: #303133;
  text-align: center;
  margin: 0 0 50px;
  font-weight: 600;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  background-color: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s, box-shadow 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  margin-bottom: 20px;
  color: #409EFF;
}

.feature-title {
  font-size: 20px;
  color: #303133;
  margin: 0 0 15px;
  font-weight: 600;
}

.feature-description {
  font-size: 14px;
  color: #606266;
  margin: 0;
  line-height: 1.5;
}

/* 页脚 */
.home-footer {
  background-color: #303133;
  color: #c0c4cc;
  padding: 30px;
  text-align: center;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .hero-section {
    flex-direction: column;
    padding: 60px 20px;
  }
  
  .hero-content {
    max-width: 100%;
    text-align: center;
    margin-bottom: 40px;
  }
  
  .hero-title {
    font-size: 36px;
  }
}

@media (max-width: 768px) {
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
  
  .placeholder-image {
    width: 200px;
    height: 200px;
  }
}

@media (max-width: 576px) {
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
  
  .placeholder-image {
    width: 150px;
    height: 150px;
  }
}
</style> 