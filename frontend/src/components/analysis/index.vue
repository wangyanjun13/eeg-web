<script setup>
import { ref } from 'vue';
import AppLayout from '@/components/layout/AppLayout.vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const analysisModules = [
  {
    title: '预处理',
    description: '对脑电数据进行滤波、去伪迹等预处理操作',
    icon: 'Filter',
    path: '/analysis/preprocessing'
  },
  {
    title: '时域分析',
    description: '分析ERP波形和时间序列特征',
    icon: 'Timer',
    path: '/analysis/time-analysis'
  },
  {
    title: '频域分析',
    description: '分析频谱特征和功率谱密度',
    icon: 'DataLine',
    path: '/analysis/frequency-analysis'
  },
  {
    title: '空间分析',
    description: '分析头皮地形图和空间分布',
    icon: 'MapLocation',
    path: '/analysis/spatial-analysis'
  },
  {
    title: '高级分析',
    description: '进行连通性分析、机器学习等高级分析',
    icon: 'TrendCharts',
    path: '/analysis/advanced-analysis'
  }
];

function navigateTo(path) {
  router.push(path);
}
</script>

<template>
  <AppLayout>
    <div class="analysis-container">
      <h1 class="page-title">数据分析工具</h1>
      <p class="page-description">选择以下分析模块开始您的脑电数据分析</p>
      
      <div class="analysis-modules">
        <el-card 
          v-for="module in analysisModules" 
          :key="module.title"
          class="analysis-module-card"
          shadow="hover"
          @click="navigateTo(module.path)"
        >
          <div class="module-content">
            <el-icon class="module-icon"><component :is="module.icon" /></el-icon>
            <h3 class="module-title">{{ module.title }}</h3>
            <p class="module-description">{{ module.description }}</p>
          </div>
        </el-card>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.analysis-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.analysis-modules {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 30px;
}

.analysis-module-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.analysis-module-card:hover {
  transform: translateY(-5px);
}

.module-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px;
}

.module-icon {
  font-size: 48px;
  color: #409EFF;
  margin-bottom: 16px;
}

.module-title {
  font-size: 20px;
  margin: 0 0 10px 0;
  color: #303133;
}

.module-description {
  color: #606266;
  margin: 0;
}
</style> 