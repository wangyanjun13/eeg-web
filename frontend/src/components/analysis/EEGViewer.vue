<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useDebounce, useDebounceFn } from '@/composables/useDebounce'
import { useChannelPositions } from '@/composables/useChannelPositions' // 导入通道位置组合式函数
import { InfoFilled } from '@element-plus/icons-vue'

// 作用：EEG数据可视化组件
// 参数：
//   data: 包含EEG数据的对象
//   timeRange: 时间范围，默认[0, 10]
//   selectedChannels: 选中的通道，默认[]
//   availableChannels: 可用于选择的通道列表
//   disableChannelSelect: 是否禁用通道选择
//   viewMode: 查看模式，'time'或'frequency'

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  timeRange: {
    type: Array,
    default: () => [0, 10]
  },
  selectedChannels: {
    type: Array,
    default: () => []
  },
  availableChannels: {  // 新增：可用于选择的通道列表
    type: Array,
    default: () => []
  },
  disableChannelSelect: {  // 新增：是否禁用通道选择
    type: Boolean,
    default: false
  },
  viewMode: {  // 新增：视图模式
    type: String,
    default: 'time' // 'time' 或 'frequency'
  },
  initialTimeRange: {
    type: Array,
    default: () => [0, 10]
  },
  persistTimeRange: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:timeRange', 'update:selectedChannels', 'update:viewMode'])

// 核心状态
const chartRef = ref(null)
let chart = null
const isFullScreen = ref(false)
const themeStyle = ref('light')
const channelCompareVisible = ref(false)
const legendSelected = ref({}) // 存储图例选中状态
const isYAxisInverted = ref(false) // 纵坐标是否反转
const localViewMode = ref(props.viewMode) // 本地视图模式状态

// 使用通道位置组合式函数
const { 
  fetchElectrodePositions, 
  getChannelPosition, 
  isLoading: positionsLoading,
  error: positionsError,
  positionSource,
  // 通道选择相关
  openChannelSelect,
  renderChannelSelectDialog
} = useChannelPositions()

// 在setup函数中，修改timeRange的初始化
const timeRange = ref(props.initialTimeRange || [0, 10]);

// 确保时间范围变化时触发事件和更新图表
watch(() => props.timeRange, (newRange) => {
  if (newRange && Array.isArray(newRange)) {
    timeRange.value = [...newRange];
    nextTick(() => {
      updateChart();
    });
  }
}, { deep: true, immediate: true });

// 导出组件设置函数供外部使用
const setup = () => {
  return {
    openChannelSelect
  };
};

// 为组件的 setup 函数赋值给组件的静态属性
defineExpose({
  setup
});

// 图表初始化和更新
const initChart = () => {
  if (!chartRef.value) {
    // DOM 元素不存在，延迟初始化
    setTimeout(() => initChart(), 50);
    return;
  }
  
  if (chart) chart.dispose();
  try {
    chart = echarts.init(chartRef.value, themeStyle.value);
    
    // 事件监听统一设置
    chart.on('legendselectchanged', ({selected}) => legendSelected.value = {...legendSelected.value, ...selected});
    chart.on('mouseover', 'series', handleSeriesMouseover);
    chart.on('mouseout', 'series', () => chart.setOption({tooltip: {showContent: false}}));
    
    window.addEventListener('resize', () => chart?.resize());
    updateChart();
  } catch (error) {
    console.error('ECharts 初始化失败:', error);
    // 如果初始化失败，延迟重试
    setTimeout(() => initChart(), 100);
  }
};

// 鼠标悬停处理
const handleSeriesMouseover = (params) => {
  if (params.componentType === 'series') {
    chart.setOption({
      tooltip: {
        showContent: true,
        formatter: (p) => {
          if (localViewMode.value === 'time') {
            const time = p.data[0]?.toFixed(3) || p.data[0]
            const value = p.data[1]?.toFixed(3) || p.data[1]
            return `<span style="color: ${p.color}">${p.seriesName}</span><br/>时间: ${time} s<br/>电压: ${value} μV`
          } else {
            const freq = p.data[0]?.toFixed(2) || p.data[0]
            const power = p.data[1]?.toFixed(3) || p.data[1]
            return `<span style="color: ${p.color}">${p.seriesName}</span><br/>频率: ${freq} Hz<br/>功率谱密度: ${power} μV²/Hz`
          }
        }
      }
    })
  }
}

// 生成图表配置
const getChartOption = (series = [], legendStatus = {}) => {
  const baseOption = {
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      top: 0,
      left: 'center',
      width: '90%',
      data: Array.isArray(series) ? series.map(s => s.name) : [],
      textStyle: { fontSize: 12 },
      pageButtonItemGap: 5,
      pageButtonPosition: 'end',
      pageIconSize: 12,
      tooltip: { show: true },
      selectedMode: true,
      selected: legendStatus
    },
    tooltip: {
      show: true,
      trigger: 'item',
      axisPointer: {
        type: 'cross',
        snap: true,
        label: { show: true }
      },
      showContent: false,
      position: (pos) => [pos[0] + 10, pos[1] - 10]
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '50px',
      containLabel: true
    },
    series
  };
  
  if (localViewMode.value === 'time') {
    // 确定实际的时间范围
    let actualTimeRange = props.timeRange;
    
    // 优先使用数据中的精确timeRange（从数据处理过程中传递过来的）
    if (props.data?.timeRange && Array.isArray(props.data.timeRange) && props.data.timeRange.length === 2) {
      // 数据本身包含预设的时间范围（如分段后或处理后的结果）
      const dataTimeRange = props.data.timeRange;
      console.log("使用数据中的预设时间范围:", dataTimeRange);
      
      // 确保范围有效（不能为零宽度）
      if (dataTimeRange[1] > dataTimeRange[0] && (dataTimeRange[1] - dataTimeRange[0]) > 0.001) {
        actualTimeRange = dataTimeRange;
      } else {
        console.warn("数据中的时间范围无效:", dataTimeRange);
      }
    } 
    // 其次从实际数据点中提取范围
    else {
      // 搜集所有时间点并找出真实范围
      let allTimePoints = [];
      series.forEach(s => {
        if (s.data && Array.isArray(s.data)) {
          s.data.forEach(point => {
            if (Array.isArray(point) && point.length > 1 && typeof point[0] === 'number') {
              allTimePoints.push(point[0]);
            }
          });
        }
      });
      
      // 如果有收集到真实时间点，确定范围
      if (allTimePoints.length > 0) {
        allTimePoints.sort((a, b) => a - b);
        const minTime = allTimePoints[0];
        const maxTime = allTimePoints[allTimePoints.length - 1];
        
        // 确保范围有效，并与props.timeRange进行比较
        if (maxTime > minTime && (maxTime - minTime) > 0.001) {
          // 数据点有有效的时间分布
          if (Math.abs(minTime - props.timeRange[0]) > 0.1 || Math.abs(maxTime - props.timeRange[1]) > 0.1) {
            console.log(`根据实际数据点调整时间范围: [${minTime.toFixed(2)}, ${maxTime.toFixed(2)}] (原范围: [${props.timeRange[0]}, ${props.timeRange[1]}])`);
          }
          actualTimeRange = [minTime, maxTime];
        }
      } 
      // 或者从times数组中推断
      else if (props.data?.times && props.data.times.length > 1) {
        const minTime = props.data.times[0];
        const maxTime = props.data.times[props.data.times.length - 1];
        
        // 确保范围有效
        if (maxTime > minTime && (maxTime - minTime) > 0.001) {
          actualTimeRange = [minTime, maxTime];
        }
      }
    }
    
    // 最终安全检查 - 确保时间范围有效且合理
    if (!actualTimeRange || actualTimeRange.length !== 2 || actualTimeRange[0] === actualTimeRange[1] || 
        (actualTimeRange[1] - actualTimeRange[0]) < 0.001) {
      console.warn("时间范围无效或过小，使用默认值:", props.timeRange);
      actualTimeRange = props.timeRange;
    }
    
    console.log("EEGViewer使用时间范围:", actualTimeRange);
    
    // 如果图表显示的时间范围与传入的不一致，更新本地timeRange并触发事件
    // 这使得预处理步骤间的时间范围可以保持一致
    if (JSON.stringify(timeRange.value) !== JSON.stringify(actualTimeRange)) {
      console.log("更新本地时间范围:", actualTimeRange);
      timeRange.value = [...actualTimeRange];
      // 不立即触发事件，避免循环更新
    }
    
    // 配置X轴
    baseOption.xAxis = {
      type: 'value',
      name: '时间 (s)',
      min: actualTimeRange[0],
      max: actualTimeRange[1],
      axisLabel: {
        formatter: '{value} s'
      }
    };
    
    // 添加事件相关信息 (如果有)
    if (props.data?.segment_info?.type === 'event_related') {
      // 添加事件发生时刻的标记线
      series.push({
        type: 'line',
        name: '事件标记',
        silent: true,
        symbolSize: 0,
        markLine: {
          silent: true,
          symbol: 'none',
          label: { show: true, position: 'middle', formatter: '事件' },
          lineStyle: { color: '#ff9800', type: 'solid', width: 2 },
          data: [{ xAxis: 0, name: '事件' }]
        }
      });
      
      // 添加事件相关信息为标题
      if (props.data.segment_info.event_count > 0) {
        baseOption.title = {
          show: true,
          text: `事件类型: ${props.data.segment_info.event_id} (${props.data.segment_info.event_count}个事件平均)`,
          textStyle: { fontSize: 12, color: '#606266' },
          left: 'center',
          top: 0,
          padding: [0, 0, 10, 0]
        };
        baseOption.grid.top = '60px';
      }
    }
    
    // 为Y轴设置合理的范围
    // 找到所有数据系列的最大值和最小值
    let yMin = Infinity;
    let yMax = -Infinity;
    
    series.forEach(s => {
      if (s.data && Array.isArray(s.data)) {
        s.data.forEach(point => {
          if (Array.isArray(point) && point.length > 1) {
            const value = point[1];
            if (typeof value === 'number' && !isNaN(value)) {
              yMin = Math.min(yMin, value);
              yMax = Math.max(yMax, value);
            }
          }
        });
      }
    });
    
    // 确保y轴范围有效
    if (yMin === Infinity || yMax === -Infinity || Math.abs(yMin - yMax) < 0.001) {
      console.warn("Y轴范围无效，使用默认值");
      yMin = -100;
      yMax = 100;
    } else {
      // 增加一点余量，使图表更美观
      const padding = Math.max((yMax - yMin) * 0.1, 0.1);
      yMin -= padding;
      yMax += padding;
    }
    
    baseOption.yAxis = {
      type: 'value',
      name: '电压 (μV)',
      nameLocation: 'middle',
      nameGap: 40,
      nameRotate: 90,
      inverse: isYAxisInverted.value,
      min: yMin,
      max: yMax
    };
  } else {
    const samplingRate = props.data?.sampling_rate || 100;
    const nyquistFreq = samplingRate / 2;
    
    // 确保频率范围合理
    let maxFreq = Math.min(nyquistFreq, 100);
    if (maxFreq < 1) {
      console.warn('采样率异常，设置默认频率范围');
      maxFreq = 100;
    }
    
    baseOption.xAxis = {
      type: 'value',
      name: '频率 (Hz)',
      min: 0,
      max: maxFreq,
      axisLabel: {
        formatter: '{value} Hz'
      }
    };
    
    // 添加常见EEG频段标记
    const bandMarkers = [
      { value: 4, name: 'θ', color: 'rgba(110, 110, 110, 0.4)' },
      { value: 8, name: 'α', color: 'rgba(110, 110, 110, 0.4)' },
      { value: 13, name: 'β', color: 'rgba(110, 110, 110, 0.4)' },
      { value: 30, name: 'γ', color: 'rgba(110, 110, 110, 0.4)' }
    ];
    
    // 过滤掉超出显示范围的标记
    const validMarkers = bandMarkers.filter(marker => marker.value <= maxFreq);
    
    // 如果有有效的频段标记，添加标记线
    if (validMarkers.length > 0) {
      baseOption.series.push({
        type: 'line',
        name: 'EEG频段',
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: '#888', type: 'dashed', width: 1 },
          label: { show: true, position: 'start' },
          data: validMarkers.map(marker => ({
            xAxis: marker.value,
            name: marker.name,
            lineStyle: { color: marker.color }
          }))
        }
      });
    }
    
    baseOption.yAxis = {
      type: 'value',
      name: '功率谱密度 (μV²/Hz)',
      nameLocation: 'middle',
      nameGap: 50,
      nameRotate: 90,
      scale: true
    };
  }
  
  baseOption.dataZoom = [{
    type: 'inside',
    start: 0,
    end: 100
  }];
  
  return baseOption;
}

// 计算频谱数据
const calculateSpectrumData = (channelData, times) => {
  if (!channelData || !times || channelData.length === 0) return [];
  
  try {
    // 确保正确计算采样率
    const samplingRate = props.data.sampling_rate || 1 / (times[1] - times[0]);
    
    // 使用FFT计算频谱
    // 仅计算开始和结束时间范围内的数据
    const startIndex = Math.max(0, Math.floor(props.timeRange[0] / (times[1] - times[0])));
    const endIndex = Math.min(channelData.length - 1, Math.ceil(props.timeRange[1] / (times[1] - times[0])));
    
    // 确保数据长度是2的幂，便于FFT计算
    let dataLength = endIndex - startIndex;
    // 找到最接近的2的幂
    dataLength = Math.pow(2, Math.floor(Math.log2(dataLength)));
    
    const slicedData = channelData.slice(startIndex, startIndex + dataLength);
    
    // 应用汉宁窗减少频谱泄漏
    const windowedData = slicedData.map((x, i) => 
      x * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / (dataLength - 1)))
    );
    
    // 使用Web API的FFT或替代方法
    const fft = performFFT(windowedData, samplingRate);
    
    // 获取采样率的一半 (Nyquist频率) 作为最大频率
    const nyquistFreq = samplingRate / 2;
    
    // 确定有效范围：从0到Nyquist频率
    const maxFreqIndex = Math.min(Math.floor(nyquistFreq * dataLength / samplingRate), fft.length / 2);
    
    // 返回计算结果，无需添加冗余日志
    return fft.slice(0, maxFreqIndex).map((value, index) => {
      const freq = index * samplingRate / dataLength;
      return [freq, value];
    });
  } catch (error) {
    console.error('计算频谱出错:', error);
    return [];
  }
}

// 简化的FFT实现
const performFFT = (timeData, samplingRate) => {
  // 简单的功率谱估计，实际应用中可使用更复杂的FFT算法或库
  const n = timeData.length;
  const result = Array(n / 2).fill(0);
  
  // 加窗并移除直流分量
  let mean = 0;
  for (let i = 0; i < n; i++) mean += timeData[i];
  mean /= n;
  
  // 使用汉宁窗计算加窗数据
  const windowed = timeData.map((x, i) => 
    (x - mean) * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / (n - 1)))
  );
  
  // 功率谱计算 - 标准脑电分析中通常使用功率谱密度(PSD)表示
  // 单位应为μV²/Hz，需要除以频率分辨率(samplingRate/n)来获得密度
  const freqResolution = samplingRate / n;
  for (let k = 0; k < n / 2; k++) {
    let real = 0, imag = 0;
    for (let t = 0; t < n; t++) {
      const angle = -2 * Math.PI * k * t / n;
      real += windowed[t] * Math.cos(angle);
      imag += windowed[t] * Math.sin(angle);
    }
    
    // 功率谱密度计算 - 平方后除以频率分辨率
    const magnitude = (real * real + imag * imag) / (n * n);
    result[k] = magnitude / freqResolution; // 单位为μV²/Hz
  }
  
  return result;
}

// 使用防抖函数优化图表更新
const debouncedUpdateChart = useDebounceFn(() => {
  if (!chart || !props.data) {
    console.warn('Chart或数据不存在，无法更新图表');
    return;
  }
  
  // 过滤确保只使用可用通道，并添加额外检查
  const allDataChannels = props.data.channels || [];
  const availableDataChannels = props.data.data ? Object.keys(props.data.data) : [];
  
  // 确保只使用真正可用的通道
  let validChannels = props.selectedChannels.filter(channel => 
    // 通道必须存在于props.availableChannels或者data.channels中
    (props.availableChannels.length > 0 
      ? props.availableChannels.includes(channel) 
      : allDataChannels.includes(channel))
    // 同时通道必须在data.data中有数据
    && availableDataChannels.includes(channel)
  );
  
  if (validChannels.length === 0) {
    console.warn('没有有效的通道数据，尝试从data.data中获取可用通道');
    // 如果没有有效通道，尝试使用availableDataChannels的前几个
    validChannels = availableDataChannels.slice(0, Math.min(5, availableDataChannels.length));
  }
  
  // 添加对数据结构的详细检查
  if (validChannels.length > 0) {
    const firstChannel = validChannels[0];
  }
  
  let series = [];
  
  if (localViewMode.value === 'time') {
    // 时域表示
    series = validChannels.map((channel, index) => {
      // 增强健壮性检查
      if (!props.data.data || !props.data.data[channel] || !Array.isArray(props.data.data[channel])) {
        console.warn(`通道 ${channel} 数据不存在或无效，将被跳过`);
        return {
          name: channel,
          type: 'line',
          showSymbol: false,
          data: [[0, 0]], // 至少有一个点以避免错误
          animationDuration: 0
        };
      }
      
      // 确保数据和时间点长度匹配
      let dataPoints = [];
      const channelData = props.data.data[channel];
      const times = props.data.times || [];
      
      // 增加数据检查和修复
      console.log(`通道 ${channel} 数据长度: ${channelData.length}, 时间点数: ${times.length}`);
      
      // 检查时间数据是否存在问题 - 判断是否所有时间点都相同或过于接近
      let timeDataProblem = false;
      if (times.length > 1) {
        // 计算时间点的范围
        const timeRange = times[times.length - 1] - times[0];
        if (timeRange < 0.001) { // 如果时间范围非常小，认为有问题
          console.warn(`通道 ${channel} 的时间数据异常 - 范围太小: ${timeRange}s`);
          timeDataProblem = true;
        }
        
        // 检查前几个时间点是否相同
        if (times.length > 5) {
          const allSame = times.slice(0, 5).every(t => Math.abs(t - times[0]) < 0.0001);
          if (allSame) {
            console.warn(`通道 ${channel} 的时间数据异常 - 前几个点都相同`);
            timeDataProblem = true;
          }
        }
      }
      
      // 处理时间数据问题
      if (timeDataProblem || times.length === 0) {
        console.warn(`为通道 ${channel} 创建新的时间序列数据`);
        
        // 创建均匀分布的时间点
        const syntheticTimes = [];
        const timeRange = props.timeRange[1] - props.timeRange[0];
        const pointCount = channelData.length;
        
        if (pointCount > 1) {
          for (let i = 0; i < pointCount; i++) {
            syntheticTimes.push(props.timeRange[0] + (i * timeRange / (pointCount - 1)));
          }
          
          // 使用合成的时间点创建数据点
          for (let i = 0; i < pointCount; i++) {
            if (syntheticTimes[i] >= props.timeRange[0] && syntheticTimes[i] <= props.timeRange[1]) {
              const value = typeof channelData[i] === 'number' && !isNaN(channelData[i]) ? channelData[i] : 0;
              dataPoints.push([syntheticTimes[i], value]);
            }
          }
        }
      } else if (channelData && times && channelData.length > 0 && times.length > 0) {
        // 正常处理有效的时间数据
        const minLength = Math.min(channelData.length, times.length);
        
        // 对于通道数据样本数与时间点数不匹配的情况做特殊处理
        if (channelData.length !== times.length) {
          console.warn(`通道 ${channel} 数据长度(${channelData.length})与时间点长度(${times.length})不匹配`);
        }
        
        for (let i = 0; i < minLength; i++) {
          if (times[i] >= props.timeRange[0] && times[i] <= props.timeRange[1]) {
            // 确保数据是有效的数值
            const value = typeof channelData[i] === 'number' && !isNaN(channelData[i]) ? channelData[i] : 0;
            dataPoints.push([times[i], value]);
          }
        }
      }
      
      // 如果没有有效点，添加一个0点
      if (dataPoints.length === 0) {
        dataPoints.push([props.timeRange[0], 0]);
      }
      
      return {
        name: channel,
        type: 'line',
        showSymbol: false,
        sampling: 'lttb',
        data: dataPoints,
        animationDuration: 0,
        emphasis: { focus: 'none' },
        itemStyle: {
          color: chart?.getOption()?.series?.[index]?.itemStyle?.color,
          opacity: 0.8
        }
      };
    });
  } else {
    // 这里保留频域表示处理逻辑，但我们暂时不修改它，因为它不是当前问题
    series = validChannels.map((channel, index) => {
      // 确保通道数据存在
      if (!props.data.data || !props.data.data[channel]) {
        console.warn(`通道 ${channel} 数据不存在，将被跳过`);
        return {
          name: channel,
          type: 'line',
          showSymbol: false,
          data: [[0, 0]],
          animationDuration: 0
        };
      }
      
      // 只需调用现有的函数，不做修改
      const spectrumData = calculateSpectrumData(
        props.data.data[channel], 
        props.data.times
      );
      
      // 确保至少有一个点
      if (!spectrumData || spectrumData.length === 0) {
        return {
          name: channel,
          type: 'line',
          showSymbol: false,
          data: [[0, 0]],
          animationDuration: 0,
          emphasis: { focus: 'none' },
          itemStyle: {
            color: chart?.getOption()?.series?.[index]?.itemStyle?.color,
            opacity: 0.8
          }
        };
      }
      
      return {
        name: channel,
        type: 'line',
        showSymbol: false,
        sampling: 'lttb',
        data: spectrumData,
        animationDuration: 0,
        emphasis: { focus: 'none' },
        itemStyle: {
          color: chart?.getOption()?.series?.[index]?.itemStyle?.color,
          opacity: 0.8
        }
      };
    });
  }

  // 如果系列为空，显示警告
  if (!series || series.length === 0) {
    console.warn('没有有效的数据系列可以显示');
    series = [{
      name: '无数据',
      type: 'line',
      data: [[0, 0]],
      lineStyle: { color: '#ccc', type: 'dashed' }
    }];
  }

  // 准备图例状态
  const legendStatus = validChannels.reduce((status, channel) => {
    status[channel] = legendSelected.value[channel] !== undefined 
      ? legendSelected.value[channel] 
      : true;
    return status;
  }, {});
  
  // 设置图表选项
  try {
    chart.setOption(getChartOption(series, legendStatus), true);
  } catch (error) {
    console.error('设置图表选项失败:', error);
  }
}, 100);

// 修改 updateChart 函数
const updateChart = () => {
  if (!chart || !props.data) return;
  
  // 确保使用当前的时间范围
  const currentTimeRange = timeRange.value;
  
  // 调用 debouncedUpdateChart 而不是直接设置选项
  debouncedUpdateChart();
};

// 监听 selectedChannels 变化
watch(() => props.selectedChannels, () => {
  nextTick(updateChart);
}, { deep: true });

// 监听 availableChannels 变化
watch(() => props.availableChannels, () => {
  nextTick(updateChart);
}, { deep: true });

// 监听 viewMode 变化
watch(() => props.viewMode, (newValue) => {
  localViewMode.value = newValue;
  nextTick(updateChart);
});

// 切换视图模式
const toggleViewMode = () => {
  localViewMode.value = localViewMode.value === 'time' ? 'frequency' : 'time';
  emit('update:viewMode', localViewMode.value);
  nextTick(updateChart);
}

// 切换纵坐标方向
const toggleYAxisDirection = () => {
  isYAxisInverted.value = !isYAxisInverted.value
  updateChart()
}

// 获取当前时间点
const getCurrentTime = () => {
  if (!chart || !props.data?.times) return 0
  const axisPointer = chart.getOption().axisPointer
  if (axisPointer?.[0]?.value) return axisPointer[0].value
  const xAxis = chart.getOption().xAxis[0]
  return xAxis ? ((xAxis.min || props.timeRange[0]) + (xAxis.max || props.timeRange[1])) / 2 : props.timeRange[0]
}

// 双击显示通道数据比较
const showChannelCompare = (event) => {
  if (event.detail === 2) {
    const pointInGrid = chart.convertFromPixel({seriesIndex: 0}, [event.offsetX, event.offsetY])
    if (pointInGrid) {
      chart.setOption({ axisPointer: { value: pointInGrid[0] } })
    }
    channelCompareVisible.value = true
  }
}

// 打开通道选择对话框
const toggleChannelSelect = () => {
  if (props.disableChannelSelect) {
    ElMessage.info('当前预处理步骤不允许更改通道选择');
    return;
  }
  
  // 使用传入的可用通道列表或数据中的通道列表
  const availableChannelList = props.availableChannels.length > 0 
    ? props.availableChannels 
    : props.data?.channels || [];
    
  openChannelSelect(
    props.selectedChannels, 
    availableChannelList, 
    (selected) => {
      emit('update:selectedChannels', selected)
      nextTick(updateChart)
    }
  )
}

// 通道比较数据
const channelCompareContent = computed(() => {
  if (!props.data || !props.selectedChannels.length) return []
  
  const currentPoint = getCurrentTime() // 获取当前坐标点
  
  if (localViewMode.value === 'time') {
    // 时域模式 - 显示时间-电压信息
    const timeIndex = props.data.times.findIndex(t => t >= currentPoint)
    
    return props.selectedChannels.map((channel, index) => ({
      channel,
      value: props.data.data[channel]?.[timeIndex]?.toFixed(3) || 0,
      unit: 'μV',
      color: chart?.getOption()?.series?.[index]?.itemStyle?.color || '#000'
    }))
  } else {
    // 频域模式 - 显示频率-功率信息
    return props.selectedChannels.map((channel, index) => {
      // 计算频谱数据
      const spectrumData = calculateSpectrumData(
        props.data.data[channel],
        props.data.times
      );
      
      // 找到最接近当前频率点的数据
      let closestPoint = null;
      let minDistance = Infinity;
      
      for (const point of spectrumData) {
        const distance = Math.abs(point[0] - currentPoint);
        if (distance < minDistance) {
          minDistance = distance;
          closestPoint = point;
        }
      }
      
      return {
        channel,
        value: closestPoint ? closestPoint[1].toFixed(3) : 0,
        unit: 'μV²/Hz',  // 专业的功率谱密度单位
        color: chart?.getOption()?.series?.[index]?.itemStyle?.color || '#000'
      };
    });
  }
})

// 全屏切换 - 简化版本，仅切换状态
const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value
  setTimeout(() => chart?.resize(), 100)
}

// 主题切换
const toggleTheme = () => {
  themeStyle.value = themeStyle.value === 'light' ? 'dark' : 'light'
  initChart()
}

// 获取电极位置
const loadElectrodePositions = async () => {
  if (props.data?.dataset_id && props.data?.subject_id) {
    await fetchElectrodePositions(props.data.dataset_id, props.data.subject_id)
  }
}

// 生命周期钩子
onMounted(async () => {
  await loadElectrodePositions()
  initChart()
  chartRef.value?.addEventListener('click', showChannelCompare)
})

onBeforeUnmount(() => {
  if (chart) {
    chart.dispose()
    chartRef.value?.removeEventListener('click', showChannelCompare)
    chart = null
  }
  window.removeEventListener('resize', () => chart?.resize())
})
</script>

<template>
  <div class="eeg-viewer">
    <div class="chart-controls">
      <el-button-group>
        <el-button 
          size="small" 
          @click="toggleChannelSelect"
          :disabled="disableChannelSelect"
        >
          选择显示通道
        </el-button>
        <el-button 
          size="small" 
          @click="toggleViewMode"
          :type="localViewMode === 'time' ? '' : 'primary'"
        >
          {{ localViewMode === 'time' ? '频域视图' : '时域视图' }}
        </el-button>
        <el-button size="small" @click="toggleTheme">切换主题</el-button>
        <el-button size="small" @click="toggleFullScreen">
          {{ isFullScreen ? '退出全屏' : '全屏' }}
        </el-button>
      </el-button-group>
    </div>
    
    <!-- 添加简约提示 -->
    <div class="chart-tip">
      <el-tooltip content="双击图表可查看具体时间点的数据" placement="top">
        <el-icon><InfoFilled /></el-icon>
        <span>双击查看数据</span>
      </el-tooltip>
    </div>
    
    <div class="coordinate-controls">
      <el-tooltip 
        :content="localViewMode === 'time' ? '反转纵坐标轴（负值向上显示）' : '调整频谱比例'"
        placement="top"
      >
        <el-button 
          type="primary" 
          :plain="!isYAxisInverted" 
          size="small" 
          @click="toggleYAxisDirection"
          class="invert-button"
          v-if="localViewMode === 'time'"
        >
          {{ isYAxisInverted ? '恢复' : '坐标反转' }}
        </el-button>
      </el-tooltip>
    </div>
    
    <div 
      ref="chartRef" 
      class="chart-container"
      :style="{ height: isFullScreen ? 'calc(100vh - 120px)' : '500px' }"
    ></div>
    
    <!-- 通道选择对话框 -->
    <component :is="renderChannelSelectDialog()" />
    
    <!-- 通道数据比较对话框 -->
    <el-dialog v-model="channelCompareVisible" 
      :title="localViewMode === 'time' ? '通道数据对比' : '频谱功率密度对比'" 
      width="30%">
      <div class="channel-compare">
        <div class="time-info">
          <template v-if="localViewMode === 'time'">
            当前时间: {{ getCurrentTime().toFixed(3) }} s
          </template>
          <template v-else>
            当前频率: {{ getCurrentTime().toFixed(2) }} Hz
          </template>
        </div>
        <div v-for="item in channelCompareContent" :key="item.channel" class="channel-item">
          <span :style="{ color: item.color }">{{ item.channel }}</span>: 
          {{ item.value }} {{ item.unit }}
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.eeg-viewer {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.chart-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}
/* 坐标轴反转按钮样式 */
.coordinate-controls {
  display: flex;
  justify-content: left;
  margin-bottom: 10px;
  padding-left: 10px;
}
/* 坐标轴反转按钮样式 */
.invert-button {
  padding: 6px 15px;
  font-size: 12px;
}

.chart-container {
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.channel-compare {
  max-height: 400px;
  overflow-y: auto;
}

.time-info {
  margin-bottom: 10px;
  font-weight: bold;
}

.channel-item {
  margin: 5px 0;
}
</style>
