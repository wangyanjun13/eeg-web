<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/AppLayout.vue';

const route = useRoute();
const router = useRouter();
const datasetId = route.params.datasetId;
const subjectId = route.params.subjectId;

// 数据状态
const subjectInfo = ref(null);
const loading = ref({
  info: false,
  analysis: false
});
const analysisResult = ref(null);

// 分析选项
const analysisOptions = reactive({
  method: 'psd',  // 默认分析方法：功率谱密度
  timeRange: [0, 10],  // 默认时间范围
  channels: [],  // 选择的通道
  bands: ['delta', 'theta', 'alpha', 'beta', 'gamma'],  // 默认频段
  windowSize: 2,  // 窗口大小（秒）
  overlap: 0.5,  // 重叠比例
  normalize: true  // 是否归一化
});

// 获取受试者信息
const fetchSubjectInfo = async () => {
  loading.value.info = true;
  try {
    const response = await datasetService.getSubjectInfo(datasetId, subjectId);
    subjectInfo.value = response.data;
    
    // 默认选择前5个通道
    if (subjectInfo.value && subjectInfo.value.channels) {
      analysisOptions.channels = subjectInfo.value.channels.slice(0, 5);
    }
  } catch (error) {
    console.error('获取受试者信息失败:', error);
    ElMessage.error('获取受试者信息失败');
  } finally {
    loading.value.info = false;
  }
};

// 执行分析
const runAnalysis = async () => {
  loading.value.analysis = true;
  try {
    const response = await datasetService.analyzeEEGData(datasetId, subjectId, {
      method: analysisOptions.method,
      start_time: analysisOptions.timeRange[0],
      duration: analysisOptions.timeRange[1] - analysisOptions.timeRange[0],
      channels: analysisOptions.channels,
      bands: analysisOptions.bands,
      window_size: analysisOptions.windowSize,
      overlap: analysisOptions.overlap,
      normalize: analysisOptions.normalize
    });
    
    analysisResult.value = response.data;
    ElMessage.success('分析完成');
  } catch (error) {
    console.error('分析失败:', error);
    ElMessage.error('分析失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    loading.value.analysis = false;
  }
};

// 重置分析选项
const resetOptions = () => {
  analysisOptions.method = 'psd';
  analysisOptions.timeRange = [0, 10];
  analysisOptions.bands = ['delta', 'theta', 'alpha', 'beta', 'gamma'];
  analysisOptions.windowSize = 2;
  analysisOptions.overlap = 0.5;
  analysisOptions.normalize = true;
  
  // 重置通道选择（选择前5个）
  if (subjectInfo.value && subjectInfo.value.channels) {
    analysisOptions.channels = subjectInfo.value.channels.slice(0, 5);
  } else {
    analysisOptions.channels = [];
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchSubjectInfo();
});
</script>

<template>
  <AppLayout>
    <div class="analyze-container">
      <!-- 返回按钮 -->
      <div class="back-button">
        <el-button @click="router.push(`/datasets/${datasetId}/subjects/${subjectId}`)" icon="ArrowLeft">
          返回受试者详情
        </el-button>
      </div>
      
      <!-- 受试者信息卡片 -->
      <el-card class="subject-info-card" v-loading="loading.info">
        <template #header>
          <div class="card-header">
            <h2>受试者信息</h2>
          </div>
        </template>
        
        <div v-if="subjectInfo">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="数据集ID">{{ datasetId }}</el-descriptions-item>
            <el-descriptions-item label="受试者ID">{{ subjectId }}</el-descriptions-item>
            <el-descriptions-item label="通道数">{{ subjectInfo.channels ? subjectInfo.channels.length : 0 }}</el-descriptions-item>
            <el-descriptions-item label="采样率">{{ subjectInfo.sampling_rate }} Hz</el-descriptions-item>
            <el-descriptions-item label="数据长度">{{ subjectInfo.duration }} 秒</el-descriptions-item>
            <el-descriptions-item label="格式">{{ subjectInfo.format }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <el-skeleton v-else :rows="3" animated />
      </el-card>
      
      <!-- 分析选项卡片 -->
      <el-card class="analysis-options-card">
        <template #header>
          <div class="card-header">
            <h3>分析选项</h3>
            <el-button type="primary" @click="runAnalysis" :loading="loading.analysis">执行分析</el-button>
          </div>
        </template>
        
        <el-form label-position="top">
          <!-- 分析方法选择 -->
          <el-form-item label="分析方法">
            <el-select v-model="analysisOptions.method" style="width: 100%">
              <el-option label="功率谱密度 (PSD)" value="psd" />
              <el-option label="快速傅里叶变换 (FFT)" value="fft" />
              <el-option label="小波分析" value="wavelet" />
              <el-option label="相干性分析" value="coherence" />
            </el-select>
          </el-form-item>
          
          <!-- 时间范围选择 -->
          <el-form-item label="时间范围 (秒)">
            <el-slider
              v-model="analysisOptions.timeRange"
              range
              :min="0"
              :max="subjectInfo ? subjectInfo.duration : 60"
              :step="0.5"
            />
            <div style="display: flex; justify-content: space-between;">
              <span>{{ analysisOptions.timeRange[0] }}s</span>
              <span>{{ analysisOptions.timeRange[1] }}s</span>
            </div>
          </el-form-item>
          
          <!-- 通道选择 -->
          <el-form-item label="选择通道">
            <el-select
              v-model="analysisOptions.channels"
              multiple
              collapse-tags
              style="width: 100%"
            >
              <el-option
                v-for="channel in subjectInfo ? subjectInfo.channels : []"
                :key="channel"
                :label="channel"
                :value="channel"
              />
            </el-select>
          </el-form-item>
          
          <!-- 频段选择 -->
          <el-form-item label="频段">
            <el-checkbox-group v-model="analysisOptions.bands">
              <el-checkbox label="delta">Delta (0.5-4Hz)</el-checkbox>
              <el-checkbox label="theta">Theta (4-8Hz)</el-checkbox>
              <el-checkbox label="alpha">Alpha (8-13Hz)</el-checkbox>
              <el-checkbox label="beta">Beta (13-30Hz)</el-checkbox>
              <el-checkbox label="gamma">Gamma (30-100Hz)</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <!-- 高级选项 -->
          <el-form-item label="高级选项">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="窗口大小 (秒)">
                  <el-input-number v-model="analysisOptions.windowSize" :min="0.5" :max="10" :step="0.5" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="重叠比例">
                  <el-input-number v-model="analysisOptions.overlap" :min="0" :max="0.9" :step="0.1" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-checkbox v-model="analysisOptions.normalize">归一化</el-checkbox>
          </el-form-item>
          
          <!-- 重置按钮 -->
          <el-form-item>
            <el-button @click="resetOptions">重置选项</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <!-- 分析结果卡片 -->
      <el-card class="analysis-result-card" v-loading="loading.analysis" v-if="analysisResult">
        <template #header>
          <div class="card-header">
            <h3>分析结果</h3>
          </div>
        </template>
        
        <div class="result-content">
          <!-- 分析结果信息 -->
          <p>分析方法: {{ analysisOptions.method }}</p>
          <p>时间范围: {{ analysisOptions.timeRange[0] }} - {{ analysisOptions.timeRange[1] }} 秒</p>
          <p>选择通道: {{ analysisOptions.channels.join(', ') }}</p>
          
          <!-- 可视化图表占位符 -->
          <div class="visualization-placeholder">
            <el-empty description="可视化组件将在这里显示" />
          </div>
          
          <!-- 分析结果数据表格 -->
          <div v-if="analysisResult.data">
            <h4>数据表格</h4>
            <el-table :data="analysisResult.data" border style="width: 100%">
              <el-table-column prop="channel" label="通道" />
              <el-table-column prop="band" label="频段" />
              <el-table-column prop="value" label="值" />
            </el-table>
          </div>
        </div>
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.analyze-container {
  padding: 20px; /* 容器内边距 */
}

.back-button {
  margin-bottom: 20px; /* 返回按钮下方间距 */
}

.subject-info-card,
.analysis-options-card,
.analysis-result-card {
  margin-bottom: 20px; /* 卡片下方间距 */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2,
.card-header h3 {
  margin: 0;
}

.visualization-placeholder {
  height: 300px; /* 可视化区域高度 */
  margin: 20px 0;
  border: 1px dashed #ccc;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style> 