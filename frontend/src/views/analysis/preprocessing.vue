<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import analysisService from '@/services/analysisService';
import datasetService from '@/services/dataset';

const route = useRoute();

// 数据状态
const rawData = ref(null);
const processedData = ref(null);
const activeTab = ref('raw'); // 'raw' 或 'processed'
const selectedChannels = ref([]);
const timeRange = ref([0, 10]);
const isLoading = ref({
  rawData: false,
  applying: false
});

// 预处理选项
const preprocessingOptions = reactive({
  filtering: {
    highpass: 0.1,
    lowpass: 40,
    notch: true
  },
  artifacts: {
    method: 'ica',
    autoDetect: true
  }
});

// 在组件挂载时加载数据
onMounted(() => {
  console.log('组件已挂载，路由参数:', route.params);
  loadData();
});

// 直接使用 datasetService 加载数据
async function loadData() {
  try {
    console.log(`尝试加载数据集 ${route.params.datasetId} 受试者 ${route.params.subjectId} 的数据`);
    
    // 设置加载状态
    isLoading.rawData = true;
    
    // 调用API获取数据
    console.log('调用 datasetService.getSubjectData');
    const response = await datasetService.getSubjectData(
      route.params.datasetId,
      route.params.subjectId,
      { start_time: 0, duration: 10 }
    );
    
    console.log('API响应:', response);
    
    if (response.status !== 'success' || !response.data) {
      throw new Error(response.error || '获取数据失败');
    }
    
    console.log('原始数据格式:', JSON.stringify(response.data).substring(0, 500) + '...');
    
    // 修复这里：正确处理返回的数据格式
    const channelData = response.data.data;
    
    if (!channelData || typeof channelData !== 'object') {
      throw new Error('数据格式错误: 未找到通道数据');
    }
    
    // 提取通道名称和对应的数据
    const channels = Object.keys(channelData);
    const sampleRate = response.data.sampleRate || 256; // 默认采样率
    const dataLength = channels.length > 0 ? channelData[channels[0]].length : 0;
    
    // 生成时间点数组
    const times = Array.from({ length: dataLength }, (_, i) => i / sampleRate);
    
    // 构建符合 EEGViewer 期望的数据格式
    rawData.value = {
      data: channelData,
      times: times,
      channels: channels
    };
    
    // 设置时间范围
    timeRange.value = [0, dataLength / sampleRate];
    
    // 更新状态
    isLoading.rawData = false;
    ElMessage.success('数据加载成功');
    
    // 初始化处理后的数据（先使用原始数据）
    processedData.value = rawData.value;
    
    // 选择前5个通道进行显示
    selectedChannels.value = channels.slice(0, 5);
  } catch (error) {
    console.error('加载数据失败:', error);
    ElMessage.error(`加载数据失败: ${error.message || '未知错误'}`);
    isLoading.rawData = false;
  }
}

// 应用预处理
async function applyPreprocessing() {
  const dataset_id = route.params.datasetId;
  const subject_id = route.params.subjectId;
  
  if (!dataset_id || !subject_id) {
    ElMessage.error('无法应用预处理：缺少数据集ID或受试者ID');
    return;
  }
  
  try {
    isLoading.applying = true;
    
    // 构造滤波参数
    const filterParams = {
      low_freq: preprocessingOptions.filtering.highpass,
      high_freq: preprocessingOptions.filtering.lowpass,
      notch: preprocessingOptions.filtering.notch,
      notch_freq: 50.0
    };
    
    console.log('发送滤波请求:', filterParams);
    
    // 调用滤波API
    const response = await analysisService.applyFilter(
      dataset_id,
      subject_id,
      filterParams
    );
    
    console.log('获取到处理后数据:', response);
    
    if (response && response.data) {
      // 确保处理后的数据格式与 EEGViewer 期望的格式一致
      processedData.value = {
        data: response.data.data,
        channels: response.data.channels || Object.keys(response.data.data),
        times: response.data.times || Array.from(
          { length: Object.values(response.data.data)[0]?.length || 0 }, 
          (_, i) => i / (response.data.sampling_rate || 256)
        )
      };
      
      activeTab.value = 'processed';
      ElMessage.success('预处理应用成功');
    } else {
      throw new Error('API返回的数据格式不正确');
    }
  } catch (error) {
    console.error('应用预处理失败:', error);
    ElMessage.error(`应用预处理失败: ${error.message || '未知错误'}`);
  } finally {
    isLoading.applying = false;
  }
}

// 重置选项
function resetOptions() {
  preprocessingOptions.filtering.highpass = 0.1;
  preprocessingOptions.filtering.lowpass = 40;
  preprocessingOptions.filtering.notch = true;
  preprocessingOptions.artifacts.method = 'ica';
  preprocessingOptions.artifacts.autoDetect = true;
  ElMessage.success('已重置预处理选项');
}
</script>

<template>
  <AppLayout>
    <div class="preprocessing-container">
      <h1 class="page-title">数据预处理</h1>
      
      <div class="preprocessing-layout">
        <!-- 左侧：预处理选项 -->
        <div class="preprocessing-options">
          <h2>预处理选项</h2>
          
          <!-- 数据视图切换 -->
          <div class="option-section">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="原始数据" name="raw"></el-tab-pane>
              <el-tab-pane label="预处理后数据" name="processed"></el-tab-pane>
            </el-tabs>
          </div>
          
          <!-- 选择通道 -->
          <div class="option-section">
            <h3>选择通道</h3>
            <el-select
              v-model="selectedChannels"
              multiple
              collapse-tags
              placeholder="选择通道"
              style="width: 100%"
            >
              <el-option
                v-for="channel in rawData?.channels"
                :key="channel"
                :label="channel"
                :value="channel"
              />
            </el-select>
          </div>
          
          <!-- 时间范围 -->
          <div class="option-section">
            <h3>时间范围 (秒)</h3>
            <el-slider
              v-model="timeRange"
              range
              :min="0"
              :max="10"
              :step="0.1"
            />
            <div class="time-range-display">
              {{ timeRange[0].toFixed(1) }}s - {{ timeRange[1].toFixed(1) }}s
            </div>
          </div>
          
          <!-- 滤波设置 -->
          <div class="option-section">
            <h3>滤波设置</h3>
            <div class="filter-option">
              <span>高通滤波 (Hz)</span>
              <el-input-number
                v-model="preprocessingOptions.filtering.highpass"
                :min="0.1"
                :max="30"
                :step="0.1"
                size="small"
              />
            </div>
            
            <div class="filter-option">
              <span>低通滤波 (Hz)</span>
              <el-input-number
                v-model="preprocessingOptions.filtering.lowpass"
                :min="1"
                :max="100"
                :step="1"
                size="small"
              />
            </div>
            
            <div class="filter-option">
              <el-checkbox v-model="preprocessingOptions.filtering.notch">
                应用50Hz陷波滤波器
              </el-checkbox>
            </div>
          </div>
          
          <!-- 去伪迹设置 -->
          <div class="option-section">
            <h3>去伪迹</h3>
            <div class="artifact-option">
              <span>去伪迹方法</span>
              <el-select
                v-model="preprocessingOptions.artifacts.method"
                placeholder="选择方法"
                size="small"
                style="width: 100%"
              >
                <el-option label="独立成分分析 (ICA)" value="ica" />
                <el-option label="阈值检测" value="threshold" />
              </el-select>
            </div>
            
            <div class="artifact-option">
              <el-checkbox v-model="preprocessingOptions.artifacts.autoDetect">
                自动检测伪迹成分
              </el-checkbox>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="option-section">
            <el-button 
              type="primary" 
              @click="applyPreprocessing" 
              :loading="isLoading.applying"
              :disabled="!rawData"
            >
              应用预处理
            </el-button>
            <el-button @click="resetOptions">重置选项</el-button>
          </div>
        </div>
        
        <!-- 右侧：数据可视化 -->
        <div class="preprocessing-visualization">
          <div v-if="isLoading.rawData" class="loading-container">
            <el-skeleton :rows="10" animated />
          </div>
          
          <template v-else>
            <!-- 根据当前选择的标签页显示不同的数据 -->
            <EEGViewer 
              v-if="activeTab === 'raw' && rawData" 
              :data="rawData"
              v-model:selectedChannels="selectedChannels"
              v-model:timeRange="timeRange"
            />
            
            <EEGViewer 
              v-else-if="activeTab === 'processed' && processedData" 
              :data="processedData"
              v-model:selectedChannels="selectedChannels"
              v-model:timeRange="timeRange"
            />
            
            <div v-else class="no-data-message">
              <el-empty description="暂无数据" />
            </div>
          </template>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.preprocessing-container {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  color: #333;
}

.preprocessing-layout {
  display: flex;
  gap: 20px;
}

.preprocessing-options {
  width: 300px;
  flex-shrink: 0;
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
}

.preprocessing-options h2 {
  margin-bottom: 15px;
  font-size: 18px;
  color: #409EFF;
}

.preprocessing-visualization {
  flex-grow: 1;
  background-color: #fff;
  border-radius: 4px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.option-section {
  margin-bottom: 20px;
}

.option-section h3 {
  margin-bottom: 10px;
  font-size: 16px;
  color: #333;
}

.filter-option,
.artifact-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.time-range-display {
  text-align: center;
  margin-top: 5px;
  color: #606266;
}

.loading-container,
.no-data-message {
  padding: 20px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style> 