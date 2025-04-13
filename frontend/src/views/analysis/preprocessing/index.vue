<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';
import { useAnalysis } from '@/composables/useAnalysis';
import FilterProcessor from './FilterProcessor.vue';
import ResamplingProcessor from './ResamplingProcessor.vue';
import ReferenceProcessor from './ReferenceProcessor.vue';
import ICAProcessor from './ICAProcessor.vue';
import BadChannelProcessor from './BadChannelProcessor.vue';
import ArtifactProcessor from './ArtifactProcessor.vue';

// 路由和基础数据
const route = useRoute();
const router = useRouter();
const datasetId = route.params.datasetId;
const subjectId = route.params.subjectId;

// 预处理步骤定义 - 集中管理
const processingSteps = [
  { key: 'filter', label: '滤波处理', icon: 'Filter', component: FilterProcessor },
  { key: 'resample', label: '重采样', icon: 'ScaleToOriginal', component: ResamplingProcessor },
  { key: 'reference', label: '重参考', icon: 'Compass', component: ReferenceProcessor },
  { key: 'ica', label: 'ICA分析', icon: 'DataAnalysis', component: ICAProcessor },
  { key: 'badChannels', label: '坏通道检测', icon: 'CircleClose', component: BadChannelProcessor },
  { key: 'artifacts', label: '伪迹处理', icon: 'Delete', component: ArtifactProcessor }
];

// 模板选项
const availableTemplates = [
  { value: 'default', label: '默认预处理' },
  { value: 'minimal', label: '最小预处理' },
  { value: 'ds002218', label: 'DS002218 数据集预处理' }
];

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

// 用户界面状态
const compareMode = ref(false);
const timeRange = ref([0, 10]);
const activeTemplate = ref('default');
const activeProcessor = ref('filter');

// 通道控制
const processingChannels = ref([]);
const displayChannels = ref([]);

// 计算属性
const currentStepIndex = computed(() => processingSteps.findIndex(step => step.key === activeProcessor.value));
const nextStep = computed(() => currentStepIndex.value < processingSteps.length - 1 ? processingSteps[currentStepIndex.value + 1] : null);
const activeProcessorComponent = computed(() => {
  const step = processingSteps.find(step => step.key === activeProcessor.value);
  return step ? step.component : null;
});

// 初始化
onMounted(async () => {
  await fetchOriginalData();
  if (originalData.value?.channels) {
    processingChannels.value = [...originalData.value.channels];
    displayChannels.value = originalData.value.channels.slice(0, 10);
  }
  await loadPreprocessTemplate(activeTemplate.value);
});

// 通道管理
const updateProcessingChannels = (channels) => {
  if (!channels || !channels.length) return;
  
  processingChannels.value = [...channels];
  
  // 更新显示通道，确保有效性
  const validDisplayChannels = displayChannels.value.filter(ch => channels.includes(ch));
  displayChannels.value = validDisplayChannels.length > 0 
    ? validDisplayChannels 
    : channels.slice(0, Math.min(10, channels.length));
};

const updateDisplayChannels = (channels) => {
  if (!channels || !channels.length) return;
  
  // 确保显示通道是处理通道的子集
  displayChannels.value = channels.filter(ch => processingChannels.value.includes(ch));
};

// 数据处理事件处理
const handleProcessComplete = (data) => {
  if (!data) return;
  
  processedData.value = data;
  compareMode.value = true;
  
  // 更新通道列表
  if (data.channels?.length) {
    processingChannels.value = data.channels;
    
    // 更新显示通道，保持有效性
    const validChannels = displayChannels.value.filter(ch => data.channels.includes(ch));
    displayChannels.value = validChannels.length > 0 
      ? validChannels 
      : data.channels.slice(0, Math.min(10, data.channels.length));
  }
  
  // 保存结果
  saveResults(activeProcessor.value, data);
};

// UI 事件处理
const toggleCompareMode = () => {
  compareMode.value = !compareMode.value;
  if (!compareMode.value) processedData.value = null;
};

const updateTimeRange = (range) => timeRange.value = range;

const handleTemplateChange = async () => {
  try {
    await loadPreprocessTemplate(activeTemplate.value);
    ElMessage.success(`已加载${activeTemplate.value}模板`);
  } catch (error) {
    ElMessage.error('加载模板失败');
  }
};

const goToNextProcessingStep = () => {
  if (!nextStep.value) {
    ElMessage.info('已经是最后一个预处理步骤');
    return;
  }
  
  activeProcessor.value = nextStep.value.key;
};

// 通道选择对话框
const openChannelDisplaySelect = () => {
  const { openChannelSelect } = EEGViewer.setup();
  openChannelSelect(
    displayChannels.value,
    processingChannels.value,
    updateDisplayChannels
  );
};
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
          v-for="step in processingSteps" 
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
        <!-- 处理通道选择 - 仅第一步显示 -->
        <div v-if="activeProcessor === 'filter'" class="processing-channels-section">
          <h4>处理通道设置</h4>
          <el-alert type="info" :closable="false" show-icon>
            <p>请选择要进行预处理的通道。这将影响所有后续处理步骤。</p>
            <p>注：设置后不可更改</p>
          </el-alert>
          <div class="channel-action">
            <el-button 
              size="small" 
              @click="updateProcessingChannels(originalData?.channels)"
              :disabled="currentStepIndex > 0"
            >
              选择处理通道
            </el-button>
            <span class="channel-count">已选: {{ processingChannels.length }}/{{ originalData?.channels?.length || 0 }}</span>
          </div>
        </div>
        
        <!-- 当前处理器组件 -->
        <component 
          :is="activeProcessorComponent" 
          :preprocessParams="preprocessParams"
          :datasetId="datasetId"
          :subjectId="subjectId"
          :originalData="originalData"
          :processingChannels="processingChannels"  
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
        <!-- 视图控制区域 -->
        <div class="view-controls">
          <el-button size="small" @click="toggleCompareMode">
            {{ compareMode ? '单一视图' : '对比视图' }}
          </el-button>
          <el-button size="small" @click="openChannelDisplaySelect">
            显示通道选择
          </el-button>
          <span class="display-info">显示: {{ displayChannels.length }}/{{ processingChannels.length }}</span>
        </div>
        
        <!-- 对比视图 -->
        <div v-if="compareMode && originalData && processedData" class="compare-view">
          <div class="original-data">
            <h3>原始数据</h3>
            <EEGViewer 
              :data="originalData" 
              v-model:timeRange="timeRange"
              :selectedChannels="displayChannels"
              :availableChannels="processingChannels"
              @update:timeRange="updateTimeRange"
              @update:selectedChannels="updateDisplayChannels"
              :disableChannelSelect="true"
            />
          </div>
          
          <div class="processed-data">
            <h3>处理后数据</h3>
            <EEGViewer 
              :data="processedData" 
              v-model:timeRange="timeRange"
              :selectedChannels="displayChannels"
              :availableChannels="processingChannels"
              @update:timeRange="updateTimeRange"
              @update:selectedChannels="updateDisplayChannels"
              :disableChannelSelect="true"
            />
          </div>
        </div>
        
        <!-- 单一数据展示 -->
        <div v-else-if="originalData" class="single-view">
          <EEGViewer 
            :data="originalData" 
            v-model:timeRange="timeRange"
            :selectedChannels="displayChannels"
            :availableChannels="originalData.channels || []"
            @update:timeRange="updateTimeRange"
            @update:selectedChannels="updateDisplayChannels"
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

.steps-navigator {
  margin-bottom: 20px;
  padding: 8px 0;
  border-top: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
}

.process-step { cursor: pointer; }

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

.loading-text { color: #606266; font-size: 14px; }

.processing-channels-section {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px dashed #dcdfe6;
}

.channel-action {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.channel-count, .display-info {
  margin-left: 10px;
  font-size: 12px;
  color: #606266;
}

.view-controls {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}
</style> 