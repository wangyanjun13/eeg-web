<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
// import ERPChart from '@/components/analysis/ERPChart.vue';
import TimeSeriesChart from '@/components/analysis/TimeSeriesChart.vue';
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
const erpData = ref(null);
const availableChannels = ref([]);
const selectedChannels = ref([]);
const availableEvents = ref([]);
const selectedEvents = ref([]);

// 加载状态
const { isLoading, withLoading } = useLoading({
  data: false,
  applying: false
});

// 分析表单
const { formState: analysisOptions, resetForm } = useFormState('time-analysis-options', {
  // 基线校正
  baseline: {
    enabled: true,
    start: -200,
    end: 0
  },
  // 平均方式
  averaging: {
    method: 'mean', // mean, median
    removeOutliers: false,
    outlierThreshold: 2.5
  },
  // 显示设置
  display: {
    showIndividual: false,
    showStd: true,
    colorByCondition: true
  }
});

// 当前活动标签页
const activeTab = ref('erp');

// 通道选择
const { 
  openChannelSelect, 
  renderChannelSelectDialog 
} = useChannelPositions();

// 加载受试者信息和可用通道
const loadSubjectInfo = async () => {
  try {
    const response = await datasetService.getSubjectInfo(datasetId.value, subjectId.value);
    if (response.data && response.data.channels) {
      availableChannels.value = response.data.channels;
      // 默认选择前5个通道
      selectedChannels.value = availableChannels.value.slice(0, 5);
    }
    
    // 加载事件标记
    if (response.data && response.data.events) {
      availableEvents.value = response.data.events;
      // 默认选择所有事件
      selectedEvents.value = availableEvents.value.map(event => event.id);
    }
  } catch (error) {
    ElMessage.error('加载受试者信息失败');
    console.error(error);
  }
};

// 运行时域分析
const runTimeAnalysis = async () => {
  if (selectedChannels.value.length === 0) {
    ElMessage.warning('请至少选择一个通道');
    return;
  }
  
  if (selectedEvents.value.length === 0) {
    ElMessage.warning('请至少选择一个事件');
    return;
  }
  
  try {
    const params = {
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      channels: selectedChannels.value,
      events: selectedEvents.value,
      ...analysisOptions
    };
    
    const response = await withLoading(
      analysisService.performTimeAnalysis(params),
      'applying'
    );
    
    erpData.value = response.data;
    ElMessage.success('时域分析完成');
  } catch (error) {
    ElMessage.error('时域分析失败');
    console.error(error);
  }
};

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

// 加载示例数据（用于开发测试）
const loadExampleData = async () => {
  try {
    const response = await withLoading(
      analysisService.getExampleTimeData(),
      'data'
    );
    erpData.value = response.data;
    ElMessage.success('加载示例数据成功');
  } catch (error) {
    ElMessage.error('加载示例数据失败');
    console.error(error);
  }
};

// 生命周期钩子
onMounted(() => {
  loadSubjectInfo();
});

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}
</script>

<template>
  <AppLayout>
    <div class="time-analysis-container">
      <h2>时域分析</h2>
      
      <el-row :gutter="20">
        <!-- 左侧控制面板 -->
        <el-col :span="6">
          <el-card class="control-panel">
            <template #header>
              <div class="card-header">
                <h3>时域分析设置</h3>
              </div>
            </template>
            
            <el-form :model="analysisOptions" label-width="120px">
              <!-- 通道选择 -->
              <el-form-item label="选择通道">
                <div class="channel-selection">
                  <el-button @click="handleSelectChannels" :disabled="isLoading.data">
                    选择通道 ({{ selectedChannels.length }})
                  </el-button>
                  <div v-if="selectedChannels.length > 0" class="selected-channels">
                    已选: {{ selectedChannels.slice(0, 3).join(', ') }}
                    <span v-if="selectedChannels.length > 3">
                      等{{ selectedChannels.length }}个通道
                    </span>
                  </div>
                </div>
              </el-form-item>
              
              <!-- 事件选择 -->
              <el-form-item label="选择事件">
                <el-select 
                  v-model="selectedEvents" 
                  multiple 
                  placeholder="选择事件"
                  style="width: 100%"
                >
                  <el-option 
                    v-for="event in availableEvents" 
                    :key="event.id" 
                    :label="event.name" 
                    :value="event.id"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 基线校正 -->
              <el-form-item label="基线校正">
                <el-switch v-model="analysisOptions.baseline.enabled" />
                <div v-if="analysisOptions.baseline.enabled" class="baseline-range">
                  <el-input-number 
                    v-model="analysisOptions.baseline.start" 
                    :min="-1000" 
                    :max="0" 
                    :step="50"
                    size="small"
                  />
                  <span class="range-separator">至</span>
                  <el-input-number 
                    v-model="analysisOptions.baseline.end" 
                    :min="-500" 
                    :max="500" 
                    :step="50"
                    size="small"
                  />
                  <span class="time-unit">ms</span>
                </div>
              </el-form-item>
              
              <!-- 平均方式 -->
              <el-form-item label="平均方式">
                <el-radio-group v-model="analysisOptions.averaging.method">
                  <el-radio label="mean">均值</el-radio>
                  <el-radio label="median">中位数</el-radio>
                </el-radio-group>
                <div class="outlier-removal">
                  <el-checkbox v-model="analysisOptions.averaging.removeOutliers">
                    移除离群值
                  </el-checkbox>
                  <el-input-number 
                    v-if="analysisOptions.averaging.removeOutliers"
                    v-model="analysisOptions.averaging.outlierThreshold" 
                    :min="1" 
                    :max="5" 
                    :step="0.1"
                    size="small"
                    style="width: 100px; margin-left: 10px;"
                  />
                  <span v-if="analysisOptions.averaging.removeOutliers">
                    标准差
                  </span>
                </div>
              </el-form-item>
              
              <!-- 显示设置 -->
              <el-form-item label="显示设置">
                <el-checkbox v-model="analysisOptions.display.showIndividual">
                  显示单次试次
                </el-checkbox>
                <el-checkbox v-model="analysisOptions.display.showStd">
                  显示标准差
                </el-checkbox>
                <el-checkbox v-model="analysisOptions.display.colorByCondition">
                  按条件着色
                </el-checkbox>
              </el-form-item>
            </el-form>
            
            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button @click="resetForm">重置</el-button>
              <el-button type="primary" @click="runTimeAnalysis" :loading="isLoading.applying">
                运行分析
              </el-button>
              <el-button @click="loadExampleData" :loading="isLoading.data">
                加载示例数据
              </el-button>
              <el-button type="success" @click="goToNextStep">下一步</el-button>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧数据显示 -->
        <el-col :span="18">
          <el-card class="data-display">
            <template #header>
              <div class="card-header">
                <el-tabs v-model="activeTab">
                  <el-tab-pane label="ERP波形" name="erp" />
                  <el-tab-pane label="单次试次" name="single-trial" />
                  <el-tab-pane label="时间序列" name="time-series" />
                </el-tabs>
              </div>
            </template>
            
            <div v-loading="isLoading.data">
              <!-- ERP波形 -->
              <div v-if="activeTab === 'erp' && erpData">
                <!-- ERPChart 
                  :data="erpData.erp" 
                  :events="erpData.events"
                  :timeWindow="analysisOptions.display.timeWindow"
                /> -->
              </div>
              
              <!-- 单次试次 -->
              <div v-else-if="activeTab === 'single-trial' && erpData">
                <TimeSeriesChart 
                  :data="erpData.singleTrials" 
                  :channels="selectedChannels"
                  :timeRange="[analysisOptions.display.timeWindow[0]/1000, analysisOptions.display.timeWindow[1]/1000]"
                />
              </div>
              
              <!-- 时间序列 -->
              <div v-else-if="activeTab === 'time-series' && erpData">
                <TimeSeriesChart 
                  :data="erpData.timeSeries" 
                  :channels="selectedChannels"
                  :timeRange="[0, 10]"
                />
              </div>
              
              <!-- 无数据提示 -->
              <div v-else class="no-data">
                <el-empty description="暂无分析数据，请运行分析或加载示例数据" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 分析流程导航 -->
      <AnalysisWorkflow 
        ref="workflowRef"
        current-step="time" 
        :dataset-id="datasetId" 
        :subject-id="subjectId" 
      />
    </div>
  </AppLayout>
  
  <!-- 通道选择对话框 -->
  <component :is="renderChannelSelectDialog()" />
</template>

<style scoped>
.time-analysis-container {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
  padding-bottom: 60px;
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

.channel-selection, .selected-channels {
  margin-top: 8px;
}

.selected-channels {
  font-size: 12px;
  color: #606266;
  margin-top: 8px;
}

.baseline-range {
  display: flex;
  align-items: center;
  margin-top: 8px;
}

.range-separator, .time-unit {
  margin: 0 8px;
}

.outlier-removal {
  margin-top: 8px;
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

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}
</style> 