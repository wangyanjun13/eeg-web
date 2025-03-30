<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
// import ERPChart from '@/components/analysis/ERPChart.vue';
import TimeSeriesChart from '@/components/analysis/TimeSeriesChart.vue';
import { useLoading } from '@/composables/useLoading';
import { useFormState } from '@/composables/useFormState';
import analysisService from '@/services/analysisService';

const route = useRoute();
const router = useRouter();

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
    timeWindow: [-200, 800],
    yScale: 'auto' // auto, fixed
  }
});

// 当前活动标签页
const activeTab = ref('erp');

// 重置选项
function resetOptions() {
  resetForm();
  ElMessage.success('已重置分析选项');
}

// 应用分析
async function applyAnalysis() {
  try {
    await withLoading(async () => {
      // 模拟API调用
      const result = await analysisService.performTimeAnalysis({
        channels: selectedChannels.value,
        events: selectedEvents.value,
        options: analysisOptions
      });
      
      erpData.value = result.data;
      ElMessage.success('时域分析完成');
    }, 'applying');
  } catch (error) {
    console.error('时域分析失败:', error);
    ElMessage.error('时域分析失败');
  }
}

// 加载示例数据
async function loadExampleData() {
  try {
    await withLoading(async () => {
      // 模拟API调用
      const result = await analysisService.getExampleTimeData();
      
      // 设置可用通道和事件
      availableChannels.value = result.channels;
      availableEvents.value = result.events;
      
      // 默认选择一些通道和事件
      selectedChannels.value = availableChannels.value.slice(0, 3).map(ch => ch.id);
      selectedEvents.value = availableEvents.value.slice(0, 2).map(ev => ev.id);
      
      // 设置ERP数据
      erpData.value = result.data;
      
      ElMessage.success('示例数据加载完成');
    }, 'data');
  } catch (error) {
    console.error('加载示例数据失败:', error);
    ElMessage.error('加载示例数据失败');
  }
}

// 生命周期钩子
onMounted(() => {
  loadExampleData();
});
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
                <h3>分析选项</h3>
              </div>
            </template>
            
            <el-form label-position="top">
              <!-- 数据选择 -->
              <el-divider>数据选择</el-divider>
              
              <el-form-item label="选择通道">
                <el-select
                  v-model="selectedChannels"
                  multiple
                  collapse-tags
                  placeholder="选择通道"
                  style="width: 100%"
                >
                  <el-option
                    v-for="channel in availableChannels"
                    :key="channel.id"
                    :label="channel.name"
                    :value="channel.id"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 事件选择 -->
              <el-form-item label="选择事件">
                <el-select
                  v-model="selectedEvents"
                  multiple
                  collapse-tags
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
              
              <!-- 基线校正设置 -->
              <el-divider>基线校正</el-divider>
              
              <el-form-item>
                <el-checkbox v-model="analysisOptions.baseline.enabled">
                  启用基线校正
                </el-checkbox>
              </el-form-item>
              
              <template v-if="analysisOptions.baseline.enabled">
                <el-form-item label="基线时间窗口 (ms)">
                  <el-input-number
                    v-model="analysisOptions.baseline.start"
                    :min="-1000"
                    :max="0"
                    :step="50"
                    style="width: 45%"
                  />
                  <span style="margin: 0 5px;">至</span>
                  <el-input-number
                    v-model="analysisOptions.baseline.end"
                    :min="analysisOptions.baseline.start"
                    :max="500"
                    :step="50"
                    style="width: 45%"
                  />
                </el-form-item>
              </template>
              
              <!-- 平均方式设置 -->
              <el-divider>平均方式</el-divider>
              
              <el-form-item label="平均方法">
                <el-radio-group v-model="analysisOptions.averaging.method">
                  <el-radio label="mean">算术平均</el-radio>
                  <el-radio label="median">中位数平均</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item>
                <el-checkbox v-model="analysisOptions.averaging.removeOutliers">
                  移除离群值
                </el-checkbox>
              </el-form-item>
              
              <template v-if="analysisOptions.averaging.removeOutliers">
                <el-form-item label="离群值阈值 (标准差)">
                  <el-input-number
                    v-model="analysisOptions.averaging.outlierThreshold"
                    :min="1"
                    :max="5"
                    :step="0.5"
                    style="width: 100%"
                  />
                </el-form-item>
              </template>
              
              <!-- 显示设置 -->
              <el-divider>显示设置</el-divider>
              
              <el-form-item label="时间窗口 (ms)">
                <el-input-number
                  v-model="analysisOptions.display.timeWindow[0]"
                  :min="-1000"
                  :max="0"
                  :step="100"
                  style="width: 45%"
                />
                <span style="margin: 0 5px;">至</span>
                <el-input-number
                  v-model="analysisOptions.display.timeWindow[1]"
                  :min="0"
                  :max="2000"
                  :step="100"
                  style="width: 45%"
                />
              </el-form-item>
              
              <el-form-item label="Y轴缩放">
                <el-select
                  v-model="analysisOptions.display.yScale"
                  style="width: 100%"
                >
                  <el-option label="自动" value="auto" />
                  <el-option label="固定" value="fixed" />
                </el-select>
              </el-form-item>
              
              <!-- 操作按钮 -->
              <div class="action-buttons">
                <el-button @click="resetOptions">重置</el-button>
                <el-button 
                  type="primary" 
                  @click="applyAnalysis" 
                  :loading="isLoading.applying"
                >
                  应用分析
                </el-button>
              </div>
            </el-form>
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
                <ERPChart 
                  :data="erpData.erp" 
                  :events="erpData.events"
                  :timeWindow="analysisOptions.display.timeWindow"
                />
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
                <el-empty description="暂无数据" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </AppLayout>
</template>

<style scoped>
.time-analysis-container {
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

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}
</style> 