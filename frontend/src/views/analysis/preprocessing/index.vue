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
  loadPreprocessTemplate
} = useAnalysis(datasetId, subjectId);

// 数据状态
const compareMode = ref(false);
const timeRange = ref([0, 10]);
const selectedChannels = ref([]);
const activeTemplate = ref('default');
const activeProcessor = ref('filter'); // 当前激活的处理器

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
};

// 渲染当前激活的处理器组件
const activeProcessorComponent = computed(() => {
  switch (activeProcessor.value) {
    case 'filter':
      return FilterProcessor;
    case 'resample':
      return ResamplingProcessor;
    case 'reference':
      return ReferenceProcessor;
    case 'ica':
      return ICAProcessor;
    case 'badChannels':
      return BadChannelProcessor;
    case 'artifacts':
      return ArtifactProcessor;
    default:
      return null;
  }
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
    
    <div class="main-content">
      <!-- 侧边处理器选择器 -->
      <div class="processor-selector">
        <el-menu
          :default-active="activeProcessor"
          @select="activeProcessor = $event"
          class="processor-menu"
        >
          <el-menu-item index="filter">
            <el-icon><Filter /></el-icon>
            <span>滤波处理</span>
          </el-menu-item>
          <el-menu-item index="resample">
            <el-icon><ScaleToOriginal /></el-icon>
            <span>重采样</span>
          </el-menu-item>
          <el-menu-item index="reference">
            <el-icon><Compass /></el-icon>
            <span>重参考</span>
          </el-menu-item>
          <el-menu-item index="ica">
            <el-icon><DataAnalysis /></el-icon>
            <span>ICA分析</span>
          </el-menu-item>
          <el-menu-item index="badChannels">
            <el-icon><CircleClose /></el-icon>
            <span>坏通道检测</span>
          </el-menu-item>
          <el-menu-item index="artifacts">
            <el-icon><Delete /></el-icon>
            <span>伪迹处理</span>
          </el-menu-item>
        </el-menu>
      </div>
      
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
  margin-bottom: 20px;
}

.main-content {
  display: flex;
  flex: 1;
  gap: 20px;
  min-height: 600px;
}

.processor-selector {
  width: 200px;
}

.processor-menu {
  height: 100%;
  border-right: 1px solid #e6e6e6;
}

.parameter-area {
  width: 300px;
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  padding: 10px;
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