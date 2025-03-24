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

// 图表引用和状态
const chartRef = ref(null)
let chart = null
const isFullScreen = ref(false)
const themeStyle = ref('light')
const channelSelectVisible = ref(false)
const localSelectedChannels = ref([])

// 初始化本地选中通道
watch(() => props.selectedChannels, (newVal) => {
  localSelectedChannels.value = [...newVal]
}, { immediate: true })

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
  
  // 对于大数据集，考虑数据抽样以提高性能
  const maxDataPoints = 5000 // 最大显示点数
  let skipFactor = 1
  
  // 计算当前数据点数
  const times = props.data.times
  const dataPointCount = times.length
  
  // 如果数据点过多，进行抽样
  if (dataPointCount > maxDataPoints) {
    skipFactor = Math.ceil(dataPointCount / maxDataPoints)
    console.log(`数据点过多(${dataPointCount})，每${skipFactor}个点取样一次`)
  }
  
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
      orient: 'horizontal',
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    toolbox: {
      feature: {
        saveAsImage: { title: '保存为图片' },
        dataZoom: { title: { zoom: '区域缩放', back: '还原缩放' } },
        restore: { title: '还原' }
      }
    },
    dataZoom: [
      {
        type: 'slider',
        show: true,
        xAxisIndex: [0],
        start: 0,
        end: 100
      },
      {
        type: 'inside',
        xAxisIndex: [0],
        start: 0,
        end: 100
      }
    ],
    xAxis: {
      type: 'value',
      name: '时间 (s)',
      nameLocation: 'middle',
      nameGap: 30,
      min: props.timeRange[0],
      max: props.timeRange[1]
    },
    yAxis: {
      type: 'value',
      name: '振幅 (μV)',
      nameLocation: 'middle',
      nameGap: 40
    },
    series: props.selectedChannels.map(channel => {
      const channelData = props.data.data[channel]
      
      // 在筛选数据时应用抽样
      const filteredData = []
      const filteredTimes = []
      
      // 在筛选数据时应用抽样
      for (let i = 0; i < times.length; i += skipFactor) {
        if (times[i] >= props.timeRange[0] && times[i] <= props.timeRange[1]) {
          filteredData.push(channelData[i])
          filteredTimes.push(times[i])
        }
      }
      
      // 组合数据
      const data = filteredTimes.map((time, idx) => [time, filteredData[idx]])
      
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
        props.timeRange[0] + (start / 100) * (props.timeRange[1] - props.timeRange[0]),
        props.timeRange[0] + (end / 100) * (props.timeRange[1] - props.timeRange[0])
      ]
      emit('update:timeRange', newTimeRange)
    }
  })
}

// 切换通道选择对话框
const toggleChannelSelect = () => {
  channelSelectVisible.value = !channelSelectVisible.value
}

// 确认通道选择
const confirmChannelSelect = () => {
  // 发出事件通知父组件更新选中的通道
  emit('update:selectedChannels', localSelectedChannels.value)
  channelSelectVisible.value = false
}

// 切换全屏
const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value
  
  if (isFullScreen.value) {
    // 全屏样式
    chartRef.value.style.position = 'fixed'
    chartRef.value.style.top = '0'
    chartRef.value.style.left = '0'
    chartRef.value.style.width = '100vw'
    chartRef.value.style.height = '100vh'
    chartRef.value.style.zIndex = '9999'
    chartRef.value.style.background = themeStyle.value === 'dark' ? '#333' : '#fff'
  } else {
    // 恢复正常样式
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
    <!-- 图表控制按钮 -->
    <div class="chart-controls">
      <el-button-group>
        <el-button size="small" @click="toggleChannelSelect">
          选择通道
        </el-button>
        <el-button size="small" @click="toggleTheme">
          切换主题
        </el-button>
        <el-button size="small" @click="toggleFullScreen">
          {{ isFullScreen ? '退出全屏' : '全屏' }}
        </el-button>
      </el-button-group>
    </div>
    
    <!-- 图表容器 -->
    <div ref="chartRef" class="chart-container"></div>
    
    <!-- 通道选择对话框 -->
    <el-dialog
      v-model="channelSelectVisible"
      title="选择要显示的通道"
      width="30%"
    >
      <el-checkbox-group v-model="localSelectedChannels">
        <el-checkbox 
          v-for="channel in props.data?.channels" 
          :key="channel" 
          :label="channel"
        >
          {{ channel }}
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="channelSelectVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmChannelSelect">确认</el-button>
        </span>
      </template>
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
  justify-content: flex-end; /* 控制按钮右对齐 */
  margin-bottom: 16px;
}

.chart-container {
  height: 500px; /* 图表默认高度 */
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); /* 阴影效果 */
  transition: all 0.3s ease; /* 平滑过渡效果 */
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}
</style>
