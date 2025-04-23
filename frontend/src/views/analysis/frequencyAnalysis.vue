<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import FrequencyChart from '@/components/analysis/FrequencyChart.vue';
import TimeFrequencyChart from '@/components/analysis/TimeFrequencyChart.vue';
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
    logScale: true,
    colorMap: 'jet', // jet, viridis, plasma
    normalize: false
  }
});

// 当前活动标签页
const activeTab = ref('spectrum');

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
  } catch (error) {
    ElMessage.error('加载受试者信息失败');
    console.error(error);
  }
};

// 运行频域分析
const runFrequencyAnalysis = async () => {
  if (selectedChannels.value.length === 0) {
    ElMessage.warning('请至少选择一个通道');
    return;
  }
  
  try {
    const params = {
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      channels: selectedChannels.value,
      ...analysisOptions
    };
    
    const response = await withLoading(
      analysisService.performFrequencyAnalysis(params),
      'applying'
    );
    
    frequencyData.value = response.data.spectrum;
    timeFrequencyData.value = response.data.timeFrequency;
    ElMessage.success('频域分析完成');
  } catch (error) {
    ElMessage.error('频域分析失败');
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
      analysisService.getExampleFrequencyData(),
      'data'
    );
    frequencyData.value = response.data.spectrum;
    timeFrequencyData.value = response.data.timeFrequency;
    ElMessage.success('加载示例数据成功');
  } catch (error) {
    ElMessage.error('加载示例数据失败');
    console.error(error);
  }
};

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}

onMounted(() => {
  loadSubjectInfo();
});
</script>

<template>
  <div class="frequency-analysis-container">
    <!-- 控制面板 -->
    <el-card class="control-panel">
      <template #header>
        <div class="card-header">
          <h3>频域分析设置</h3>
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
        
        <!-- 分析类型标签页 -->
        <el-tabs v-model="activeTab" class="analysis-tabs">
          <!-- 频谱分析标签页 -->
          <el-tab-pane label="频谱分析" name="spectrum">
            <el-form-item label="分析方法">
              <el-select v-model="analysisOptions.spectrum.method">
                <el-option label="快速傅里叶变换 (FFT)" value="fft" />
                <el-option label="Welch方法" value="welch" />
                <el-option label="多窗谱估计" value="multitaper" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="窗口大小">
              <el-input-number 
                v-model="analysisOptions.spectrum.windowSize" 
                :min="0.5" 
                :max="10" 
                :step="0.5"
              />
              <span class="unit">秒</span>
            </el-form-item>
            
            <el-form-item label="重叠率">
              <el-slider 
                v-model="analysisOptions.spectrum.overlap" 
                :min="0" 
                :max="90" 
                :step="10"
              />
              <span class="value-display">{{ analysisOptions.spectrum.overlap }}%</span>
            </el-form-item>
            
            <el-form-item label="窗函数">
              <el-select v-model="analysisOptions.spectrum.windowFunction">
                <el-option label="Hann窗" value="hann" />
                <el-option label="Hamming窗" value="hamming" />
                <el-option label="Blackman窗" value="blackman" />
              </el-select>
            </el-form-item>
          </el-tab-pane>
          
          <!-- 时频分析标签页 -->
          <el-tab-pane label="时频分析" name="timeFrequency">
            <el-form-item label="分析方法">
              <el-select v-model="analysisOptions.timeFrequency.method">
                <el-option label="短时傅里叶变换 (STFT)" value="stft" />
                <el-option label="小波变换" value="wavelet" />
                <el-option label="希尔伯特变换" value="hilbert" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="窗口大小">
              <el-input-number 
                v-model="analysisOptions.timeFrequency.windowSize" 
                :min="0.1" 
                :max="2" 
                :step="0.1"
              />
              <span class="unit">秒</span>
            </el-form-item>
            
            <el-form-item label="步长">
              <el-input-number 
                v-model="analysisOptions.timeFrequency.stepSize" 
                :min="0.01" 
                :max="0.5" 
                :step="0.01"
              />
              <span class="unit">秒</span>
            </el-form-item>
            
            <el-form-item label="频率范围">
              <el-slider 
                v-model="analysisOptions.timeFrequency.freqRange" 
                range 
                :min="0" 
                :max="100" 
                :step="1"
              />
              <span class="value-display">
                {{ analysisOptions.timeFrequency.freqRange[0] }} - 
                {{ analysisOptions.timeFrequency.freqRange[1] }} Hz
              </span>
            </el-form-item>
          </el-tab-pane>
          
          <!-- 频带设置标签页 -->
          <el-tab-pane label="频带设置" name="bands">
            <el-form-item label="Delta (δ)">
              <el-slider 
                v-model="analysisOptions.bands.delta" 
                range 
                :min="0.5" 
                :max="8" 
                :step="0.5"
              />
              <span class="value-display">
                {{ analysisOptions.bands.delta[0] }} - 
                {{ analysisOptions.bands.delta[1] }} Hz
              </span>
            </el-form-item>
            
            <el-form-item label="Theta (θ)">
              <el-slider 
                v-model="analysisOptions.bands.theta" 
                range 
                :min="3" 
                :max="10" 
                :step="0.5"
              />
              <span class="value-display">
                {{ analysisOptions.bands.theta[0] }} - 
                {{ analysisOptions.bands.theta[1] }} Hz
              </span>
            </el-form-item>
            
            <el-form-item label="Alpha (α)">
              <el-slider 
                v-model="analysisOptions.bands.alpha" 
                range 
                :min="7" 
                :max="15" 
                :step="0.5"
              />
              <span class="value-display">
                {{ analysisOptions.bands.alpha[0] }} - 
                {{ analysisOptions.bands.alpha[1] }} Hz
              </span>
            </el-form-item>
            
            <el-form-item label="Beta (β)">
              <el-slider 
                v-model="analysisOptions.bands.beta" 
                range 
                :min="12" 
                :max="35" 
                :step="0.5"
              />
              <span class="value-display">
                {{ analysisOptions.bands.beta[0] }} - 
                {{ analysisOptions.bands.beta[1] }} Hz
              </span>
            </el-form-item>
            
            <el-form-item label="Gamma (γ)">
              <el-slider 
                v-model="analysisOptions.bands.gamma" 
                range 
                :min="25" 
                :max="100" 
                :step="1"
              />
              <span class="value-display">
                {{ analysisOptions.bands.gamma[0] }} - 
                {{ analysisOptions.bands.gamma[1] }} Hz
              </span>
            </el-form-item>
          </el-tab-pane>
          
          <!-- 显示设置标签页 -->
          <el-tab-pane label="显示设置" name="display">
            <el-form-item label="对数刻度">
              <el-switch v-model="analysisOptions.display.logScale" />
            </el-form-item>
            
            <el-form-item label="颜色映射">
              <el-select v-model="analysisOptions.display.colorMap">
                <el-option label="Jet" value="jet" />
                <el-option label="Viridis" value="viridis" />
                <el-option label="Plasma" value="plasma" />
                <el-option label="Inferno" value="inferno" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="归一化">
              <el-switch v-model="analysisOptions.display.normalize" />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      
      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button @click="resetForm">重置</el-button>
        <el-button type="primary" @click="runFrequencyAnalysis" :loading="isLoading.applying">
          运行分析
        </el-button>
        <el-button @click="loadExampleData" :loading="isLoading.data">
          加载示例数据
        </el-button>
        <el-button type="success" @click="goToNextStep">下一步</el-button>
      </div>
    </el-card>
    
    <!-- 数据显示 -->
    <template v-if="frequencyData || timeFrequencyData">
      <!-- 频谱分析结果 -->
      <el-card v-if="frequencyData" class="data-display">
        <template #header>
          <div class="card-header">
            <h3>频谱分析结果</h3>
          </div>
        </template>
        
        <FrequencyChart 
          :data="frequencyData" 
          :logScale="analysisOptions.display.logScale"
        />
        
        <!-- 频带功率图表 -->
        <div class="band-power-charts">
          <div v-for="(band, name) in analysisOptions.bands" :key="name" class="band-chart">
            <h4>{{ name.charAt(0).toUpperCase() + name.slice(1) }} 频带 ({{ band[0] }}-{{ band[1] }} Hz)</h4>
            <FrequencyChart 
              v-if="frequencyData"
              :data="{
                ...frequencyData,
                frequencies: frequencyData.frequencies.filter(f => f >= band[0] && f <= band[1]),
                powers: frequencyData.channels.map(ch => ({
                  name: ch,
                  values: frequencyData.powers[ch].filter((_, i) => 
                    frequencyData.frequencies[i] >= band[0] && 
                    frequencyData.frequencies[i] <= band[1]
                  )
                }))
              }"
              :logScale="analysisOptions.display.logScale"
              :title="`${name} 频带功率`"
            />
          </div>
        </div>
      </el-card>
      
      <!-- 时频分析结果 -->
      <el-card v-if="timeFrequencyData" class="data-display">
        <template #header>
          <div class="card-header">
            <h3>时频分析结果</h3>
          </div>
        </template>
        
        <TimeFrequencyChart 
          :data="timeFrequencyData"
          :colorMap="analysisOptions.display.colorMap"
        />
      </el-card>
    </template>
    
    <div v-else class="no-data">
      <el-empty description="暂无分析数据，请运行分析或加载示例数据" />
    </div>
    
    <!-- 分析流程导航 -->
    <AnalysisWorkflow 
      ref="workflowRef"
      current-step="frequency" 
      :dataset-id="datasetId" 
      :subject-id="subjectId" 
    />
  </div>
  
  <!-- 通道选择对话框 -->
  <component :is="renderChannelSelectDialog()" />
</template>

<style scoped>
.frequency-analysis-container {
  padding: 20px;
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

.unit {
  margin-left: 8px;
}

.value-display {
  margin-left: 8px;
  color: #606266;
  font-size: 12px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 10px;
}

.data-display {
  margin-top: 20px;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  margin-top: 20px;
}

.band-power-charts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 30px;
}

.band-chart h4 {
  margin: 10px 0;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
}
</style> 