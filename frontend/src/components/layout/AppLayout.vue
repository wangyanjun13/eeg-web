<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  ArrowDown,
  Collection,
  Document,
  Histogram,
  DataAnalysis,
  Connection,
  User,
  HomeFilled
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';

const router = useRouter();
const route = useRoute();

// 用户状态管理
const userInfo = ref(null);

// 从本地存储加载用户信息
const loadUserInfo = () => {
  try {
    const storedUser = localStorage.getItem('userInfo');
    if (storedUser) {
      userInfo.value = JSON.parse(storedUser);
    }
  } catch (e) {
    console.error('解析用户信息失败', e);
  }
};

// 初始化加载用户信息
onMounted(() => {
  loadUserInfo();
  
  // 添加存储事件监听器，以便在其他页面修改用户信息时更新
  window.addEventListener('storage', (event) => {
    if (event.key === 'userInfo') {
      loadUserInfo();
    }
  });
});

// 登录/登出处理
const handleLogin = () => {
  router.push('/login');
};

const handleLogout = () => {
  ElMessageBox.confirm(
    '确定要退出登录吗？',
    '退出登录',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 保留用户信息但标记为未登录
    if (userInfo.value) {
      userInfo.value.isLoggedIn = false;
      localStorage.setItem('userInfo', JSON.stringify(userInfo.value));
    }
    ElMessage.success('已退出登录');
    
    // 跳转到首页
    router.push('/');
  }).catch(() => {
    // 取消退出登录
  });
};

// 导航函数
function navigateTo(path) {
  router.push(path);
}

// 计算当前路由
const currentPath = computed(() => route.path);

// 判断当前路由是否激活
const isActive = (path) => {
  if (path === '/datasets') {
    return currentPath.value === '/datasets' || currentPath.value.startsWith('/datasets/');
  }
  return currentPath.value === path || currentPath.value.startsWith(path);
};

// 返回首页
const goToHome = () => {
  router.push('/');
};
</script>

<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-left">
        <img src="@/assets/eeg-logo.svg" alt="Logo" class="header-logo" @click="goToHome" />
        <h1 class="header-title">EEG数据分析交互展示平台</h1>
      </div>
      
      <!-- 简化的主导航 -->
      <div class="main-nav">
        <div 
          class="nav-item" 
          :class="{ active: isActive('/datasets') }"
          @click="navigateTo('/datasets')"
        >
          <el-icon><DataAnalysis /></el-icon>
          <span>数据集分析</span>
        </div>
        
        <div 
          class="nav-item" 
          :class="{ active: isActive('/my-files') }"
          @click="navigateTo('/my-files')"
        >
          <el-icon><Connection /></el-icon>
          <span>模型评测</span>
        </div>
      </div>

      <!-- 用户信息下拉菜单 -->
      <div class="header-right">
        <el-dropdown v-if="userInfo && userInfo.isLoggedIn">
          <span class="user-dropdown-link">
            <span class="username">{{ userInfo.username }}</span> 
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="navigateTo('/user/profile')">个人资料</el-dropdown-item>
              <el-dropdown-item @click="navigateTo('/user/settings')">设置</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button v-else type="primary" @click="handleLogin" size="small">
          <el-icon><User /></el-icon>
          <span>登录</span>
        </el-button>
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
  margin-right: 40px;
  cursor: pointer;
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

/* 主导航样式 */
.main-nav {
  display: flex;
  gap: 20px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 15px;
  height: 40px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.nav-item:hover {
  background-color: #f0f5ff;
  color: #409EFF;
}

.nav-item.active {
  background-color: #ecf5ff;
  color: #409EFF;
}

.nav-item .el-icon {
  font-size: 18px;
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

.username {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  
  .nav-item {
    padding: 0 10px;
  }
  
  .username {
    max-width: 80px;
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
  
  .nav-item {
    padding: 0 8px;
  }
  
  .nav-item span {
    font-size: 14px;
  }
  
  .username {
    max-width: 60px;
  }
}
</style> 