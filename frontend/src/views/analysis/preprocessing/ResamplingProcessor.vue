<script setup>
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as echarts from 'echarts';
import analysisService from '@/services/analysisService';
import { useLoading } from '@/composables/useLoading';

const props = defineProps({
  preprocessParams: {
    type: Object,
    required: true
  },
  datasetId: {
    type: String,
    required: true
  },
  subjectId: {
    type: String,
    required: true
  },
  originalData: {
    type: Object,
    default: null
  },
  processingChannels: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['process-complete']);

const { isLoading, withLoading } = useLoading({
  processing: false
});

// 重采样效果可视化
const showResampleEffects = ref(false);
const resampleEffectsRef = ref(null);
let resampleEffectsChart = null;

// 添加已应用重采样状态
const hasAppliedResampling = ref(false);
const appliedSamplingRate = ref(0);

// 计算当前采样率和数据大小
const currentSamplingRate = computed(() => {
  return props.originalData?.sampling_rate || 0;
});

const currentDataPoints = computed(() => {
  if (!props.originalData || !props.originalData.data) return 0;
  // 获取第一个通道的数据长度作为示例
  const firstChannel = Object.keys(props.originalData.data)[0];
  return props.originalData.data[firstChannel]?.length || 0;
});

// 计算重采样后的数据点数
const resampledDataPoints = computed(() => {
  if (!currentDataPoints.value || !currentSamplingRate.value || !props.preprocessParams.resample.resample_freq) {
    return 0;
  }
  // 按比例计算
  return Math.round(currentDataPoints.value * (props.preprocessParams.resample.resample_freq / currentSamplingRate.value));
});

// 应用重采样
const applyResampling = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载数据');
    return;
  }

  try {
    // 参数验证
    if (props.preprocessParams.resample.resample && 
        (props.preprocessParams.resample.resample_freq <= 0)) {
      throw new Error('重采样频率必须大于0Hz');
    }
    
    // 检查重采样率是否与当前采样率几乎相同
    if (Math.abs(props.preprocessParams.resample.resample_freq - currentSamplingRate.value) < 0.01) {
      ElMessage.info(`目标采样率 (${props.preprocessParams.resample.resample_freq.toFixed(2)}Hz) 与当前采样率 (${currentSamplingRate.value.toFixed(2)}Hz) 几乎相同，无需重采样`);
      
      // 直接使用当前数据作为结果
      emit('process-complete', props.originalData);
      return;
    }
    
    // 检查是否降采样过度 - 添加有意义的警告
    const ratio = props.preprocessParams.resample.resample_freq / currentSamplingRate.value;
    if (ratio < 0.25) { // 如果降采样率低于原采样率的1/4
      try {
        await ElMessageBox.confirm(
          `您将把采样率从${currentSamplingRate.value}Hz降低到${props.preprocessParams.resample.resample_freq}Hz，` +
          `这将显著减少数据点数量(${ratio.toFixed(2)}倍)。` +
          `\n\n过度降低采样率可能导致频率在${props.preprocessParams.resample.resample_freq/2}Hz以上的信号特征丢失。确定要继续吗？`,
          '降采样警告',
          { confirmButtonText: '继续', cancelButtonText: '取消', type: 'warning' }
        );
      } catch (e) {
        // 用户取消操作
        return;
      }
    }
    
    // 验证处理通道不为空
    if (!props.processingChannels || props.processingChannels.length === 0) {
      throw new Error('请至少选择一个通道进行处理');
    }

    console.log('【重要调试】重采样请求参数:', {
      原始采样率: currentSamplingRate.value,
      目标采样率: props.preprocessParams.resample.resample_freq,
      通道: props.processingChannels,
      数据点数: currentDataPoints.value
    });

    // 显示提示正在处理
    const loadingMessage = ElMessage({
      type: 'info',
      message: '正在应用重采样处理，这可能需要几秒钟...',
      duration: 0
    });

    const response = await withLoading(
      analysisService.applyResample(props.datasetId, props.subjectId, {
        resample: props.preprocessParams.resample.resample,
        resample_freq: props.preprocessParams.resample.resample_freq,
        channels: props.processingChannels,
        force_refresh: { timestamp: new Date().getTime() }
      }),
      'processing'
    );

    // 关闭加载提示
    loadingMessage.close();

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }
    
    // 记录重采样已应用状态
    hasAppliedResampling.value = true;
    appliedSamplingRate.value = response.data.sampling_rate;
    
    // 记录重采样前后的对比信息
    const originalRate = currentSamplingRate.value;
    const newRate = response.data.sampling_rate;
    
    // 发送处理完成事件
    emit('process-complete', response.data);
    
    // 添加更有意义的成功消息
    ElMessage.success(
      `重采样成功: 采样率从 ${originalRate}Hz 变更为 ${newRate}Hz，` +
      `数据点数量变化: ${currentDataPoints.value} → ${response.data.times.length}`
    );
  } catch (error) {
    console.error('应用重采样失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用重采样失败: ${errorMessage}`);
  }
};

// 初始化重采样效果图表
const initResampleEffectsChart = () => {
  if (resampleEffectsChart) resampleEffectsChart.dispose();
  if (!resampleEffectsRef.value) return;
  
  resampleEffectsChart = echarts.init(resampleEffectsRef.value);
  updateResampleEffectsChart();
  
  window.addEventListener('resize', () => resampleEffectsChart?.resize());
};

// 更新重采样效果图表
const updateResampleEffectsChart = () => {
  if (!resampleEffectsChart || !showResampleEffects.value) return;
  
  // 原始Nyquist频率和目标Nyquist频率
  const originalNyquist = currentSamplingRate.value / 2;
  const targetNyquist = props.preprocessParams.resample.resample_freq / 2;
  
  const option = {
    title: {
      text: '重采样效果示意',
      textStyle: {
        fontSize: 14
      },
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return `频率: ${params[0].value[0].toFixed(1)} Hz<br/>
                原始: ${params[0].value[1].toFixed(2)}<br/>
                重采样后: ${params[1] ? params[1].value[1].toFixed(2) : '0'}`;
      }
    },
    legend: {
      data: ['原始信号', '重采样后信号'],
      bottom: 10
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '25%'
    },
    xAxis: {
      type: 'value',
      name: '频率 (Hz)',
      nameLocation: 'middle',
      nameGap: 25,
      max: Math.max(originalNyquist * 1.2, targetNyquist * 1.2)
    },
    yAxis: {
      type: 'value',
      name: '幅度',
      nameLocation: 'middle',
      nameGap: 30,
      nameRotate: 90,
      min: 0,
      max: 1.05
    },
    series: [
      {
        name: '原始信号',
        type: 'line',
        data: generateSpectrumData(currentSamplingRate.value, originalNyquist),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2 },
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '重采样后信号',
        type: 'line',
        data: generateSpectrumData(props.preprocessParams.resample.resample_freq, targetNyquist),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, type: 'dashed' },
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '原始Nyquist频率',
        type: 'line',
        markLine: {
          symbol: 'none',
          label: { formatter: `原始Nyquist: ${originalNyquist.toFixed(1)}Hz` },
          lineStyle: { color: '#409EFF', type: 'dashed' },
          data: [{ xAxis: originalNyquist }]
        }
      },
      {
        name: '目标Nyquist频率',
        type: 'line',
        markLine: {
          symbol: 'none',
          label: { formatter: `目标Nyquist: ${targetNyquist.toFixed(1)}Hz` },
          lineStyle: { color: '#67C23A', type: 'dashed' },
          data: [{ xAxis: targetNyquist }]
        }
      }
    ]
  };
  
  resampleEffectsChart.setOption(option);
};

// 生成频谱数据模拟
const generateSpectrumData = (samplingRate, nyquist) => {
  const points = 100;
  const data = [];
  
  for (let i = 0; i <= points; i++) {
    const freq = (i / points) * nyquist * 1.5; // 超出Nyquist频率一点以展示截止效果
    let amp = 1.0;
    
    // 在Nyquist频率附近进行衰减模拟
    if (freq > nyquist * 0.8) {
      amp *= Math.max(0, 1 - Math.pow((freq - nyquist * 0.8) / (nyquist * 0.2), 2));
    }
    
    // 在Nyquist频率后迅速衰减为0
    if (freq > nyquist) {
      amp = Math.max(0, amp * (1 - Math.pow((freq - nyquist) / 5, 2)));
    }
    
    data.push([freq, amp]);
  }
  
  return data;
};

// 监听是否显示重采样效果
watch(showResampleEffects, (newValue) => {
  if (newValue) {
    nextTick(() => {
      initResampleEffectsChart();
    });
  }
});

// 监听重采样参数变化
watch(() => [
  props.preprocessParams.resample.resample_freq,
  props.originalData?.sampling_rate
], () => {
  if (showResampleEffects.value) {
    nextTick(updateResampleEffectsChart);
  }
}, { deep: true });

// 组件挂载完成
onMounted(() => {
  if (showResampleEffects.value) {
    nextTick(initResampleEffectsChart);
  }
});

// 组件卸载前清理
onBeforeUnmount(() => {
  if (resampleEffectsChart) {
    resampleEffectsChart.dispose();
    resampleEffectsChart = null;
  }
  window.removeEventListener('resize', () => resampleEffectsChart?.resize());
});
</script>

<template>
  <div class="resample-processor">
    <h3>重采样设置</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <el-form-item label="启用重采样">
        <el-switch v-model="preprocessParams.resample.resample" />
      </el-form-item>
      
      <template v-if="preprocessParams.resample.resample">
        <el-form-item label="目标采样率">
          <div class="sampling-rate-input">
            <el-input-number 
              v-model="preprocessParams.resample.resample_freq" 
              :min="50" 
              :max="2000" 
              :step="10"
              size="small"
              class="small-input"
            />
            <span class="unit">Hz</span>
          </div>
        </el-form-item>
        
        <div class="info-panel" v-if="originalData">
          <div class="info-row">
            <div class="info-label">当前采样率:</div>
            <div class="info-value">
              {{ currentSamplingRate.toFixed(1) }} Hz
              <el-tag v-if="hasAppliedResampling" size="mini" type="success">已重采样</el-tag>
            </div>
          </div>
          <div class="info-row">
            <div class="info-label">目标采样率:</div>
            <div class="info-label">重采样后:</div>
            <div class="info-value">{{ preprocessParams.resample.resample_freq.toFixed(1) }} Hz</div>
          </div>
          <div class="info-row">
            <div class="info-label">数据点数变化:</div>
            <div class="info-value">{{ currentDataPoints }} → {{ resampledDataPoints }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">Nyquist频率:</div>
            <div class="info-value">{{ (currentSamplingRate/2).toFixed(1) }} → {{ (preprocessParams.resample.resample_freq/2).toFixed(1) }} Hz</div>
          </div>
        </div>
        
        <el-form-item label="显示效果">
          <el-switch v-model="showResampleEffects" />
        </el-form-item>
        
        <div v-if="showResampleEffects" class="effect-chart-container">
          <div ref="resampleEffectsRef" class="effect-chart"></div>
          <div class="effect-explanation">
            <p>图表展示了重采样对信号频谱的影响</p>
            <p>Nyquist频率 = 采样率/2，是可恢复的最高频率</p>
          </div>
        </div>
      </template>
      
      <el-form-item class="action-item">
        <el-button 
          type="primary" 
          @click="applyResampling" 
          :loading="isLoading.processing"
          :disabled="!originalData || !preprocessParams.resample.resample"
          size="small"
        >
          应用重采样
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.resample-processor {
  padding: 10px;
  max-width: 250px;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.sampling-rate-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.small-input {
  width: 90px;
}

.unit {
  color: #606266;
  font-size: 12px;
}

.info-panel {
  margin: 10px 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.info-label {
  color: #606266;
}

.info-value {
  font-weight: 500;
  color: #303133;
}

.effect-chart-container {
  margin-top: 10px;
  margin-bottom: 15px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  padding: 10px;
}

.effect-chart {
  height: 180px;
  width: 100%;
}

.effect-explanation {
  margin-top: 8px;
  padding-top: 5px;
  border-top: 1px dashed #EBEEF5;
  font-size: 12px;
  color: #909399;
}

.effect-explanation p {
  margin: 3px 0;
}

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}
</style> 