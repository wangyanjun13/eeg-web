<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import AppLayout from '@/components/layout/AppLayout.vue';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';
import { useAnalysis } from '@/composables/useAnalysis';
import FilterProcessor from './FilterProcessor.vue';
import ResamplingProcessor from './ResamplingProcessor.vue';
import ReferenceProcessor from './ReferenceProcessor.vue';
import ICAProcessor from './ICAProcessor.vue';
import BadChannelProcessor from './BadChannelProcessor.vue';
import ArtifactProcessor from './ArtifactProcessor.vue';

const route = useRoute();
const router = useRouter();
const datasetId = route.params.datasetId;
const subjectId = route.params.subjectId;

// 使用分析组合函数
const {
  isLoading,
  originalData,
  processedData,
  preprocessParams,
  fetchOriginalData,
  loadPreprocessTemplate,
  saveResults
} = useAnalysis(datasetId, subjectId);

// 数据状态
const compareMode = ref(false);
const timeRange = ref([0, 10]);
const selectedChannels = ref([]);
const activeTemplate = ref('default');
const activeProcessor = ref('filter'); // 当前激活的处理器

// 预处理步骤定义
const processingSteps = [
  { key: 'filter', label: '滤波处理', icon: 'Filter', component: FilterProcessor },
  { key: 'resample', label: '重采样', icon: 'ScaleToOriginal', component: ResamplingProcessor },
  { key: 'reference', label: '重参考', icon: 'Compass', component: ReferenceProcessor },
  { key: 'ica', label: 'ICA分析', icon: 'DataAnalysis', component: ICAProcessor },
  { key: 'badChannels', label: '坏通道检测', icon: 'CircleClose', component: BadChannelProcessor },
  { key: 'artifacts', label: '伪迹处理', icon: 'Delete', component: ArtifactProcessor }
];

// 找到当前步骤的索引
const currentStepIndex = computed(() => {
  return processingSteps.findIndex(step => step.key === activeProcessor.value);
});

// 下一个处理步骤
const nextStep = computed(() => {
  if (currentStepIndex.value < processingSteps.length - 1) {
    return processingSteps[currentStepIndex.value + 1];
  }
  return null;
});

const availableTemplates = [
  { value: 'default', label: '默认预处理' },
  { value: 'minimal', label: '最小预处理' },
  { value: 'ds002218', label: 'DS002218 数据集预处理' }
];

// 加载初始数据
onMounted(async () => {
  await fetchOriginalData();
  if (originalData.value && originalData.value.channels) {
    // 默认选择前10个通道
    selectedChannels.value = originalData.value.channels.slice(0, 10);
  }
  
  // 加载默认模板
  await loadPreprocessTemplate(activeTemplate.value);
});

// 切换对比模式
const toggleCompareMode = () => {
  compareMode.value = !compareMode.value;
  if (!compareMode.value) {
    processedData.value = null; // 清除处理后的数据
  }
};

// 更新时间范围
const updateTimeRange = (range) => {
  timeRange.value = range;
};

// 处理模板变更
const handleTemplateChange = async () => {
  try {
    await loadPreprocessTemplate(activeTemplate.value);
    ElMessage.success(`已加载${activeTemplate.value}模板`);
  } catch (error) {
    console.error('加载模板失败:', error);
    ElMessage.error('加载模板失败');
  }
};

// 处理处理器产生的数据更新
const handleProcessComplete = (data) => {
  processedData.value = data;
  compareMode.value = true;
  
  // 保存当前步骤的处理结果
  savePreprocessingResults();
};

// 保存预处理结果
const savePreprocessingResults = () => {
  if (!processedData.value) return;
  
  try {
    // 保存处理结果
    saveResults(activeProcessor.value, processedData.value);
    ElMessage.success('处理结果已保存');
  } catch (error) {
    console.error('保存处理结果失败:', error);
    ElMessage.error('保存处理结果失败');
  }
};

// 进入下一步处理
const goToNextProcessingStep = () => {
  if (!nextStep.value) {
    ElMessage.info('已经是最后一个预处理步骤');
    return;
  }
  
  if (processedData.value) {
    // 如果有处理结果，先保存
    savePreprocessingResults();
  }
  
  // 切换到下一个处理器
  activeProcessor.value = nextStep.value.key;
};

// 渲染当前激活的处理器组件
const activeProcessorComponent = computed(() => {
  const step = processingSteps.find(step => step.key === activeProcessor.value);
  return step ? step.component : null;
});
</script>

<template>
  <div class="preprocessing-container">
    <!-- 顶部控制栏 -->
    <div class="top-controls">
      <div class="template-selector">
        <span>预处理模板:</span>
        <el-select v-model="activeTemplate" @change="handleTemplateChange" size="small">
          <el-option
            v-for="item in availableTemplates"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </div>
      
      <div class="view-toggle">
        <el-button type="primary" size="small" @click="toggleCompareMode">
          {{ compareMode ? '关闭对比模式' : '开启对比模式' }}
        </el-button>
      </div>
    </div>
    
    <!-- 步骤导航 -->
    <div class="steps-navigator">
      <el-steps :active="currentStepIndex" finish-status="success" simple>
        <el-step 
          v-for="(step, index) in processingSteps" 
          :key="step.key" 
          :title="step.label"
          @click="activeProcessor = step.key"
          class="process-step"
        >
          <template #icon>
            <el-icon><component :is="step.icon" /></el-icon>
          </template>
        </el-step>
      </el-steps>
    </div>
    
    <div class="main-content">
      <!-- 参数设置区域 -->
      <div class="parameter-area">
        <component 
          :is="activeProcessorComponent" 
          :preprocessParams="preprocessParams"
          :datasetId="datasetId"
          :subjectId="subjectId"
          :originalData="originalData"
          @process-complete="handleProcessComplete"
        />
        
        <!-- 步骤导航按钮 -->
        <div class="step-navigation">
          <el-button 
            v-if="nextStep"
            type="primary" 
            @click="goToNextProcessingStep"
            :disabled="!processedData"
          >
            下一步: {{ nextStep?.label }}
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
          
          <el-button 
            v-if="!nextStep && processedData"
            type="success" 
            @click="$refs.workflowRef?.goToNextStep()"
          >
            完成预处理，进入时域分析
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- 数据显示区域 -->
      <div class="data-display">
        <!-- 对比视图 -->
        <div v-if="compareMode && originalData && processedData" class="compare-view">
          <div class="original-data">
            <h3>原始数据</h3>
            <EEGViewer 
              :data="originalData" 
              v-model:timeRange="timeRange"
              v-model:selectedChannels="selectedChannels"
              @update:timeRange="updateTimeRange"
            />
          </div>
          
          <div class="processed-data">
            <h3>处理后数据</h3>
            <EEGViewer 
              :data="processedData" 
              v-model:timeRange="timeRange"
              v-model:selectedChannels="selectedChannels"
              @update:timeRange="updateTimeRange"
            />
          </div>
        </div>
        
        <!-- 单一数据展示 -->
        <div v-else-if="originalData" class="single-view">
          <EEGViewer 
            :data="originalData" 
            v-model:timeRange="timeRange"
            v-model:selectedChannels="selectedChannels"
            @update:timeRange="updateTimeRange"
          />
        </div>
        
        <div v-else class="loading-container">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span class="loading-text">数据加载中...</span>
        </div>
      </div>
    </div>
    
    <!-- 分析流程导航 -->
    <AnalysisWorkflow 
      ref="workflowRef"
      current-step="preprocessing" 
      :dataset-id="datasetId" 
      :subject-id="subjectId" 
    />
  </div>
</template>

<style scoped>
.preprocessing-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  padding-bottom: 60px;
}

.top-controls {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

/* 步骤导航样式 */
.steps-navigator {
  margin-bottom: 20px;
  padding: 8px 0;
  border-top: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
}

.process-step {
  cursor: pointer;
}

.main-content {
  display: flex;
  flex: 1;
  gap: 20px;
  min-height: 600px;
}

.parameter-area {
  width: 280px;
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  padding: 10px;
  display: flex;
  flex-direction: column;
}

.step-navigation {
  margin-top: auto;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.data-display {
  flex: 1;
  min-height: 500px;
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  padding: 15px;
  overflow: auto;
}

.compare-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.compare-view h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.loading-container .el-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #409eff;
}

.loading-text {
  color: #606266;
  font-size: 14px;
}
</style> 