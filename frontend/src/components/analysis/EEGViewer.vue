<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useDebounce, useDebounceFn } from '@/composables/useDebounce'
import { useChannelPositions } from '@/composables/useChannelPositions' // 导入通道位置组合式函数
/*作用：EEG数据可视化组件
  参数：
    data: 包含EEG数据的对象
    timeRange: 时间范围，默认[0, 10]
    selectedChannels: 选中的通道，默认[]
*/

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
const channelSelectVisible = ref(false)
const localSelectedChannels = ref([])
const channelCompareVisible = ref(false)
const isSelectAll = computed(() => {
  return props.data?.channels && 
         localSelectedChannels.value.length === props.data.channels.length
})
const legendSelected = ref({}) // 存储图例选中状态
const isYAxisInverted = ref(false) // 纵坐标是否反转

// 使用通道位置组合式函数
const { 
  fetchElectrodePositions, 
  getChannelPosition, 
  isLoading: positionsLoading,
  error: positionsError,
  positionSource
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
          return `<span style="color: ${p.color}">${p.seriesName}</span><br/>时间: ${time} s<br/>振幅: ${value} μV`
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
    name: '振幅 (μV)',
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
const toggleChannelSelect = () => channelSelectVisible.value = true

// 全选或清空通道
const toggleSelectAll = () => {
  localSelectedChannels.value = isSelectAll.value 
    ? [] 
    : (props.data?.channels ? [...props.data.channels] : [])
}

// 确认通道选择
const confirmChannelSelect = () => {
  if (localSelectedChannels.value.length === 0) {
    ElMessage.warning('请至少选择一个通道')
    return
  }
  
  channelSelectVisible.value = false
  emit('update:selectedChannels', [...localSelectedChannels.value])
  nextTick(updateChart)
}

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

// 监听状态变化
watch(() => props.selectedChannels, (newVal) => {
  localSelectedChannels.value = [...newVal]
}, { immediate: true })

watch(() => channelSelectVisible.value, (newVal) => {
  if (!newVal) {
    localSelectedChannels.value = [...props.selectedChannels]
  }
})

// 合并数据变化监听
watch([() => props.data, () => props.timeRange, () => props.selectedChannels], () => {
  if (chart) updateChart()
}, { deep: true })

// 获取电极位置
const loadElectrodePositions = async () => {
  if (props.data?.dataset_id && props.data?.subject_id) {
    await fetchElectrodePositions(props.data.dataset_id, props.data.subject_id)
  }
}

// 生命周期
onMounted(() => {
  if (props.data) {
    initChart()
    chartRef.value.addEventListener('click', showChannelCompare)
    loadElectrodePositions() // 加载电极位置
  }
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
    
    <div ref="chartRef" class="chart-container"></div>
    
    <el-dialog v-model="channelSelectVisible" title="选择要显示的通道" width="50%">
      <div class="channel-select-header">
        <el-button size="small" type="primary" @click="toggleSelectAll">
          {{ isSelectAll ? '清空' : '全选' }}
        </el-button>
      </div>
      
      <!-- 添加头部轮廓和电极位置显示 -->
      <div v-if="positionSource !== 'none'" class="head-container">
        <div class="head-circle"></div>
        <div class="ear left-ear"></div>
        <div class="ear right-ear"></div>
        <div class="nose"></div>
        
        <!-- 使用小点标记电极位置 -->
        <div 
          v-for="(channel, index) in props.data?.channels" 
          :key="channel" 
          class="channel-marker"
          :class="{ 'selected': localSelectedChannels.includes(channel) }"
          :style="{
            left: `${getChannelPosition(channel, index, props.data?.channels.length).x * 100}%`,
            top: `${getChannelPosition(channel, index, props.data?.channels.length).y * 100}%`
          }"
          @click="localSelectedChannels.includes(channel) ? 
                  localSelectedChannels = localSelectedChannels.filter(ch => ch !== channel) : 
                  localSelectedChannels.push(channel)"
        >
          <span class="channel-label">{{ channel }}</span>
        </div>
      </div>
      
      <!-- 如果没有位置信息，显示常规复选框 -->
      <el-checkbox-group v-else v-model="localSelectedChannels" class="channel-grid">
        <el-checkbox v-for="channel in props.data?.channels" :key="channel" :value="channel">
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
    
    <el-dialog v-model="channelCompareVisible" title="通道数据对比" width="30%">
      <div class="channel-compare">
        <div class="time-info">当前时间: {{ getCurrentTime() }} s</div>
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
  height: 500px;
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.channel-select-header {
  margin-bottom: 10px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
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

/* 头部容器样式 */
.head-container {
  position: relative;
  width: 400px;
  height: 400px;
  margin: 0 auto 20px;
}

/* 头部轮廓 */
.head-circle {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid #ccc;
  top: 0;
  left: 0;
}

/* 耳朵 */
.ear {
  position: absolute;
  width: 30px;
  height: 60px;
  border: 2px solid #ccc;
  border-radius: 50%;
  top: 50%;
  transform: translateY(-50%);
}

.left-ear {
  left: -15px;
  border-right: none;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.right-ear {
  right: -15px;
  border-left: none;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

/* 鼻子 */
.nose {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid #ccc;
  border-radius: 50%;
  top: 0;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 通道标记样式 */
.channel-marker {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background-color: #409EFF;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 20;
  transition: all 0.2s;
}

/* 选中的通道标记 */
.channel-marker.selected {
  background-color: #67C23A;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.8);
  width: 16px;
  height: 16px;
}

/* 通道标签 - 悬停时显示 */
.channel-label {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.channel-marker:hover .channel-label {
  opacity: 1;
}
</style>
