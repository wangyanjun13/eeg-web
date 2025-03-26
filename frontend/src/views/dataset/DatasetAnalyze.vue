<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import AppLayout from '@/components/AppLayout.vue';
import { useLoading } from '@/composables/useLoading';

const route = useRoute();
const datasetId = ref(route.params.id);
const dataset = ref(null);
const { isLoading: loading, withLoading } = useLoading(true);
const selectedMethod = ref('fft');
const availableMethods = [
  { value: 'fft', label: '快速傅里叶变换 (FFT)' },
  { value: 'wavelet', label: '小波分析' },
  { value: 'psd', label: '功率谱密度' },
  { value: 'coherence', label: '相干性分析' }
];

onMounted(async () => {
  try {
    // 模拟API调用
    await withLoading(new Promise(resolve => {
      setTimeout(() => {
        dataset.value = {
          id: datasetId.value,
          name: '示例数据集 ' + datasetId.value,
          channels: 64,
          sampling_rate: 256
        };
        resolve();
      }, 500);
    }));
  } catch (error) {
    console.error('获取数据集信息失败:', error);
  }
});

function analyzeData() {
  console.log(`使用 ${selectedMethod.value} 方法分析数据集 ${datasetId.value}`);
  // 这里添加实际的分析逻辑
}
</script>

<template>
  <AppLayout>
    <div class="dataset-analyze-container">
      <h1 class="page-title">数据分析</h1>
      
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>
      
      <div v-else-if="dataset" class="analysis-content">
        <div class="dataset-info-panel">
          <h2>{{ dataset.name }}</h2>
          <div class="info-item">
            <span class="label">通道数:</span>
            <span class="value">{{ dataset.channels }}</span>
          </div>
          <div class="info-item">
            <span class="label">采样率:</span>
            <span class="value">{{ dataset.sampling_rate }} Hz</span>
          </div>
        </div>
        
        <div class="analysis-options">
          <h3>分析选项</h3>
          
          <div class="form-group">
            <label for="method">分析方法</label>
            <select id="method" v-model="selectedMethod">
              <option v-for="method in availableMethods" :key="method.value" :value="method.value">
                {{ method.label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>时间范围</label>
            <div class="range-inputs">
              <input type="number" min="0" max="60" step="1" value="0"> <span>至</span>
              <input type="number" min="0" max="60" step="1" value="10"> <span>秒</span>
            </div>
          </div>
          
          <div class="form-group">
            <label>选择通道</label>
            <div class="channel-selection">
              <button class="channel-btn">全部</button>
              <button class="channel-btn">前额叶</button>
              <button class="channel-btn">顶叶</button>
              <button class="channel-btn">枕叶</button>
              <button class="channel-btn">颞叶</button>
            </div>
          </div>
          
          <button class="analyze-button" @click="analyzeData">
            开始分析
          </button>
        </div>
        
        <div class="results-placeholder">
          <p>分析结果将在这里显示</p>
          <p>请先选择分析参数并点击"开始分析"按钮</p>
        </div>
      </div>
      
      <div v-else class="error-state">
        <p>无法找到该数据集，请确认数据集ID是否正确。</p>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.dataset-analyze-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #333;
}

.loading-state, .error-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.analysis-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

@media (min-width: 768px) {
  .analysis-content {
    grid-template-columns: 300px 1fr;
  }
}

.dataset-info-panel {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.dataset-info-panel h2 {
  font-size: 18px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.info-item {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.label {
  color: #666;
  margin-right: 10px;
  min-width: 70px;
}

.value {
  font-weight: 500;
}

.analysis-options {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  grid-column: 1 / -1;
}

.analysis-options h3 {
  font-size: 18px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

select, input {
  width: 100%;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-inputs span {
  color: #666;
}

.channel-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.channel-btn {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f5f7fa;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.channel-btn:hover {
  background-color: #e6f1fc;
  border-color: #409eff;
  color: #409eff;
}

.analyze-button {
  padding: 12px 24px;
  border-radius: 4px;
  background-color: #409eff;
  color: white;
  border: none;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 10px;
  width: 100%;
}

.analyze-button:hover {
  background-color: #66b1ff;
}

.results-placeholder {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  grid-column: 1 / -1;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #888;
}
</style> 