import { createRouter, createWebHistory } from 'vue-router';
import DatasetOverview from '../views/dataset/index.vue';
import DatasetDetail from '../views/dataset/detail.vue';
import DatasetUpload from '../views/dataset/DatasetUpload.vue';
import SubjectDetail from '../views/subject/detail.vue';
import NotFound from '../views/NotFound.vue';

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/datasets',
    meta: {
      title: 'EEG数据分析平台'
    }
  },
  {
    path: '/datasets',
    name: 'Datasets',
    component: DatasetOverview,
    meta: {
      title: '数据集浏览 - EEG数据分析平台'
    }
  },
  {
    path: '/datasets/:id',
    name: 'DatasetDetail',
    component: DatasetDetail,
    meta: {
      title: '数据集详情 - EEG数据分析平台'
    }
  },
  {
    path: '/datasets/:datasetId/subjects/:subjectId',
    name: 'SubjectDetail',
    component: SubjectDetail,
    meta: {
      title: '受试者详情 - EEG数据分析平台'
    }
  },
  {
    path: '/datasets/:datasetId/subjects/:subjectId/analyze',
    name: 'SubjectAnalyze',
    component: () => import('../views/analysis/preprocessing.vue'),
    meta: {
      title: '数据分析 - EEG数据分析平台'
    }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('../views/analysis/preprocessing.vue'),
    meta: {
      title: '数据分析工具 - EEG数据分析平台'
    }
  },
  {
    path: '/analysis/preprocessing',
    name: 'Preprocessing',
    component: () => import('../views/analysis/preprocessing.vue'),
    meta: {
      title: '数据预处理 - EEG数据分析平台'
    }
  },
  {
    path: '/analysis/time-analysis',
    name: 'TimeAnalysis',
    component: () => import('../views/analysis/timeAnalysis.vue'),
    meta: {
      title: '时域分析 - EEG数据分析平台'
    }
  },
  {
    path: '/analysis/frequency-analysis',
    name: 'FrequencyAnalysis',
    component: () => import('../views/analysis/frequencyAnalysis.vue'),
    meta: {
      title: '频域分析 - EEG数据分析平台'
    }
  },
  {
    path: '/analysis/spatial-analysis',
    name: 'SpatialAnalysis',
    component: () => import('../views/analysis/spatialAnalysis.vue'),
    meta: {
      title: '空间分析 - EEG数据分析平台'
    }
  },
  {
    path: '/analysis/advanced-analysis',
    name: 'AdvancedAnalysis',
    component: () => import('../views/analysis/advancedAnalysis.vue'),
    meta: {
      title: '高级分析 - EEG数据分析平台'
    }
  },
  {
    path: '/upload',
    name: 'DatasetUpload',
    component: DatasetUpload,
    meta: {
      title: '上传数据 - EEG数据分析平台'
    }
  },
  {
    path: '/user/profile',
    name: 'UserProfile',
    component: () => import('../views/user/UserProfile.vue'),
    meta: {
      title: '个人资料 - EEG数据分析平台'
    }
  },
  {
    path: '/user/settings',
    name: 'UserSettings',
    component: () => import('../views/user/UserSettings.vue'),
    meta: {
      title: '用户设置 - EEG数据分析平台'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面未找到 - EEG数据分析平台'
    }
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
});

// 全局前置守卫，用于更改页面标题
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = to.meta.title;
  }
  next();
});

export default router; 