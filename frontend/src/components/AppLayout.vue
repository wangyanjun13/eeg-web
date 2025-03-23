<script setup>
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  Document, 
  DataAnalysis, 
  PieChart, 
  Upload
} from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();

// 计算当前活动菜单项
const activeMenu = computed(() => {
  return route.path.split('/')[1] || 'datasets';
});

// 导航函数
function navigateTo(path) {
  router.push(path);
}
</script>

<template>
  <div class="app-layout">
    <!-- 侧边导航栏 -->
    <div class="side-nav">
      <el-menu
        mode="vertical"
        :default-active="activeMenu"
        class="side-menu"
        :collapse="true"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409EFF"
      >
        <el-tooltip
          content="数据集浏览"
          placement="right"
          :show-after="200"
          effect="dark"
        >
          <el-menu-item index="datasets" @click="navigateTo('/datasets')">
            <el-icon><Document /></el-icon>
            <template #title>数据集浏览</template>
          </el-menu-item>
        </el-tooltip>

        <el-tooltip
          content="数据分析"
          placement="right"
          :show-after="200"
          effect="dark"
        >
          <el-menu-item index="analysis" @click="navigateTo('/analysis')">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>数据分析</template>
          </el-menu-item>
        </el-tooltip>

        <el-tooltip
          content="可视化"
          placement="right"
          :show-after="200"
          effect="dark"
        >
          <el-menu-item index="visualization" @click="navigateTo('/visualization')">
            <el-icon><PieChart /></el-icon>
            <template #title>可视化</template>
          </el-menu-item>
        </el-tooltip>

        <el-tooltip
          content="上传数据集"
          placement="right"
          :show-after="200"
          effect="dark"
        >
          <el-menu-item index="upload" @click="navigateTo('/upload')">
            <el-icon><Upload /></el-icon>
            <template #title>上传数据集</template>
          </el-menu-item>
        </el-tooltip>
      </el-menu>
    </div>

    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="logo">
        <h1>EEG数据分析交互展示平台</h1>
      </div>
      
      <!-- 用户信息下拉菜单 -->
      <div class="user-info">
        <el-dropdown>
          <span class="user-dropdown-link">
            用户名 <el-icon class="el-icon--right"><arrow-down /></el-icon>
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
  min-height: 100vh; /* 最小高度为视口高度 */
  display: flex;
  flex-direction: column;
}

.side-nav {
  position: fixed; /* 固定位置 */
  left: 0;
  top: 0; /* 侧边导航栏延伸到顶部 */
  bottom: 0;
  z-index: 1000;
  background-color: #001529; /* 侧边导航栏背景颜色 */
}

.side-menu {
  border-right: none; /* 移除右侧边框 */
}

.app-header {
  height: 60px; /* 头部高度 */
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* 阴影效果 */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 64px; /* 左侧留出侧边导航栏的宽度 */
  right: 0;
  z-index: 1001;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 20px; /* 向右移动 logo 和标题 */
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.user-info {
  margin-left: auto; /* 推到右侧 */
}

.user-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #409EFF;
}

.main-container {
  display: flex;
  flex: 1;
  margin-top: 60px; /* 为顶部导航栏留出空间 */
}

.main-content {
  flex: 1;
  margin-left: 64px; /* 左侧留出侧边导航栏的宽度 */
  padding: 20px 20px 20px 0;
  background-color: #f0f2f5; /* 内容区背景色 */
  min-height: calc(100vh - 60px);
}
</style> 