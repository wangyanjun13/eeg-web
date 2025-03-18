import { createRouter, createWebHistory } from 'vue-router';
import * as Views from '../views';

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/datasets'
  },
  {
    path: '/datasets',
    name: 'Datasets',
    component: Views.DatasetOverview,
    meta: {
      title: '数据集浏览 - EEG数据分析平台'
    }
  },
  {
    path: '/datasets/:id',
    name: 'DatasetDetail',
    component: Views.DatasetDetail,
    meta: {
      title: '数据集详情 - EEG数据分析平台'
    }
  },
  {
    path: '/datasets/:datasetId/subjects/:subjectId',
    name: 'SubjectDetail',
    component: Views.SubjectDetail,
    meta: {
      title: '受试者详情 - EEG数据分析平台'
    }
  },
  {
    path: '/datasets/:datasetId/subjects/:subjectId/analyze',
    name: 'SubjectAnalyze',
    component: Views.SubjectAnalyze,
    meta: {
      title: '数据分析 - EEG数据分析平台'
    }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('../views/Analysis.vue'),
    meta: {
      title: '数据分析工具 - EEG数据分析平台'
    }
  },
  {
    path: '/visualization',
    name: 'Visualization',
    component: () => import('../views/Visualization.vue'),
    meta: {
      title: '可视化工具 - EEG数据分析平台'
    }
  },
  {
    path: '/upload',
    name: 'DatasetUpload',
    component: Views.DatasetUpload,
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
    component: () => import('../views/NotFound.vue'),
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