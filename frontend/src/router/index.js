import { createRouter, createWebHistory } from 'vue-router';
import DatasetOverview from '../views/dataset/index.vue';
import DatasetDetail from '../views/dataset/detail.vue';
import DatasetUpload from '../views/dataset/DatasetUpload.vue';
import MyFiles from '../views/dataset/MyFiles.vue';
import SubjectDetail from '../views/subject/detail.vue';
import NotFound from '../views/NotFound.vue';
import Preprocessing from '../views/analysis/preprocessing/index.vue';
import TimeAnalysis from '../views/analysis/timeAnalysis.vue';
import FrequencyAnalysis from '../views/analysis/frequencyAnalysis.vue';
import SpatialAnalysis from '../views/analysis/spatialAnalysis.vue';
import AdvancedAnalysis from '../views/analysis/advancedAnalysis.vue';
import Home from '../views/Home.vue';
import Login from '../views/user/Login.vue';
import UserProfile from '../views/user/UserProfile.vue';
import UserSettings from '../views/user/UserSettings.vue';

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: 'EEG数据分析平台'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录 - EEG数据分析平台'
    }
  },
  {
    path: '/datasets',
    name: 'Datasets',
    component: DatasetOverview,
    meta: {
      title: '数据集浏览 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/datasets/:id',
    name: 'DatasetDetail',
    component: DatasetDetail,
    meta: {
      title: '数据集详情 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/datasets/:datasetId/subjects/:subjectId',
    name: 'SubjectDetail',
    component: SubjectDetail,
    meta: {
      title: '被试详情 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/datasets/:datasetId/subjects/:subjectId/analyze',
    name: 'SubjectAnalyze',
    component: Preprocessing,
    meta: {
      title: '数据分析 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Preprocessing,
    meta: {
      title: '数据分析工具 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/analysis/preprocessing/:datasetId/:subjectId',
    name: 'Preprocessing',
    component: Preprocessing,
    meta: {
      title: '预处理 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/analysis/time-analysis/:datasetId/:subjectId',
    name: 'TimeAnalysis',
    component: TimeAnalysis,
    meta: {
      title: '时域分析 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/analysis/frequency-analysis/:datasetId/:subjectId',
    name: 'FrequencyAnalysis',
    component: FrequencyAnalysis,
    meta: {
      title: '频域分析 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/analysis/spatial-analysis/:datasetId/:subjectId',
    name: 'SpatialAnalysis',
    component: SpatialAnalysis,
    meta: {
      title: '空间分析 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/analysis/advanced-analysis/:datasetId/:subjectId',
    name: 'AdvancedAnalysis',
    component: AdvancedAnalysis,
    meta: {
      title: '高级分析 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/upload',
    name: 'DatasetUpload',
    component: DatasetUpload,
    meta: {
      title: '上传数据 - EEG数据分析平台',
      requiresAuth: true
    }
  },
  {
    path: '/my-files',
    name: 'MyFiles',
    component: MyFiles,
    meta: {
      requiresAuth: true,
      title: '我的文件 - EEG数据分析平台'
    }
  },
  {
    path: '/upload-file',
    name: 'UploadFile',
    component: () => import('../views/dataset/DatasetUpload.vue'),
    meta: {
      requiresAuth: true,
      title: '上传文件 - EEG数据分析平台'
    }
  },
  {
    path: '/user/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: {
      requiresAuth: true,
      title: '个人资料 - EEG数据分析平台'
    }
  },
  {
    path: '/user/settings',
    name: 'UserSettings',
    component: UserSettings,
    meta: {
      requiresAuth: true,
      title: '用户设置 - EEG数据分析平台'
    }
  },
  {
    path: '/model-visualization',
    name: 'ModelVisualization',
    component: () => import('../views/dataset/ModelVisualization.vue'),
    meta: {
      requiresAuth: true,
      title: '模型可视化 - EEG数据分析平台'
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

// 全局前置守卫，用于更改页面标题和检查登录状态
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = to.meta.title;
  }
  
  // 检查该路由是否需要登录权限
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 获取用户登录状态
    const userInfo = localStorage.getItem('userInfo');
    let isLoggedIn = false;
    
    if (userInfo) {
      try {
        const parsedUser = JSON.parse(userInfo);
        isLoggedIn = parsedUser && parsedUser.isLoggedIn;
      } catch (e) {
        console.error('解析用户信息失败', e);
      }
    }
    
    if (!isLoggedIn) {
      // 如果没有登录，重定向到登录页面
      next({
        path: '/login',
        query: { redirect: to.fullPath } // 保存原本要访问的路径
      });
    } else {
      // 已登录，正常进入
      next();
    }
  } else {
    // 不需要登录权限的路由，正常进入
    next();
  }
});

export default router; 