<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
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
import AppLayout from '@/components/layout/AppLayout.vue';

const route = useRoute();
const router = useRouter();
const datasetId = computed(() => route.params.datasetId);
const subjectId = computed(() => route.params.subjectId);

// 数据状态
const frequencyData = ref(null);
const timeFrequencyData = ref(null);
const availableChannels = ref([]);
const selectedChannels = ref([]);
const preprocessedDataAvailable = ref(false);
const preprocessedData = ref(null);

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

// 确保表单状态中的所有必要字段都存在
watch(analysisOptions, () => {
  // 确保 spectrum 字段存在
  if (!analysisOptions.spectrum) {
    analysisOptions.spectrum = {
      method: 'fft',
      windowSize: 2,
      overlap: 50,
      windowFunction: 'hann'
    };
  }
  
  // 确保 timeFrequency 字段存在
  if (!analysisOptions.timeFrequency) {
    analysisOptions.timeFrequency = {
      method: 'stft',
      windowSize: 0.5,
      stepSize: 0.1,
      freqRange: [1, 40]
    };
  } else if (!analysisOptions.timeFrequency.freqRange) {
    analysisOptions.timeFrequency.freqRange = [1, 40];
  }
  
  // 确保 bands 字段存在
  if (!analysisOptions.bands) {
    analysisOptions.bands = {
      delta: [1, 4],
      theta: [4, 8],
      alpha: [8, 13],
      beta: [13, 30],
      gamma: [30, 45]
    };
  }
  
  // 确保 display 字段存在
  if (!analysisOptions.display) {
    analysisOptions.display = {
      logScale: true,
      colorMap: 'jet',
      normalize: false
    };
  }
}, { deep: true, immediate: true });

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

// 加载预处理数据
const loadPreprocessedData = () => {
  try {
    const preprocessedDataStr = localStorage.getItem('preprocessed_data');
    if (!preprocessedDataStr) {
      return false;
    }
    
    const parsedData = JSON.parse(preprocessedDataStr);
    
    // 检查数据是否匹配当前的数据集和受试者
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
    
    // 保存预处理数据到状态中
    preprocessedData.value = parsedData;
    preprocessedDataAvailable.value = true;
    
    // 更新可用通道和选择的通道
    if (parsedData.data && parsedData.data.channels) {
      availableChannels.value = parsedData.data.channels;
      // 选择所有预处理后的通道，因为这些是用户已经筛选过的
      selectedChannels.value = [...parsedData.data.channels];
      ElMessage.info('已加载预处理后的数据');
      return true;
    }
    
    return false;
  } catch (e) {
    console.warn('读取预处理数据失败', e);
    return false;
  }
};

// 运行频域分析
const runFrequencyAnalysis = async () => {
  if (selectedChannels.value.length === 0) {
    ElMessage.warning('请至少选择一个通道');
    return;
  }
  
  try {
    // 确保所有必要的配置存在
    if (!analysisOptions.spectrum) {
      analysisOptions.spectrum = {
        method: 'fft',
        windowSize: 2,
        overlap: 50,
        windowFunction: 'hann'
      };
    }
    
    if (!analysisOptions.timeFrequency) {
      analysisOptions.timeFrequency = {
        method: 'stft',
        windowSize: 0.5,
        stepSize: 0.1,
        freqRange: [1, 40]
      };
    } else if (!analysisOptions.timeFrequency.freqRange) {
      analysisOptions.timeFrequency.freqRange = [1, 40];
    }
    
    if (!analysisOptions.bands) {
      analysisOptions.bands = {
        delta: [1, 4],
        theta: [4, 8],
        alpha: [8, 13],
        beta: [13, 30],
        gamma: [30, 45]
      };
    }
    
    if (!analysisOptions.display) {
      analysisOptions.display = {
        logScale: true,
        colorMap: 'jet',
        normalize: false
      };
    }
    
    // 确保频率范围符合后端预期格式
    const freqRange = analysisOptions.timeFrequency.freqRange;
    const freqs = [];
    for (let f = freqRange[0]; f <= freqRange[1]; f += 1) {
      freqs.push(f);
    }
    
    // 构建符合后端预期的请求参数
    const params = {
      freqs: freqs, // 必须是频率数组，不是范围
      n_cycles: 7, // 默认值
      method: analysisOptions.timeFrequency.method,
      channels: selectedChannels.value,
      // 前端配置参数 - 用于计算和显示
      spectrum: {
        ...analysisOptions.spectrum
      },
      timeFrequency: {
        ...analysisOptions.timeFrequency
      },
      bands: analysisOptions.bands,
      display: analysisOptions.display
    };
    
    // 如果有预处理数据，添加到请求参数中
    if (preprocessedDataAvailable.value && preprocessedData.value) {
      params.use_preprocessed_data = true;
      
      // 确保我们只提供必要的数据字段，避免数据过大
      const necessaryData = {
        data: preprocessedData.value.data.data || {},
        channels: preprocessedData.value.data.channels || [],
        sampling_rate: preprocessedData.value.data.sampling_rate,
        timeRange: preprocessedData.value.data.timeRange,
        events: preprocessedData.value.data.events || []
      };
      
      params.preprocessed_data = necessaryData;
    }
    
    console.log('发送频域分析请求:', {
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      params: {
        freqsLength: params.freqs.length,
        method: params.method,
        usePreprocessedData: params.use_preprocessed_data || false,
        channelsCount: params.channels.length,
        freqRange: [params.freqs[0], params.freqs[params.freqs.length - 1]]
      }
    });
    
    ElMessage.info('正在执行频域分析，请稍候...');
    
    const response = await withLoading(
      analysisService.performFrequencyAnalysis(datasetId.value, subjectId.value, params),
      'applying'
    );
    
    if (response && response.data) {
      console.log('频域分析返回数据格式:', {
        hasSpectrum: !!response.data.spectrum,
        hasTimeFrequency: !!response.data.timeFrequency,
        timeFreqDataType: typeof response.data.timeFrequency,
        hasTimes: response.data.timeFrequency?.times ? 'yes' : 'no',
        hasFrequencies: response.data.timeFrequency?.frequencies ? 'yes' : 'no',
        hasPower: response.data.timeFrequency?.power ? 'yes' : 'no',
        powerType: typeof response.data.timeFrequency?.power,
        powerIsArray: Array.isArray(response.data.timeFrequency?.power),
        powerLength: Array.isArray(response.data.timeFrequency?.power) ? response.data.timeFrequency.power.length : 0
      });
      
      // 处理频谱数据
      if (response.data.spectrum) {
        frequencyData.value = response.data.spectrum;
        
        // 检查并修复频谱数据结构
        if (frequencyData.value) {
          // 确保powers字段存在
          if (!frequencyData.value.powers && frequencyData.value.data) {
            console.log('修复频谱数据：将data字段复制到powers字段');
            frequencyData.value.powers = frequencyData.value.data;
          }
          
          // 确保channels字段存在
          if (!frequencyData.value.channels || !Array.isArray(frequencyData.value.channels)) {
            console.log('修复频谱数据：使用选中的通道作为channels字段');
            frequencyData.value.channels = [...selectedChannels.value];
          }
          
          // 确保frequencies字段存在
          if (!frequencyData.value.frequencies || !Array.isArray(frequencyData.value.frequencies)) {
            console.log('修复频谱数据：使用请求的频率范围作为frequencies字段');
            frequencyData.value.frequencies = [...freqs];
          }
          
          // 检查每个通道是否有对应的功率值
          if (frequencyData.value.powers) {
            frequencyData.value.channels.forEach(channel => {
              if (!frequencyData.value.powers[channel]) {
                console.warn(`通道 ${channel} 没有对应的功率值，创建空数组`);
                frequencyData.value.powers[channel] = Array(frequencyData.value.frequencies.length).fill(0);
              }
            });
          }
        }
      } else {
        console.warn('响应中缺少频谱数据');
      }
      
      // 处理时频数据 - 使用安全的数据处理方式
      if (response.data.timeFrequency) {
        try {
          const tfData = response.data.timeFrequency;
          console.log('检查时频数据结构', {
            hasTimes: !!tfData.times && Array.isArray(tfData.times),
            hasFreqs: !!tfData.frequencies && Array.isArray(tfData.frequencies),
            hasPower: !!tfData.power && Array.isArray(tfData.power),
            timesLength: tfData.times?.length || 0,
            freqsLength: tfData.frequencies?.length || 0,
            powerDimensions: tfData.power ? (
              Array.isArray(tfData.power[0]) ? (
                Array.isArray(tfData.power[0][0]) ? '3D' : '2D'
              ) : '1D'
            ) : 'unknown'
          });
          
          // 创建安全的时频数据对象
          let safeTimeFreqData = {
            times: [],
            frequencies: [],
            power: [],
            events: []
          };
          
          // 验证并添加时间数组
          if (tfData.times && Array.isArray(tfData.times) && tfData.times.length > 0) {
            safeTimeFreqData.times = tfData.times.map(t => (typeof t === 'number' && !isNaN(t)) ? t : 0);
          } else {
            // 创建默认时间数组
            safeTimeFreqData.times = Array.from({length: 100}, (_, i) => -0.5 + i * 0.015);
            console.warn('使用默认时间数组');
          }
          
          // 验证并添加频率数组
          if (tfData.frequencies && Array.isArray(tfData.frequencies) && tfData.frequencies.length > 0) {
            safeTimeFreqData.frequencies = tfData.frequencies.map(f => (typeof f === 'number' && !isNaN(f)) ? f : 0);
          } else {
            // 使用请求中的频率数组
            safeTimeFreqData.frequencies = [...freqs];
            console.warn('使用请求中的频率数组');
          }
          
          // 验证并添加功率数据
          if (tfData.power && Array.isArray(tfData.power) && tfData.power.length > 0) {
            // 判断power是3D数组还是2D数组
            const is3DPower = tfData.power.length > 0 && 
                           Array.isArray(tfData.power[0]) && 
                           tfData.power[0].length > 0 &&
                           Array.isArray(tfData.power[0][0]);
            
            if (is3DPower) {
              console.log('收到3D时频数据，提取第一个通道的数据');
              // 使用第一个通道的数据
              safeTimeFreqData.power = tfData.power[0].map(row => 
                row.map(val => (typeof val === 'number' && !isNaN(val)) ? val : 0)
              );
            } else if (Array.isArray(tfData.power[0])) {
              // 已是2D格式，但需要验证
              safeTimeFreqData.power = tfData.power.map(row => 
                Array.isArray(row) ? 
                row.map(val => (typeof val === 'number' && !isNaN(val)) ? val : 0) : 
                Array(safeTimeFreqData.times.length).fill(0)
              );
            } else {
              // 格式错误，创建默认2D数组
              console.warn('时频功率数据格式错误，创建默认数据');
              safeTimeFreqData.power = Array(safeTimeFreqData.frequencies.length)
                .fill()
                .map(() => Array(safeTimeFreqData.times.length).fill(0));
            }
          } else {
            // 没有功率数据，创建默认的
            console.warn('缺少功率数据，创建默认数据');
            safeTimeFreqData.power = Array(safeTimeFreqData.frequencies.length)
              .fill()
              .map(() => Array(safeTimeFreqData.times.length).fill(0));
          }
          
          // 验证并添加事件数据
          if (tfData.events && Array.isArray(tfData.events)) {
            safeTimeFreqData.events = tfData.events.map(event => ({
              time: typeof event.time === 'number' ? event.time : 0,
              name: event.name || '事件',
              color: event.color || '#ff0000'
            }));
          } else {
            // 添加默认事件
            safeTimeFreqData.events = [{ time: 0, name: '事件', color: '#ff0000' }];
          }
          
          // 验证维度匹配
          if (safeTimeFreqData.power.length !== safeTimeFreqData.frequencies.length) {
            console.warn(`功率数据维度不匹配：${safeTimeFreqData.power.length} vs ${safeTimeFreqData.frequencies.length}`);
            // 调整功率数组以匹配频率数组
            const newPower = Array(safeTimeFreqData.frequencies.length)
              .fill()
              .map((_, i) => i < safeTimeFreqData.power.length ? 
                safeTimeFreqData.power[i] : Array(safeTimeFreqData.times.length).fill(0)
              );
            safeTimeFreqData.power = newPower;
          }
          
          // 检查每行的长度是否匹配时间数组
          safeTimeFreqData.power.forEach((row, i) => {
            if (row.length !== safeTimeFreqData.times.length) {
              console.warn(`功率数据行 ${i} 长度不匹配：${row.length} vs ${safeTimeFreqData.times.length}`);
              // 调整该行长度
              const newRow = Array(safeTimeFreqData.times.length).fill(0);
              for (let j = 0; j < Math.min(row.length, safeTimeFreqData.times.length); j++) {
                newRow[j] = row[j];
              }
              safeTimeFreqData.power[i] = newRow;
            }
          });
          
          // 使用安全的数据
          timeFrequencyData.value = safeTimeFreqData;
          ElMessage.success('时频分析数据已更新');
        } catch (e) {
          console.error('处理时频数据时出错:', e);
          // 创建完全默认的时频数据
          timeFrequencyData.value = analysisService._createDefaultTimeFrequencyData();
          ElMessage.warning('处理时频数据时出错，使用默认数据');
        }
      } else {
        console.warn('响应中缺少时频数据');
        ElMessage.warning('服务器未返回时频数据，将使用默认数据');
        timeFrequencyData.value = analysisService._createDefaultTimeFrequencyData();
      }
      
      ElMessage.success('频域分析完成');
    } else {
      throw new Error('服务器返回了无效的响应数据');
    }
  } catch (error) {
    console.error('频域分析失败:', error);
    
    // 检查是否有默认数据
    if (error?.defaultData) {
      // 使用API服务返回的默认数据
      console.log('使用API服务返回的默认数据');
      
      if (error.defaultData.spectrum) {
        frequencyData.value = error.defaultData.spectrum;
      }
      
      if (error.defaultData.timeFrequency) {
        timeFrequencyData.value = error.defaultData.timeFrequency;
      }
      
      ElMessage.warning(`频域分析API出错，但已加载默认数据: ${error.message || '未知错误'}`);
    } else {
      // 加载本地示例数据
      ElMessage.error(`频域分析失败: ${error.message || '未知错误'}`);
      
      try {
        console.log('尝试加载本地示例数据');
        const localExampleData = createLocalExampleData();
        frequencyData.value = localExampleData.spectrum;
        timeFrequencyData.value = localExampleData.timeFrequency;
        ElMessage.info('已加载本地示例数据用于展示');
      } catch (e) {
        console.warn('加载本地示例数据也失败', e);
      }
    }
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

// 加载示例数据
const loadExampleData = async () => {
  try {
    console.log('开始加载频域分析示例数据');
    const response = await withLoading(
      analysisService.getFrequencyAnalysisExample(),
      'data'
    );
    
    if (response && response.data) {
      // 检查返回的数据结构
      console.log('获取到示例数据, 检查格式:', {
        hasSpectrum: !!response.data.spectrum,
        hasTimeFrequency: !!response.data.timeFrequency,
        timeFreqDataType: response.data.timeFrequency ? typeof response.data.timeFrequency : 'null'
      });
      
      // 确保数据格式正确
      if (response.data.spectrum) {
        frequencyData.value = response.data.spectrum;
      }
      
      if (response.data.timeFrequency) {
        // 检查时频数据的格式是否符合期望
        const tfData = response.data.timeFrequency;
        if (Array.isArray(tfData.times) && Array.isArray(tfData.frequencies) && Array.isArray(tfData.power)) {
          console.log('时频数据格式正确');
          timeFrequencyData.value = tfData;
        } else {
          console.warn('时频数据格式不符合期望，创建默认格式');
          // 创建默认格式的时频数据
          timeFrequencyData.value = createLocalExampleData().timeFrequency;
        }
      } else {
        console.warn('响应中缺少时频数据，使用本地默认数据');
        timeFrequencyData.value = createLocalExampleData().timeFrequency;
      }
      
      ElMessage.success('示例数据加载成功');
    } else {
      throw new Error('API返回了空响应');
    }
  } catch (error) {
    console.error('加载示例数据失败:', error);
    ElMessage.warning('从服务器加载示例数据失败，使用本地示例数据');
    
    // 创建本地示例数据 - 确保UI可以展示
    const localExampleData = createLocalExampleData();
    frequencyData.value = localExampleData.spectrum;
    timeFrequencyData.value = localExampleData.timeFrequency;
  }
};

// 创建本地示例数据
const createLocalExampleData = () => {
  // 创建频谱数据
  const frequencies = Array.from({length: 50}, (_, i) => i + 1);
  const powers = {};
  
  // 为每个选中的通道创建示例数据
  selectedChannels.value.forEach((ch, index) => {
    // 创建不同特征的功率谱
    const channelPowers = frequencies.map(f => {
      if (index % 3 === 0) {
        // 第一组通道有明显的Alpha峰
        return f < 8 ? 0.1 * f : (f >= 8 && f <= 12 ? 5 - 0.5 * (f - 8) : 0.1 * (50 - f));
      } else if (index % 3 === 1) {
        // 第二组通道有明显的Beta峰
        return f < 13 ? 0.1 * f : (f >= 13 && f <= 30 ? 3 - 0.1 * (f - 13) : 0.1 * (50 - f));
      } else {
        // 第三组通道有明显的Theta峰
        return f < 4 ? 0.1 * f : (f >= 4 && f <= 7 ? 4 - 0.5 * (f - 4) : 0.1 * (50 - f));
      }
    });
    powers[ch] = channelPowers;
  });
  
  // 为时频分析创建数据
  const timePoints = Array.from({length: 100}, (_, i) => -200 + i * 10); // -200ms 到 800ms
  const freqs = Array.from({length: 40}, (_, i) => i + 1); // 1-40Hz
  
  // 创建2D功率数组
  const power = [];
  for (let i = 0; i < freqs.length; i++) {
    const freqPower = [];
    for (let j = 0; j < timePoints.length; j++) {
      // 根据频率和时间创建不同的模式
      const t = timePoints[j] / 1000; // 转换为秒
      const f = freqs[i];
      
      let val = 0;
      if (f >= 8 && f <= 12 && t >= 0.1) { // Alpha
        val = 3 + 2 * Math.sin(t * 5) * Math.exp(-t);
      } else if (f >= 13 && f <= 30 && t >= 0.2) { // Beta
        val = 2 + Math.sin(t * 8) * Math.exp(-t);
      } else if (f >= 4 && f <= 7 && t >= 0) { // Theta
        val = 4 + 3 * Math.sin(t * 3) * Math.exp(-t);
      } else {
        val = 0.5 * Math.random();
      }
      
      freqPower.push(val);
    }
    power.push(freqPower);
  }
  
  return {
    spectrum: {
      frequencies: frequencies,
      channels: selectedChannels.value,
      powers: powers
    },
    timeFrequency: {
      times: timePoints,
      frequencies: freqs,
      power: power,
      events: [
        { time: 0, name: '刺激呈现', color: '#ff0000' },
        { time: 300, name: '反应', color: '#00ff00' }
      ]
    }
  };
};

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}

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
  frequencyData.value = null;
  timeFrequencyData.value = null;
  preprocessedDataAvailable.value = false;
  preprocessedData.value = null;
  
  const hasPreprocessedData = loadPreprocessedData();
  if (!hasPreprocessedData) {
    await loadSubjectInfo();
  }
});
</script>

<template>
  <AppLayout>
    <div class="frequency-analysis-container">
      <!-- 控制面板 -->
      <el-card class="control-panel">
        <template #header>
          <div class="card-header">
            <h3>频域分析设置</h3>
            <el-tag v-if="preprocessedDataAvailable" size="small" type="success">已加载预处理数据</el-tag>
          </div>
        </template>
        
        <el-form :model="analysisOptions" label-width="120px">
          <!-- 通道选择 -->
          <el-form-item label="选择通道">
            <div class="channel-selection">
              <el-button type="primary" size="small" @click="handleSelectChannels" :disabled="isLoading.data">
                选择通道 ({{ selectedChannels.length }}/{{ availableChannels.length }})
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
            <div v-for="(band, name) in analysisOptions?.bands || {}" :key="name" class="band-chart">
              <h4>{{ name.charAt(0).toUpperCase() + name.slice(1) }} 频带 ({{ band?.[0] || 0 }}-{{ band?.[1] || 0 }} Hz)</h4>
              <FrequencyChart 
                v-if="frequencyData && frequencyData.frequencies && frequencyData.powers"
                :data="{
                  frequencies: frequencyData.frequencies.filter(f => f >= (band?.[0] || 0) && f <= (band?.[1] || 100)),
                  powers: Object.fromEntries(
                    (frequencyData.channels || Object.keys(frequencyData.powers || {})).map(ch => [
                      ch,
                      ((frequencyData.powers || {})[ch] || []).filter((_, i) => 
                        frequencyData.frequencies[i] >= (band?.[0] || 0) && 
                        frequencyData.frequencies[i] <= (band?.[1] || 100)
                      )
                    ])
                  ),
                  channels: frequencyData.channels || Object.keys(frequencyData.powers || {})
                }"
                :logScale="analysisOptions?.display?.logScale ?? false"
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
            :colorMap="analysisOptions?.display?.colorMap || 'jet'"
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
  </AppLayout>
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