<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useDebounce, useDebounceFn } from '@/composables/useDebounce'
import { useChannelPositions } from '@/composables/useChannelPositions' // 导入通道位置组合式函数
// 作用：EEG数据可视化组件
// 参数：
//   data: 包含EEG数据的对象
//   timeRange: 时间范围，默认[0, 10]
//   selectedChannels: 选中的通道，默认[]

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

// 核心状态
const chartRef = ref(null)
let chart = null
const isFullScreen = ref(false)
const themeStyle = ref('light')
const channelCompareVisible = ref(false)
const legendSelected = ref({}) // 存储图例选中状态
const isYAxisInverted = ref(false) // 纵坐标是否反转

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

// 图表初始化和更新
const initChart = () => {
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value, themeStyle.value)
  
  // 事件监听统一设置
  chart.on('legendselectchanged', ({selected}) => legendSelected.value = {...legendSelected.value, ...selected})
  chart.on('mouseover', 'series', handleSeriesMouseover)
  chart.on('mouseout', 'series', () => chart.setOption({tooltip: {showContent: false}}))
  
  window.addEventListener('resize', () => chart?.resize())
  updateChart()
}

// 鼠标悬停处理
const handleSeriesMouseover = (params) => {
  if (params.componentType === 'series') {
    chart.setOption({
      tooltip: {
        showContent: true,
        formatter: (p) => {
          const time = p.data[0]?.toFixed(3) || p.data[0]
          const value = p.data[1]?.toFixed(3) || p.data[1]
          return `<span style="color: ${p.color}">${p.seriesName}</span><br/>时间: ${time} s<br/>电压: ${value} μV`
        }
      }
    })
  }
}

// 生成图表配置
const getChartOption = (series, legendStatus) => ({
  legend: {
    type: 'scroll',
    orient: 'horizontal',
    top: 0,
    left: 'center',
    width: '90%',
    data: props.selectedChannels,
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
  xAxis: {
    type: 'value',
    name: '时间 (s)',
    min: props.timeRange[0],
    max: props.timeRange[1]
  },
  yAxis: {
    type: 'value',
    name: '电压 (μV)',
    nameLocation: 'middle',
    nameGap: 40,
    nameRotate: 90,
    inverse: isYAxisInverted.value
  },
  dataZoom: [{
    type: 'inside',
    start: 0,
    end: 100
  }],
  series
})

// 使用防抖函数优化图表更新
const debouncedUpdateChart = useDebounceFn(() => {
  if (!chart || !props.data) return
  
  // 原updateChart函数的内容
  const series = props.selectedChannels.map((channel, index) => ({
    name: channel,
    type: 'line',
    showSymbol: true,
    symbolSize: 5,
    symbol: 'circle',
    sampling: 'lttb',
    data: props.data.data[channel]?.map((value, idx) => [
      props.data.times[idx],
      value
    ]).filter(point => 
      point[0] >= props.timeRange[0] && 
      point[0] <= props.timeRange[1]
    ) || [],
    animationDuration: 0,
    emphasis: { focus: 'none' },
    itemStyle: {
      color: chart?.getOption()?.series?.[index]?.itemStyle?.color,
      opacity: 0
    }
  }))

  // 准备图例状态，使用现有状态或默认为显示
  const legendStatus = props.selectedChannels.reduce((status, channel) => {
    status[channel] = legendSelected.value[channel] !== undefined 
      ? legendSelected.value[channel] 
      : true
    return status
  }, {})
  
  // 设置图表选项
  chart.setOption(getChartOption(series, legendStatus), true)
}, 100)

// 替换原来的updateChart函数调用为防抖版本
const updateChart = () => {
  debouncedUpdateChart()
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
  openChannelSelect(
    props.selectedChannels, 
    props.data?.channels || [], 
    (selected) => {
      emit('update:selectedChannels', selected)
      nextTick(updateChart)
    }
  )
}

// 通道比较数据
const channelCompareContent = computed(() => {
  if (!props.data || !props.selectedChannels.length) return []
  
  const currentTime = getCurrentTime()
  const timeIndex = props.data.times.findIndex(t => t >= currentTime)
  
  return props.selectedChannels.map((channel, index) => ({
    channel,
    value: props.data.data[channel]?.[timeIndex]?.toFixed(3) || 0,
    color: chart?.getOption()?.series?.[index]?.itemStyle?.color || '#000'
  }))
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
        <el-button size="small" @click="toggleChannelSelect">选择通道</el-button>
        <el-button size="small" @click="toggleTheme">切换主题</el-button>
        <el-button size="small" @click="toggleFullScreen">
          {{ isFullScreen ? '退出全屏' : '全屏' }}
        </el-button>
      </el-button-group>
    </div>
    
    <div class="coordinate-controls">
      <el-tooltip content="反转纵坐标轴（负值向上显示）" placement="top">
        <el-button 
          type="primary" 
          :plain="!isYAxisInverted" 
          size="small" 
          @click="toggleYAxisDirection"
          class="invert-button"
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
    <el-dialog v-model="channelCompareVisible" title="通道数据对比" width="30%">
      <div class="channel-compare">
        <div class="time-info">当前时间: {{ getCurrentTime().toFixed(3) }} s</div>
        <div v-for="item in channelCompareContent" :key="item.channel" class="channel-item">
          <span :style="{ color: item.color }">{{ item.channel }}</span>: {{ item.value }} μV
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
