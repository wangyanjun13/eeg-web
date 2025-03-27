<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
import FrequencyChart from '@/components/analysis/FrequencyChart.vue';
import TimeFrequencyChart from '@/components/analysis/TimeFrequencyChart.vue';
import { useLoading } from '@/composables/useLoading';
import { useFormState } from '@/composables/useFormState';
import analysisService from '@/services/analysisService';

const route = useRoute();
const router = useRouter();

// 数据状态
const frequencyData = ref(null);
const timeFrequencyData = ref(null);
const availableChannels = ref([]);
const selectedChannels = ref([]);

// 加载状态
const { isLoading, withLoading } = useLoading({
  data: false,
  applying: false
});

// 分析表单
const { formState: analysisOptions, resetForm } = useFormState('frequency-analysis-options', {
  // 频谱分析设置
  spectrum: {
    method: 'fft', // fft, welch, multitaper
    windowSize: 2, // 秒
    overlap: 50, // 百分比
    windowFunction: 'hann' // hann, hamming, blackman
  },
  // 时频分析设置
  timeFrequency: {
    method: 'stft', // stft, wavelet, hilbert
    windowSize: 0.5, // 秒
    stepSize: 0.1, // 秒
    freqRange: [1, 40] // Hz
  },
  // 频带设置
  bands: {
    delta: [1, 4],
    theta: [4, 8],
    alpha: [8, 13],
    beta: [13, 30],
    gamma: [30, 45]
  },
  // 显示设置
  display: {
    logScale: false,
    colorMap: 'jet' // jet, viridis, plasma, inferno
  }
});

// 当前活动标签页
const activeTab = ref('spectrum');

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
      const result = await analysisService.performFrequencyAnalysis({
        channels: selectedChannels.value,
        options: analysisOptions
      });
      
      frequencyData.value = result.frequencyData;
      timeFrequencyData.value = result.timeFrequencyData;
      ElMessage.success('频域分析完成');
    }, 'applying');
  } catch (error) {
    console.error('频域分析失败:', error);
    ElMessage.error('频域分析失败');
  }
}

// 加载示例数据
async function loadExampleData() {
  try {
    await withLoading(async () => {
      // 模拟API调用
      const result = await analysisService.getExampleFrequencyData();
      
      // 设置可用通道
      availableChannels.value = result.channels;
      
      // 默认选择一些通道
      selectedChannels.value = availableChannels.value.slice(0, 3).map(ch => ch.id);
      
      // 设置频谱和时频数据
      frequencyData.value = result.frequencyData;
      timeFrequencyData.value = result.timeFrequencyData;
      
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
    <div class="frequency-analysis-container">
      <h2>频域分析</h2>
      
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
              
              <!-- 频谱分析设置 -->
              <el-divider>频谱分析设置</el-divider>
              
              <el-form-item label="分析方法">
                <el-select
                  v-model="analysisOptions.spectrum.method"
                  style="width: 100%"
                >
                  <el-option label="快速傅里叶变换 (FFT)" value="fft" />
                  <el-option label="Welch方法" value="welch" />
                  <el-option label="多窗口谱估计" value="multitaper" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="窗口大小 (秒)">
                <el-input-number
                  v-model="analysisOptions.spectrum.windowSize"
                  :min="0.5"
                  :max="10"
                  :step="0.5"
                  style="width: 100%"
                />
              </el-form-item>
              
              <el-form-item v-if="analysisOptions.spectrum.method === 'welch'" label="重叠率 (%)">
                <el-input-number
                  v-model="analysisOptions.spectrum.overlap"
                  :min="0"
                  :max="90"
                  :step="10"
                  style="width: 100%"
                />
              </el-form-item>
              
              <el-form-item label="窗函数">
                <el-select
                  v-model="analysisOptions.spectrum.windowFunction"
                  style="width: 100%"
                >
                  <el-option label="Hann窗" value="hann" />
                  <el-option label="Hamming窗" value="hamming" />
                  <el-option label="Blackman窗" value="blackman" />
                </el-select>
              </el-form-item>
              
              <!-- 时频分析设置 -->
              <el-divider>时频分析设置</el-divider>
              
              <el-form-item label="分析方法">
                <el-select
                  v-model="analysisOptions.timeFrequency.method"
                  style="width: 100%"
                >
                  <el-option label="短时傅里叶变换 (STFT)" value="stft" />
                  <el-option label="小波变换" value="wavelet" />
                  <el-option label="希尔伯特变换" value="hilbert" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="窗口大小 (秒)">
                <el-input-number
                  v-model="analysisOptions.timeFrequency.windowSize"
                  :min="0.1"
                  :max="2"
                  :step="0.1"
                  style="width: 100%"
                />
              </el-form-item>
              
              <el-form-item label="步长 (秒)">
                <el-input-number
                  v-model="analysisOptions.timeFrequency.stepSize"
                  :min="0.01"
                  :max="0.5"
                  :step="0.01"
                  style="width: 100%"
                />
              </el-form-item>
              
              <el-form-item label="频率范围 (Hz)">
                <el-input-number
                  v-model="analysisOptions.timeFrequency.freqRange[0]"
                  :min="0.1"
                  :max="20"
                  :step="0.5"
                  style="width: 45%"
                />
                <span style="margin: 0 5px;">至</span>
                <el-input-number
                  v-model="analysisOptions.timeFrequency.freqRange[1]"
                  :min="analysisOptions.timeFrequency.freqRange[0]"
                  :max="100"
                  :step="1"
                  style="width: 45%"
                />
              </el-form-item>
              
              <!-- 显示设置 -->
              <el-divider>显示设置</el-divider>
              
              <el-form-item>
                <el-checkbox v-model="analysisOptions.display.logScale">
                  使用对数刻度
                </el-checkbox>
              </el-form-item>
              
              <el-form-item label="颜色映射">
                <el-select
                  v-model="analysisOptions.display.colorMap"
                  style="width: 100%"
                >
                  <el-option label="Jet" value="jet" />
                  <el-option label="Viridis" value="viridis" />
                  <el-option label="Plasma" value="plasma" />
                  <el-option label="Inferno" value="inferno" />
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
                  <el-tab-pane label="频谱分析" name="spectrum" />
                  <el-tab-pane label="时频分析" name="time-frequency" />
                  <el-tab-pane label="频带功率" name="band-power" />
                </el-tabs>
              </div>
            </template>
            
            <div v-loading="isLoading.data">
              <!-- 频谱分析 -->
              <div v-if="activeTab === 'spectrum' && frequencyData">
                <FrequencyChart 
                  :data="frequencyData" 
                  :logScale="analysisOptions.display.logScale"
                />
              </div>
              
              <!-- 时频分析 -->
              <div v-else-if="activeTab === 'time-frequency' && timeFrequencyData">
                <TimeFrequencyChart 
                  :data="timeFrequencyData" 
                  :colorMap="analysisOptions.display.colorMap"
                />
              </div>
              
              <!-- 频带功率 -->
              <div v-else-if="activeTab === 'band-power' && frequencyData">
                <div class="band-power-charts">
                  <div v-for="(band, name) in analysisOptions.bands" :key="name" class="band-chart">
                    <h4>{{ name.charAt(0).toUpperCase() + name.slice(1) }} ({{ band[0] }}-{{ band[1] }} Hz)</h4>
                    <FrequencyChart 
                      :data="frequencyData" 
                      :logScale="analysisOptions.display.logScale"
                      :freqRange="band"
                    />
                  </div>
                </div>
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
.frequency-analysis-container {
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

.band-power-charts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.band-chart h4 {
  margin: 10px 0;
  text-align: center;
}
</style> 