<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const props = defineProps({
  currentStep: {
    type: String,
    required: true
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
  { key: 'raw', label: '原始数据', icon: 'DataLine', path: '/datasets/:datasetId/subjects/:subjectId' },
  { key: 'preprocessing', label: '预处理', icon: 'Filter', path: '/analysis/preprocessing' },
  { key: 'time', label: '时域分析', icon: 'Timer', path: '/analysis/time-analysis' },
  { key: 'frequency', label: '频域分析', icon: 'PieChart', path: '/analysis/frequency-analysis' },
  { key: 'spatial', label: '空间分析', icon: 'Position', path: '/analysis/spatial-analysis' },
  { key: 'advanced', label: '高级分析', icon: 'DataAnalysis', path: '/analysis/advanced-analysis' }
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
  } else if (!path.includes('datasets')) {
    path = `${path}/${props.datasetId}/${props.subjectId}`;
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

defineExpose({
  goToNextStep
});
</script>

<template>
  <div class="analysis-workflow">
    <el-steps :active="activeStep" finish-status="success" simple>
      <el-step 
        v-for="(step, index) in steps" 
        :key="index" 
        :title="step.label"
        @click="navigateToStep(step)"
        class="workflow-step"
      >
        <template #icon>
          <el-icon>
            <component :is="step.icon" />
          </el-icon>
        </template>
      </el-step>
    </el-steps>
  </div>
</template>

<style scoped>
.analysis-workflow {
  background-color: white;
  padding: 12px 20px;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 -2px 12px 0 rgba(0, 0, 0, 0.1);
  position: fixed;
  bottom: 0;
  left: 64px;
  right: 0;
  z-index: 1000;
}

.workflow-step {
  cursor: pointer;
}

:deep(.el-step__title) {
  font-size: 14px;
}

:deep(.el-step__icon) {
  font-size: 18px;
}
</style> 