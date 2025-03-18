<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

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
  }
})

const emit = defineEmits(['update:timeRange', 'update:selectedChannels'])

// Chart references
const chartRef = ref(null)
let chart = null
const isFullScreen = ref(false)
const themeStyle = ref('light')

// 初始化图表
const initChart = () => {
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value, themeStyle.value)
  
  // 窗口大小改变时，重新调整图表大小
  window.addEventListener('resize', () => {
    chart && chart.resize()
  })
  
  updateChart()
}

// 更新图表数据
const updateChart = () => {
  if (!chart || !props.data || !props.data.data) return
  
  const option = {
    title: {
      text: 'EEG数据可视化',
      subtext: `采样率: ${props.data.sampling_rate}Hz`
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const param = params[0]
        return `
          <div>时间: ${param.axisValue.toFixed(3)}s</div>
          ${params.map(p => `<div>${p.seriesName}: ${p.value.toFixed(2)}μV</div>`).join('')}
        `
      }
    },
    legend: {
      data: props.selectedChannels,
      type: 'scroll',
      bottom: 0
    },
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none'
        },
        saveAsImage: {}
      }
    },
    dataZoom: [
      {
        type: 'slider',
        xAxisIndex: 0,
        start: (props.timeRange[0] / props.data.duration) * 100,
        end: (props.timeRange[1] / props.data.duration) * 100
      },
      {
        type: 'inside',
        xAxisIndex: 0,
        start: 0,
        end: 100
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '时间 (秒)',
      min: props.timeRange[0],
      max: props.timeRange[1]
    },
    yAxis: {
      type: 'value',
      name: '振幅 (μV)',
      scale: true
    },
    series: props.selectedChannels.map(channel => {
      const channelData = props.data.data[channel]
      
      // 根据时间范围筛选数据点
      const timeStart = props.timeRange[0] * props.data.sampling_rate
      const timeEnd = props.timeRange[1] * props.data.sampling_rate
      const filteredData = channelData.filter((_, idx) => idx >= timeStart && idx <= timeEnd)
      
      // 时间点
      const timePoints = Array.from(
        { length: filteredData.length },
        (_, i) => props.timeRange[0] + (i / props.data.sampling_rate)
      )
      
      // 组合数据
      const data = timePoints.map((time, idx) => [time, filteredData[idx]])
      
      return {
        name: channel,
        type: 'line',
        showSymbol: false,
        data: data,
        animationDuration: 0
      }
    })
  }
  
  chart.setOption(option)
  
  // 监听数据区域缩放事件，更新timeRange
  chart.on('dataZoom', (params) => {
    if (params.batch) {
      const { start, end } = params.batch[0]
      const newTimeRange = [
        (start / 100) * props.data.duration,
        (end / 100) * props.data.duration
      ]
      emit('update:timeRange', newTimeRange)
    }
  })
}

// 切换全屏
const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value
  
  if (isFullScreen.value) {
    chartRef.value.style.position = 'fixed'
    chartRef.value.style.top = '0'
    chartRef.value.style.left = '0'
    chartRef.value.style.width = '100vw'
    chartRef.value.style.height = '100vh'
    chartRef.value.style.zIndex = '9999'
    chartRef.value.style.background = themeStyle.value === 'dark' ? '#333' : '#fff'
  } else {
    chartRef.value.style.position = 'relative'
    chartRef.value.style.top = 'auto'
    chartRef.value.style.left = 'auto'
    chartRef.value.style.width = '100%'
    chartRef.value.style.height = '500px'
    chartRef.value.style.zIndex = 'auto'
  }
  
  // 重新调整图表大小
  setTimeout(() => {
    chart && chart.resize()
  }, 100)
}

// 切换主题
const toggleTheme = () => {
  themeStyle.value = themeStyle.value === 'light' ? 'dark' : 'light'
  initChart()
}

// 监听props变化
watch(() => props.data, initChart, { deep: true })
watch(() => props.timeRange, updateChart, { deep: true })
watch(() => props.selectedChannels, updateChart, { deep: true })

// 生命周期钩子
onMounted(() => {
  if (props.data) {
    initChart()
  }
})

onBeforeUnmount(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
  window.removeEventListener('resize', () => {
    chart && chart.resize()
  })
})
</script>

<template>
  <div class="eeg-viewer">
    <div class="chart-controls">
      <el-button-group>
        <el-button size="small" @click="toggleTheme">
          切换主题
        </el-button>
        <el-button size="small" @click="toggleFullScreen">
          {{ isFullScreen ? '退出全屏' : '全屏' }}
        </el-button>
      </el-button-group>
    </div>
    
    <div ref="chartRef" class="chart-container"></div>
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

.chart-container {
  height: 500px;
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}
</style>
