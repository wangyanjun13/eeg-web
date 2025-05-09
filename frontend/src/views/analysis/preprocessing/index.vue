<script setup>
import { ref, onMounted, computed, markRaw, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading, InfoFilled } from '@element-plus/icons-vue';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';
import { useAnalysis } from '@/composables/useAnalysis';
import FilterProcessor from './FilterProcessor.vue';
import ResamplingProcessor from './ResamplingProcessor.vue';
import ReferenceProcessor from './ReferenceProcessor.vue';
import ICAProcessor from './ICAProcessor.vue';
import BadChannelProcessor from './BadChannelProcessor.vue';
import ArtifactProcessor from './ArtifactProcessor.vue';
import SegmentProcessor from './SegmentProcessor.vue';
import BadSegmentProcessor from './BadSegmentProcessor.vue';

// 路由和基础数据
const route = useRoute();
const router = useRouter();
const datasetId = route.params.datasetId;
const subjectId = route.params.subjectId;

// 预处理步骤定义 - 集中管理
const processingSteps = ref([
  { key: 'filter', label: '滤波处理', icon: 'Filter', component: markRaw(FilterProcessor) },
  { key: 'resample', label: '重采样', icon: 'ScaleToOriginal', component: markRaw(ResamplingProcessor) },
  { key: 'segment', label: '数据分段', icon: 'ScaleToOriginal', component: markRaw(SegmentProcessor) },
  { key: 'badChannels', label: '坏通道检测', icon: 'CircleClose', component: markRaw(BadChannelProcessor) },
  { key: 'badSegments', label: '坏段剔除', icon: 'Delete', component: markRaw(BadSegmentProcessor) },
  { key: 'reference', label: '重参考', icon: 'Compass', component: markRaw(ReferenceProcessor) },
  { key: 'ica', label: 'ICA分析', icon: 'DataAnalysis', component: markRaw(ICAProcessor) },
  { key: 'artifacts', label: '伪迹处理', icon: 'Delete', component: markRaw(ArtifactProcessor) }
]);

// 使用分析组合函数
const {
  isLoading,
  originalData,
  processedData,
  preprocessParams,
  fetchOriginalData,
  saveResults
} = useAnalysis(datasetId, subjectId);

// 用户界面状态
const timeRange = ref([0, 10]);
const activeProcessor = ref('filter');
const viewMode = ref('time');

// 通道控制
const processingChannels = ref([]);
const displayChannels = ref([]);

// 状态管理
const processingStatus = ref({});
const activeStepIndex = ref(0);
const completedSteps = ref([]);

// 计算属性
const currentComponent = computed(() => processingSteps.value[activeStepIndex.value].component);

const currentStepInput = computed(() => {
  return activeStepIndex.value === 0 ? originalData.value : 
         processedData.value ? processedData.value : originalData.value;
});

const disableChannelSelection = computed(() => activeStepIndex.value !== 0);

// 获取步骤状态
const getStepStatus = (stepKey) => {
  const index = processingSteps.value.findIndex(step => step.key === stepKey);
  
  if (index === activeStepIndex.value) return 'process';
  if (completedSteps.value.includes(stepKey)) return 'success';
  if (index < activeStepIndex.value) return 'finish';
  
  return 'wait';
};

// 判断是否可以切换到目标步骤
const canSwitchToStep = (targetIndex) => {
  if (targetIndex < activeStepIndex.value) return true;
  
  // 检查所有前置步骤是否已完成
  for (let i = 0; i < targetIndex; i++) {
    if (!completedSteps.value.includes(processingSteps.value[i].key)) {
      return false;
    }
  }
  return true;
};

// 数据刷新工具函数
const refreshData = (data, callback) => {
  setTimeout(() => {
    originalData.value = null;
    processedData.value = null;
    
    setTimeout(() => {
      if (data) originalData.value = JSON.parse(JSON.stringify(data));
      if (callback) callback();
    }, 0);
  }, 0);
};

// 保存结果并处理错误
const saveResultSafely = (key, data) => {
  if (!data) {
    console.warn('尝试保存空数据');
    return false;
  }
  
  try {
    // 创建深度复制以避免引用问题
    const dataCopy = JSON.parse(JSON.stringify(data));
    
    // 保存到全局存储对象
    if (typeof window !== 'undefined') {
      if (!window.savedResults) window.savedResults = {};
      window.savedResults[key] = dataCopy;
    }
    
    // 尝试保存到状态管理
    try {
      saveResults(key, dataCopy);
    } catch (e) {
      console.warn('保存到localStorage失败，但流程继续', e);
    }
    
    return true;
  } catch (e) {
    console.warn('数据序列化失败，可能含有循环引用', e);
    
    // 如果序列化失败，尝试使用更安全的方式
    try {
      // 简单地复制主要字段而非整个对象
      const safeData = {
        channels: data.channels ? [...data.channels] : [],
        times: data.times ? data.times.slice(0, 10) : [], // 只保存少量时间点作为示例
        sampling_rate: data.sampling_rate,
        duration: data.duration,
        from_cache: data.from_cache,
        process_time: data.process_time
      };
      
      if (typeof window !== 'undefined') {
        if (!window.savedResults) window.savedResults = {};
        window.savedResults[key] = safeData;
      }
      
      saveResults(key, safeData);
      return true;
    } catch (fallbackError) {
      console.error('备用保存方法也失败', fallbackError);
      return false;
    }
  }
};

// 处理点击上一步
const handlePrevStep = () => {
  if (activeStepIndex.value > 0) {
    handleStepClick(activeStepIndex.value - 1);
  }
};

// 处理步骤点击
const handleStepClick = async (stepIndex) => {
  if (!canSwitchToStep(stepIndex)) {
    ElMessage.warning('请先完成前面的步骤');
    return;
  }
  
  // 处理返回前面的步骤
  if (stepIndex < activeStepIndex.value) {
    try {
      await ElMessageBox.confirm(
        '返回前面的步骤可能会丢失后续处理结果，确定要返回吗？',
        '提示',
        { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
      );
      
      // 清除后续步骤的完成状态
      completedSteps.value = completedSteps.value.filter(step => {
        const idx = processingSteps.value.findIndex(s => s.key === step);
        return idx < stepIndex;
      });
      
      // 确定要恢复的数据
      let dataToRestore;
      if (stepIndex === 0) {
        await fetchOriginalData();
        dataToRestore = originalData.value;
      } else {
        const prevStepKey = processingSteps.value[stepIndex - 1].key;
        dataToRestore = window.savedResults?.[prevStepKey] || 
                       (await fetchOriginalData(), originalData.value);
      }
      
      // 更新步骤索引
      activeStepIndex.value = stepIndex;
      activeProcessor.value = processingSteps.value[stepIndex].key;
      
      // 强制刷新数据
      refreshData(dataToRestore);
      
    } catch (e) {
      // 用户取消
      return;
    }
  } else if (stepIndex > activeStepIndex.value) {
    // 调用 handleNextStep 处理向前跳转
    handleNextStep();
  }
};

// 处理下一步按钮点击
const handleNextStep = async () => {
  if (activeStepIndex.value < processingSteps.value.length - 1) {
    const currentStepKey = processingSteps.value[activeStepIndex.value].key;
    let currentResult;
    
    // 如果当前步骤未完成，提示确认
    if (!completedSteps.value.includes(currentStepKey)) {
      try {
        await ElMessageBox.confirm(
          `您尚未应用${processingSteps.value[activeStepIndex.value].label}处理，是否直接进入${processingSteps.value[activeStepIndex.value + 1].label}步骤？`,
          '提示',
          { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
        );
        
        // 标记为已完成并保存当前输入作为结果
        completedSteps.value.push(currentStepKey);
        currentResult = processedData.value || originalData.value;
        
        // 保存结果
        saveResultSafely(currentStepKey, currentResult);
      } catch (e) {
        return; // 用户取消
      }
    } else {
      // 已完成，使用处理结果
      currentResult = processedData.value || originalData.value;
      saveResultSafely(currentStepKey, currentResult);
    }
    
    // 获取要传递的数据（首选内存中的数据）
    // 增加安全检查
    let dataToPass;
    
    if (typeof window !== 'undefined' && window.savedResults && window.savedResults[currentStepKey]) {
      dataToPass = window.savedResults[currentStepKey];
    } else if (currentResult) {
      dataToPass = currentResult;
      console.warn(`未找到${currentStepKey}的保存结果，使用当前结果`);
    } else {
      console.error('无法获取有效的处理结果数据');
      ElMessage.error('处理数据不完整，无法继续');
      return;
    }
    
    // 确保timeRange存在                                                                                                                                                                                                                                                                                                                                                      
    if (!dataToPass.timeRange && timeRange.value) {
      console.log('添加缺失的时间范围信息:', timeRange.value);
      dataToPass.timeRange = [...timeRange.value];
    }
    
    // 防止空数据
    if (!dataToPass || !dataToPass.channels || dataToPass.channels.length === 0) {
      console.error('数据无效，缺少通道信息');
      ElMessage.error('处理数据不完整，无法继续');
      return;
    }
    
    // 更新步骤索引
    const nextStepIndex = activeStepIndex.value + 1;
    activeStepIndex.value = nextStepIndex;
    activeProcessor.value = processingSteps.value[nextStepIndex].key;
    
    // 输出调试信息，查看数据内容
    console.log('切换到下一步，数据采样率:', dataToPass.sampling_rate);
    
    // 强制刷新数据，确保Vue检测到变化
    refreshData(dataToPass);
  }
};

// 处理完成回调
const handleProcessComplete = (data, processorKey) => {
  if (!data) {
    console.error('处理结果为空');
    ElMessage.warning('处理结果为空，无法显示');
    return;
  }
  
  try {
    // 确保数据是对象而非字符串
    let processedResult = typeof data === 'string' ? JSON.parse(data) : {...data};
    
    // 保存原始数据的时间范围以确保一致性
    const originalTimeRange = originalData.value?.timeRange || 
                            (originalData.value?.times && originalData.value.times.length > 1 ? 
                            [originalData.value.times[0], originalData.value.times[originalData.value.times.length - 1]] : 
                            null);
    
    console.log('原始数据时间范围:', originalTimeRange);
    console.log('处理结果时间范围:', processedResult.timeRange);
    
    // 基本数据验证和补全 - 保持简单
    if (!processedResult.data) processedResult.data = {};
    
    // 确保channels数组存在
    if (!processedResult.channels || !Array.isArray(processedResult.channels)) {
      processedResult.channels = Object.keys(processedResult.data);
      if (processedResult.channels.length === 0 && originalData.value?.channels) {
        processedResult.channels = [...originalData.value.channels];
      }
    }
    
    // 确保times数组存在
    if (!processedResult.times || !Array.isArray(processedResult.times)) {
      const timeLength = processedResult.data && Object.keys(processedResult.data).length > 0 
        ? processedResult.data[Object.keys(processedResult.data)[0]].length 
        : 100;
      processedResult.times = Array.from({length: timeLength}, (_, i) => i / 10);
    }
    
    // 确保每个通道都有数据 - 保持简单的填充
    processedResult.channels.forEach(channel => {
      if (!processedResult.data[channel]) {
        processedResult.data[channel] = Array(processedResult.times.length).fill(0);
      }
    });
    
    // 确保必要的元数据存在
    processedResult.sampling_rate = processedResult.sampling_rate || 100;
    processedResult.dataset_id = processedResult.dataset_id || datasetId;
    processedResult.subject_id = processedResult.subject_id || subjectId;
    
    // 改进的时间范围处理逻辑
    // 1. 优先使用处理结果自带的时间范围(来自后端)
    // 2. 如果没有，使用原始数据的时间范围(保持一致性)
    // 3. 如果原始数据没有时间范围，则从times数组计算
    // 4. 最后才使用默认范围
    if (!processedResult.timeRange) {
      if (originalTimeRange) {
        console.log('应用原始数据的时间范围:', originalTimeRange);
        processedResult.timeRange = originalTimeRange;
      } else if (processedResult.times && processedResult.times.length > 1) {
        const calculatedRange = [processedResult.times[0], processedResult.times[processedResult.times.length - 1]];
        console.log('从times数组计算时间范围:', calculatedRange);
        processedResult.timeRange = calculatedRange;
      } else {
        // 设置duration(持续时间)
        processedResult.duration = processedResult.duration || 10;
        console.log('使用默认时间范围:', [0, processedResult.duration]);
        processedResult.timeRange = [0, processedResult.duration];
      }
    } else {
      // 输出诊断信息
      console.log('处理结果已包含时间范围:', processedResult.timeRange);
      
      // 对于分段后的数据，确保duration与时间范围一致
      if (processorKey === 'segment' || processingSteps.value.findIndex(s => s.key === 'segment') < processingSteps.value.findIndex(s => s.key === processorKey)) {
        processedResult.duration = processedResult.timeRange[1] - processedResult.timeRange[0];
        console.log('基于分段后的时间范围更新duration:', processedResult.duration);
      } else {
        // 对于其他情况，设置默认duration
        processedResult.duration = processedResult.duration || (processedResult.timeRange ? (processedResult.timeRange[1] - processedResult.timeRange[0]) : 10);
      }
    }
    
    // 更新处理后数据
    processedData.value = processedResult;
    
    // 同步UI显示的时间范围
    if (processedResult.timeRange) {
      timeRange.value = [...processedResult.timeRange];
      console.log('更新UI时间范围:', timeRange.value);
    }
    
    // 只更新显示通道，保留原始处理通道
    if (processedResult.channels?.length) {
      // 保持显示通道一致性
      const validChannels = displayChannels.value.filter(ch => processedResult.channels.includes(ch));
      displayChannels.value = validChannels.length ? 
                            [...validChannels] : 
                            [...processedResult.channels.slice(0, Math.min(10, processedResult.channels.length))];
    }
    
    // 保存结果
    saveResultSafely(processorKey, processedResult);
    
    // 标记为已完成
    if (!completedSteps.value.includes(processorKey)) {
      completedSteps.value.push(processorKey);
    }
  } catch (error) {
    console.error('处理结果解析失败:', error);
    ElMessage.error(`处理结果解析失败: ${error.message}`);
  }
};

// 处理通道更新
const updateDisplayChannels = (channels) => {
  if (channels?.length) {
    displayChannels.value = channels.filter(ch => processingChannels.value.includes(ch));
  }
};

// 更新时间范围和视图模式
const updateTimeRange = (range) => timeRange.value = range;
const updateViewMode = (mode) => viewMode.value = mode;

// 完成预处理
const handleComplete = async () => {
  try {
    await ElMessageBox.confirm(
      '确定完成预处理流程吗？将进入分析阶段。',
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' }
    );
    
    router.push({
      name: 'analysis',
      params: { datasetId, subjectId }
    });
  } catch (e) {} // 用户取消
};

// 页面离开确认
const beforePageLeave = async (e) => {
  if (completedSteps.value.length > 0) {
    e.preventDefault();
    try {
      await ElMessageBox.confirm(
        '离开页面将丢失当前处理结果，确定要离开吗？',
        '提示',
        { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
      );
      window.removeEventListener('beforeunload', beforePageLeave);
      window.location.href = e.target.href;
    } catch (error) {} // 用户取消
  }
};

// 添加当前数据集和受试者ID
const currentDatasetId = ref('');
const currentSubjectId = ref('');

// 获取 URL 参数或从其他存储中获取当前选择的数据集和受试者
onMounted(() => {
  // 示例：从 URL 中获取参数
  const urlParams = new URLSearchParams(window.location.search);
  currentDatasetId.value = urlParams.get('dataset') || '';
  currentSubjectId.value = urlParams.get('subject') || '';
  
  // 如果 URL 中没有，可以尝试从 localStorage 获取最近选择的
  if (!currentDatasetId.value || !currentSubjectId.value) {
    currentDatasetId.value = localStorage.getItem('currentDatasetId') || '';
    currentSubjectId.value = localStorage.getItem('currentSubjectId') || '';
  }
});

// 处理更新后的数据
const handleProcessedData = (data) => {
  // 根据你的应用逻辑处理数据
  console.log('处理后的数据:', data);
  // 例如：更新图表数据等
  // updateChartData(data);
};

// 组件生命周期
onMounted(async () => {
  await fetchOriginalData();
  if (originalData.value?.channels) {
    processingChannels.value = [...originalData.value.channels];
    displayChannels.value = originalData.value.channels.slice(0, Math.min(10, originalData.value.channels.length));
  }
  
  // 初始化全局存储
  if (typeof window !== 'undefined') {
    window.savedResults = window.savedResults || {};
  }
  
  // 添加事件监听
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', beforePageLeave);
  }
  
  // 读取之前保存的时间范围
  const savedTimeRange = localStorage.getItem('selected_time_range');
  if (savedTimeRange) {
    try {
      const parsedRange = JSON.parse(savedTimeRange);
      timeRange.value = parsedRange;
    } catch (e) {
      console.error('解析保存的时间范围失败:', e);
    }
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforePageLeave);
});
</script>

<template>
  <div class="preprocessing-container">
    <!-- 步骤导航 -->
    <div class="steps-nav">
      <el-steps :active="activeStepIndex" finish-status="success">
        <el-step 
          v-for="(step, index) in processingSteps" 
          :key="step.key" 
          :title="step.label"
          :status="getStepStatus(step.key)"
          @click="handleStepClick(index)"
        />
      </el-steps>
    </div>
    
    <div class="main-content">
      <!-- 参数设置区域 -->
      <div class="parameter-area">
        <!-- 处理通道信息 -->
        <div v-if="activeProcessor === 'filter'" class="processing-channels-section">
          <div class="channel-header">
            <h4>处理通道</h4>
            <el-tooltip placement="right" content="预处理将应用于所有可用通道">
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
          <div class="channel-compact-action">
            <span class="channel-count">通道数量: {{ processingChannels.length }}</span>
          </div>
        </div>
        
        <!-- 当前处理器组件 -->
        <component 
          :is="currentComponent" 
          :preprocessParams="preprocessParams"
          :datasetId="datasetId"
          :subjectId="subjectId"
          :originalData="currentStepInput"
          :processingChannels="processingChannels"  
          @process-complete="(data) => handleProcessComplete(data, processingSteps[activeStepIndex].key)"
        />
        
        <!-- 步骤导航按钮 -->
        <div class="step-navigation">
          <el-button 
            @click="handlePrevStep" 
            :disabled="activeStepIndex <= 0 || isLoading">
            上一步
          </el-button>
          <el-button 
            type="primary" 
            @click="handleNextStep" 
            :disabled="activeStepIndex >= processingSteps.length - 1 || isLoading">
            下一步
          </el-button>
          <el-button 
            type="success" 
            @click="handleComplete" 
            :disabled="isLoading">
            完成预处理
          </el-button>
        </div>
      </div>
      
      <!-- 数据显示区域 -->
      <div class="data-display">
        <!-- 视图控制区域 -->
        <div class="view-controls">
          <el-radio-group v-model="viewMode" size="small" class="view-mode-selector">
            <el-radio-button label="time">时域</el-radio-button>
            <el-radio-button label="frequency">频域</el-radio-button>
          </el-radio-group>
          <span class="display-info">显示: {{ displayChannels.length }}/{{ processingChannels.length }}</span>
        </div>
        
        <!-- 数据对比视图 -->
        <div v-if="originalData" class="compare-view">
          <div class="original-data">
            <h3>处理前数据</h3>
            <EEGViewer 
              :data="originalData" 
              v-model:timeRange="timeRange"
              :selectedChannels="displayChannels"
              :availableChannels="processingChannels"
              @update:timeRange="updateTimeRange"
              @update:selectedChannels="updateDisplayChannels"
              :disableChannelSelect="disableChannelSelection"
              :viewMode="viewMode"
              @update:viewMode="updateViewMode"
            />
          </div>
          
          <div class="processed-data">
            <h3>{{ processedData ? '处理后数据' : '等待处理' }}</h3>
            <EEGViewer 
              v-if="processedData"
              :data="processedData" 
              v-model:timeRange="timeRange"
              :selectedChannels="displayChannels"
              :availableChannels="processingChannels"
              @update:timeRange="updateTimeRange"
              @update:selectedChannels="updateDisplayChannels"
              :disableChannelSelect="disableChannelSelection"
              :viewMode="viewMode"
              @update:viewMode="updateViewMode"
            />
            <div v-else class="placeholder-message">
              <el-empty description="请应用处理后查看结果" />
            </div>
          </div>
        </div>
        
        <!-- 加载中状态 -->
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
  
  <!-- 处理状态显示 -->
  <div v-if="processedData && processingStatus[activeProcessor]" class="processing-status">
    <el-tag size="small" :type="processingStatus[activeProcessor].fromCache ? 'success' : 'primary'">
      {{ processingStatus[activeProcessor].fromCache ? '已从缓存加载' : '实时处理' }}
    </el-tag>
    <span v-if="processingStatus[activeProcessor].time" class="processing-time">
      处理耗时: {{ processingStatus[activeProcessor].time.toFixed(2) }}秒
    </span>
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

.steps-nav { margin-bottom: 20px; }
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
  color: #606266;
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
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px dashed #dcdfe6;
}

.channel-header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 5px;
}

.channel-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: normal;
}

.channel-compact-action {
  display: flex;
  align-items: center;
  gap: 8px;
}

.channel-count { font-size: 12px; color: #606266; }

.view-controls {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  gap: 10px;
}

.view-mode-selector {
  margin-left: auto;
  margin-right: 10px;
}

.processing-status {
  display: flex;
  align-items: center;
  margin: 5px 0;
  gap: 10px;
}

.processing-time { font-size: 12px; color: #606266; }

.placeholder-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 500px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
}
</style> 