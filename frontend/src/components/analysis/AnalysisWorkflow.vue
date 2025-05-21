<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

const props = defineProps({
  currentStep: {
    type: String,
    required: true,
    validator: (value) => ['raw', 'preprocessing', 'time', 'frequency', 'spatial', 'advanced'].includes(value)
  },
  datasetId: {
    type: String,
    required: true
  },
  subjectId: {
    type: String,
    required: true
  }
});

const router = useRouter();

const steps = [
  { 
    key: 'raw', 
    label: '原始数据', 
    icon: 'DataLine', 
    path: '/datasets/:datasetId/subjects/:subjectId',
    description: '查看和检查原始EEG数据'
  },
  { 
    key: 'preprocessing', 
    label: '预处理', 
    icon: 'Filter', 
    path: '/analysis/preprocessing/:datasetId/:subjectId',
    description: '滤波、去伪迹、重参考等'
  },
  { 
    key: 'time', 
    label: '时域分析', 
    icon: 'Timer', 
    path: '/analysis/time-analysis/:datasetId/:subjectId',
    description: 'ERP分析、时间序列分析'
  },
  { 
    key: 'frequency', 
    label: '频域分析', 
    icon: 'PieChart', 
    path: '/analysis/frequency-analysis/:datasetId/:subjectId',
    description: '频谱分析、时频分析'
  },
  { 
    key: 'spatial', 
    label: '空间分析', 
    icon: 'Position', 
    path: '/analysis/spatial-analysis/:datasetId/:subjectId',
    description: '地形图、源定位分析'
  },
  { 
    key: 'advanced', 
    label: '高级分析', 
    icon: 'DataAnalysis', 
    path: '/analysis/advanced-analysis/:datasetId/:subjectId',
    description: '连接性分析、机器学习'
  }
];

const activeStep = computed(() => {
  return steps.findIndex(step => step.key === props.currentStep);
});

// 导航到指定步骤
function navigateToStep(step) {
  let path = step.path;
  if (path.includes(':datasetId')) {
    path = path.replace(':datasetId', props.datasetId);
  }
  if (path.includes(':subjectId')) {
    path = path.replace(':subjectId', props.subjectId);
  }
  router.push(path);
}

// 获取下一步
const nextStep = computed(() => {
  const currentIndex = activeStep.value;
  if (currentIndex < steps.length - 1) {
    return steps[currentIndex + 1];
  }
  return null;
});

// 导航到下一步
function goToNextStep() {
  if (nextStep.value) {
    navigateToStep(nextStep.value);
  }
}

// 控制悬停状态
const isExpanded = ref(false);

defineExpose({
  goToNextStep
});
</script>

<template>
  <div 
    class="analysis-workflow-sidebar"
    @mouseenter="isExpanded = true"
    @mouseleave="isExpanded = false"
  >
    <div class="workflow-content" :class="{ 'expanded': isExpanded }">
      <div class="workflow-header">
        <h3>分析工作流</h3>
        <span class="step-indicator">{{ activeStep + 1 }}/{{ steps.length }}</span>
      </div>
      
      <div class="steps-container">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="workflow-step"
          :class="{ 
            'active': index === activeStep,
            'completed': index < activeStep,
            'pending': index > activeStep
          }"
          @click="navigateToStep(step)"
        >
          <div class="step-icon">
            <el-icon v-if="index > activeStep">{{ index + 1 }}</el-icon>
            <el-icon v-else-if="index < activeStep"><Check /></el-icon>
            <component v-else :is="step.icon" />
          </div>
          
          <div class="step-content">
            <div class="step-title">{{ step.label }}</div>
            <div class="step-description" v-if="isExpanded">{{ step.description }}</div>
          </div>
        </div>
      </div>
      
      <div class="navigation-buttons" v-if="isExpanded">
        <el-button 
          v-if="activeStep > 0" 
          @click="navigateToStep(steps[activeStep - 1])"
          icon="ArrowLeft"
          size="small"
          plain
        >
          上一步
        </el-button>
        
        <el-button 
          v-if="activeStep < steps.length - 1" 
          @click="navigateToStep(steps[activeStep + 1])"
          type="primary"
          icon="ArrowRight"
          size="small"
          class="next-button"
        >
          下一步
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-workflow-sidebar {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1000;
  display: flex;
  align-items: center;
}

.workflow-content {
  background-color: white;
  border-radius: 0 12px 12px 0;
  box-shadow: 2px 0 15px rgba(0, 0, 0, 0.1);
  padding: 16px 0;
  transition: all 0.3s ease;
  width: 60px;
  overflow: hidden;
}

.workflow-content.expanded {
  width: 280px;
  padding: 16px;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 16px;
  background-color: var(--primary-color);
  border-radius: 6px;
  color: white;
}

.workflow-header h3 {
  margin: 0;
  font-size: 16px;
  color: white;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.3s;
}

.expanded .workflow-header h3 {
  opacity: 1;
}

.step-indicator {
  color: white;
  font-size: 12px;
  white-space: nowrap;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workflow-step {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.workflow-step:hover {
  background-color: #f5f7fa;
}

.step-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
  color: #909399;
  margin-right: 12px;
  flex-shrink: 0;
  transition: all 0.3s;
}

.step-content {
  overflow: hidden;
}

.step-title {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
  white-space: nowrap;
}

.step-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  white-space: nowrap;
}

/* 活动步骤样式 */
.workflow-step.active {
  background-color: rgba(64, 158, 255, 0.1);
}

.workflow-step.active .step-icon {
  background-color: var(--primary-color);
  color: white;
}

.workflow-step.active .step-title {
  color: var(--button-use);
  font-weight: 600;
}

/* 已完成步骤样式 */
.workflow-step.completed .step-icon {
  background-color: var(--success-color);
  color: white;
}

/* 导航按钮 */
.navigation-buttons {
  display: flex;
  justify-content: space-between;
  padding: 16px 16px 0;
  margin-top: 8px;
  border-top: 1px solid #ebeef5;
}

.next-button {
  margin-left: auto;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .analysis-workflow-sidebar {
    bottom: 0;
    top: auto;
    left: 0;
    right: 0;
    transform: none;
  }
  
  .workflow-content {
    width: 100%;
    border-radius: 12px 12px 0 0;
    padding: 12px;
  }
  
  .workflow-content.expanded {
    width: 100%;
  }
  
  .steps-container {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
  }
  
  .workflow-step {
    flex-direction: column;
    align-items: center;
    text-align: center;
    min-width: 80px;
  }
  
  .step-icon {
    margin-right: 0;
    margin-bottom: 8px;
  }
}
</style> 