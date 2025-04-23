<script setup>
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  ArrowDown
} from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();

// 导航函数
function navigateTo(path) {
  router.push(path);
}
</script>

<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-left">
        <img src="@/assets/vue.svg" alt="Logo" class="header-logo" @click="navigateTo('/')" />
        <h1 class="header-title">EEG数据分析交互展示平台</h1>
      </div>
      <!-- 用户信息下拉菜单 -->
      <div class="header-right">
        <el-dropdown>
          <span class="user-dropdown-link">
            用户名 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="navigateTo('/user/profile')">个人资料</el-dropdown-item>
              <el-dropdown-item @click="navigateTo('/user/settings')">设置</el-dropdown-item>
              <el-dropdown-item divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <div class="main-container">
      <div class="main-content">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/*顶部导航栏*/
.app-header {
  height: 60px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1001;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-logo {
  width: 32px;
  height: 32px;
  cursor: pointer;
  transition: transform 0.3s;
  margin-right: 16px;
}

.header-logo:hover {
  transform: scale(1.1);
}

.header-title {
  margin: 0;
  font-size: 22px;
  color: #303133;
  font-weight: 500;
  font-weight:bold;
}

.header-right {
  margin-left: auto;
}

.user-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #409EFF;
}

/*主要内容区域*/
.main-container {
  flex: 1;
  margin-top: 60px;
  display: flex;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .main-content {
    padding: 15px;
  }
}

@media (max-width: 768px) {
  .header-title {
    font-size: 18px;
  }
  
  .main-content {
    padding: 10px;
  }
}

@media (max-width: 576px) {
  .header-title {
    font-size: 16px;
  }
  
  .app-header {
    padding: 0 10px;
  }
  
  .main-content {
    padding: 10px 5px;
  }
}
</style> 