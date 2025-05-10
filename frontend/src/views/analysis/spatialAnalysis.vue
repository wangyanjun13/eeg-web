<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
import TopoMap from '@/components/analysis/TopoMap.vue';
import { useLoading } from '@/composables/useLoading';
import { useFormState } from '@/composables/useFormState';
import analysisService from '@/services/analysisService';
import datasetService from '@/services/dataset';
import { useChannelPositions } from '@/composables/useChannelPositions';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';

const route = useRoute();
const router = useRouter();
const datasetId = computed(() => route.params.datasetId);
const subjectId = computed(() => route.params.subjectId);

// 数据状态
const topoData = ref(null);
const availableTimePoints = ref([]);
const selectedTimePoint = ref(null);
const availableFrequencyBands = ref([
  { value: 'delta', label: 'Delta (1-4 Hz)' },
  { value: 'theta', label: 'Theta (4-8 Hz)' },
  { value: 'alpha', label: 'Alpha (8-13 Hz)' },
  { value: 'beta', label: 'Beta (13-30 Hz)' },
  { value: 'gamma', label: 'Gamma (30-45 Hz)' }
]);
const selectedFrequencyBand = ref('alpha');
const preprocessedDataAvailable = ref(false);
const preprocessedData = ref(null);
const availableChannels = ref([]);
const selectedChannels = ref([]);

// 加载状态
const { isLoading, withLoading } = useLoading({
  data: false,
  applying: false
});

// 分析表单
const { formState: analysisOptions, resetForm } = useFormState('spatial-analysis-options', {
  // 插值设置
  interpolation: {
    method: 'spline', // spline, linear, nearest
    resolution: 64 // 插值分辨率
  },
  // 显示设置
  display: {
    colorMap: 'jet', // jet, viridis, plasma, inferno
    showContour: true,
    showElectrodes: true,
    normalize: true
  }
});

// 当前活动标签页
const activeTab = ref('topo');

// 通道选择
const { 
  openChannelSelect, 
  renderChannelSelectDialog 
} = useChannelPositions();

// 选择通道
const handleSelectChannels = () => {
  openChannelSelect(
    selectedChannels.value,
    availableChannels.value,
    (selected) => {
      selectedChannels.value = selected;
    }
  );
};

// 加载受试者信息
const loadSubjectInfo = async () => {
  try {
    const response = await datasetService.getSubjectInfo(datasetId.value, subjectId.value);
    if (response.data) {
      console.log('受试者信息:', response.data);
      if (response.data.channels) {
        availableChannels.value = response.data.channels;
        // 默认选择前5个通道或全部通道（如果少于5个）
        selectedChannels.value = availableChannels.value.slice(0, Math.min(5, availableChannels.value.length));
      }
    }
  } catch (error) {
    ElMessage.error('加载受试者信息失败');
    console.error(error);
  }
};

// 加载预处理数据
const loadPreprocessedData = () => {
  try {
    const preprocessedDataStr = localStorage.getItem('preprocessed_data');
    if (!preprocessedDataStr) {
      return false;
    }
    
    const parsedData = JSON.parse(preprocessedDataStr);
    
    // 检查数据是否匹配当前数据集和受试者
    if (parsedData.datasetId !== datasetId.value || 
        parsedData.subjectId !== subjectId.value) {
      console.log('预处理数据不匹配当前数据集/受试者');
      return false;
    }
    
    // 检查数据是否过期（24小时）
    const dataAge = Date.now() - parsedData.timestamp;
    const oneDayMs = 24 * 60 * 60 * 1000;
    
    if (dataAge >= oneDayMs) {
      console.log('预处理数据已过期，已移除');
      localStorage.removeItem('preprocessed_data');
      return false;
    }
    
    // 数据有效，可以使用
    preprocessedData.value = parsedData;
    preprocessedDataAvailable.value = true;
    
    // 更新可用通道
    if (parsedData.data && parsedData.data.channels) {
      availableChannels.value = parsedData.data.channels;
      // 选择所有预处理后的通道，因为这些是用户已经筛选过的
      selectedChannels.value = [...parsedData.data.channels];
      ElMessage.info('已加载预处理数据');
    }
    
    return true;
  } catch (error) {
    console.error('加载预处理数据失败:', error);
    ElMessage.warning('加载预处理数据失败，将使用原始数据');
    return false;
  }
};

// 运行空间分析
const runSpatialAnalysis = async () => {
  try {
    const params = {
      frequencyBand: selectedFrequencyBand.value,
      timePoint: selectedTimePoint.value,
      channels: selectedChannels.value,
      ...analysisOptions
    };
    
    // 如果有预处理数据，添加到请求参数中
    if (preprocessedDataAvailable.value && preprocessedData.value) {
      params.use_preprocessed_data = true;
      params.preprocessed_data = preprocessedData.value.data;
    }
    
    console.log('发送空间分析请求:', {
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      params
    });
    
    const response = await withLoading(
      analysisService.performSpatialAnalysis(datasetId.value, subjectId.value, params),
      'applying'
    );
    
    if (response.data) {
      topoData.value = response.data;
      availableTimePoints.value = response.data.timePoints || [];
      if (availableTimePoints.value.length > 0 && !selectedTimePoint.value) {
        selectedTimePoint.value = availableTimePoints.value[0];
      }
      ElMessage.success('空间分析完成');
    }
  } catch (error) {
    ElMessage.error('空间分析失败');
    console.error(error);
  }
};

// 加载示例数据
const loadExampleData = async () => {
  try {
    const response = await withLoading(
      analysisService.getSpatialAnalysisExample(),
      'data'
    );
    
    if (response && response.data) {
      topoData.value = response.data;
      availableTimePoints.value = response.data.timePoints || [];
      if (availableTimePoints.value.length > 0) {
        selectedTimePoint.value = availableTimePoints.value[0];
      }
      ElMessage.success('示例数据加载成功');
    }
  } catch (error) {
    console.error('加载示例数据失败:', error);
    ElMessage.error('加载示例数据失败');
  }
};

// 生命周期钩子
onMounted(async () => {
  // 先尝试加载预处理数据
  const hasPreprocessedData = loadPreprocessedData();
  
  // 如果没有预处理数据或加载失败，则加载原始数据
  if (!hasPreprocessedData) {
    await loadSubjectInfo();
  }
});

// 监听路由参数变化
watch([datasetId, subjectId], async () => {
  topoData.value = null;
  preprocessedDataAvailable.value = false;
  preprocessedData.value = null;
  
  const hasPreprocessedData = loadPreprocessedData();
  if (!hasPreprocessedData) {
    await loadSubjectInfo();
  }
});

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}
</script>

<template>
  <AppLayout>
    <div class="spatial-analysis-container">
      <h2>空间分析</h2>
      
      <el-row :gutter="20">
        <!-- 左侧控制面板 -->
        <el-col :span="6">
          <el-card class="control-panel">
            <template #header>
              <div class="card-header">
                <h3>空间分析设置</h3>
                <el-tag v-if="preprocessedDataAvailable" size="small" type="success">已加载预处理数据</el-tag>
              </div>
            </template>
            
            <el-form :model="analysisOptions" label-width="120px" label-position="left">
              <!-- 通道选择 -->
              <el-form-item label="通道选择">
                <el-button type="primary" size="small" @click="handleSelectChannels">
                  选择通道 ({{ selectedChannels.length }}/{{ availableChannels.length }})
                </el-button>
                <div v-if="selectedChannels.length > 0" class="selected-channels-info">
                  已选: {{ selectedChannels.slice(0, 3).join(', ') }}
                  <span v-if="selectedChannels.length > 3">等{{ selectedChannels.length }}个通道</span>
                </div>
              </el-form-item>
              
              <!-- 频带选择 -->
              <el-form-item label="频带选择">
                <el-select v-model="selectedFrequencyBand" placeholder="选择频带">
                  <el-option
                    v-for="band in availableFrequencyBands"
                    :key="band.value"
                    :label="band.label"
                    :value="band.value"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 时间点选择 -->
              <el-form-item label="时间点" v-if="availableTimePoints.length > 0">
                <el-select v-model="selectedTimePoint" placeholder="选择时间点">
                  <el-option
                    v-for="time in availableTimePoints"
                    :key="time"
                    :label="`${time} ms`"
                    :value="time"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 插值方法 -->
              <el-form-item label="插值方法">
                <el-select v-model="analysisOptions.interpolation.method">
                  <el-option label="样条插值" value="spline" />
                  <el-option label="线性插值" value="linear" />
                  <el-option label="最近邻插值" value="nearest" />
                </el-select>
              </el-form-item>
              
              <!-- 插值分辨率 -->
              <el-form-item label="插值分辨率">
                <el-slider
                  v-model="analysisOptions.interpolation.resolution"
                  :min="32"
                  :max="128"
                  :step="16"
                  show-input
                />
              </el-form-item>
              
              <!-- 显示设置 -->
              <el-form-item label="显示设置">
                <el-checkbox v-model="analysisOptions.display.showContour">显示等高线</el-checkbox>
                <el-checkbox v-model="analysisOptions.display.showElectrodes">显示电极位置</el-checkbox>
                <el-checkbox v-model="analysisOptions.display.normalize">归一化</el-checkbox>
              </el-form-item>
              
              <!-- 颜色映射 -->
              <el-form-item label="颜色映射">
                <el-select v-model="analysisOptions.display.colorMap">
                  <el-option label="Jet" value="jet" />
                  <el-option label="Viridis" value="viridis" />
                  <el-option label="Plasma" value="plasma" />
                  <el-option label="Inferno" value="inferno" />
                </el-select>
              </el-form-item>
            </el-form>
            
            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button @click="resetForm">重置</el-button>
              <el-button type="primary" @click="runSpatialAnalysis" :loading="isLoading.applying"
                         :disabled="selectedChannels.length === 0">
                运行分析
              </el-button>
              <el-button @click="loadExampleData" :loading="isLoading.data">
                加载示例数据
              </el-button>
              <el-button type="success" @click="goToNextStep">
                下一步
              </el-button>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧显示区域 -->
        <el-col :span="18">
          <el-card class="data-display">
            <template #header>
              <div class="card-header">
                <h3>空间分布</h3>
                <el-tabs v-model="activeTab" type="card">
                  <el-tab-pane label="头皮地形图" name="topo"></el-tab-pane>
                  <el-tab-pane label="3D视图" name="3d"></el-tab-pane>
                  <el-tab-pane label="源定位" name="source"></el-tab-pane>
                </el-tabs>
              </div>
            </template>
            
            <div v-loading="isLoading.data || isLoading.applying">
              <!-- 头皮地形图 -->
              <div v-if="activeTab === 'topo' && topoData">
                <TopoMap
                  :data="topoData"
                  :colorMap="analysisOptions.display.colorMap"
                  :title="`${selectedFrequencyBand} 频带 (${selectedTimePoint || 'N/A'} ms)`"
                />
              </div>
              
              <!-- 3D视图 -->
              <div v-else-if="activeTab === '3d' && topoData">
                <div class="placeholder">
                  <el-empty description="3D视图功能正在开发中" />
                </div>
              </div>
              
              <!-- 源定位 -->
              <div v-else-if="activeTab === 'source' && topoData">
                <div class="placeholder">
                  <el-empty description="源定位功能正在开发中" />
                </div>
              </div>
              
              <!-- 无数据提示 -->
              <div v-else class="no-data">
                <el-empty description="暂无数据，请运行分析或加载示例数据" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 分析流程导航 -->
      <AnalysisWorkflow 
        ref="workflowRef"
        current-step="spatial" 
        :dataset-id="datasetId" 
        :subject-id="subjectId" 
      />
    </div>
    
    <!-- 通道选择对话框 -->
    <component :is="renderChannelSelectDialog()" />
  </AppLayout>
</template>

<style scoped>
.spatial-analysis-container {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.control-panel {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 10px;
}

.data-display {
  height: calc(100vh - 180px);
  overflow: auto;
}

.no-data, .placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.selected-channels-info {
  font-size: 13px;
  color: #606266;
  margin-top: 8px;
}
</style> 