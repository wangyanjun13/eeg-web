<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

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
const isSelectAll = ref(false)
const legendSelected = ref({}) // 存储图例选中状态

// 图表初始化和更新
const initChart = () => {
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value, themeStyle.value)
  window.addEventListener('resize', () => chart?.resize())
  
  // 添加图例点击事件
  chart.on('legendselectchanged', (params) => {
    legendSelected.value = {...legendSelected.value, ...params.selected}
  })
  
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chart || !props.data?.data) return
  
  const series = props.selectedChannels.map((channel, index) => ({
    name: channel,
    type: 'line',
    showSymbol: true,
    symbolSize: 5,
    symbol: 'circle',
    sampling: 'lttb',
    data: props.data.data[channel]?.map((value, index) => [
      props.data.times[index],
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

  // 准备图例选中状态
  const legendSelStatus = {}
  props.selectedChannels.forEach(channel => {
    // 如果之前有状态，使用之前的状态，否则默认为显示
    legendSelStatus[channel] = legendSelected.value[channel] !== undefined 
      ? legendSelected.value[channel] 
      : true
  })
  
  chart.setOption({
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      top: 0,
      left: 'center',
      width: '90%',
      data: props.selectedChannels,
      textStyle: {
        fontSize: 12
      },
      pageButtonItemGap: 5,
      pageButtonPosition: 'end',
      pageIconSize: 12,
      tooltip: {
        show: true
      },
      selectedMode: true,
      selected: legendSelStatus
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
      top: '50px', // 增加顶部空间给图例
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
      name: '振幅 (μV)'
    },
    dataZoom: [{
      type: 'inside',
      start: 0,
      end: 100
    }],
    series
  }, true) // 强制不合并

  // 事件处理
  chart.off('mouseover').off('mouseout')
  
  chart.on('mouseover', 'series', (params) => {
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
  })
  
  chart.on('mouseout', 'series', () => {
    chart.setOption({ tooltip: { showContent: false } })
  })
}

// 获取当前时间点
const getCurrentTime = () => {
  if (!chart || !props.data?.times) return 0
  const axisPointer = chart.getOption().axisPointer
  if (axisPointer?.[0]?.value) return axisPointer[0].value
  const xAxis = chart.getOption().xAxis[0]
  return xAxis ? ((xAxis.min || props.timeRange[0]) + (xAxis.max || props.timeRange[1])) / 2 : props.timeRange[0]
}

// 通道选择相关功能
const updateSelectAllState = () => {
  isSelectAll.value = props.data?.channels && 
                      localSelectedChannels.value.length === props.data.channels.length &&
                      props.data.channels.every(ch => localSelectedChannels.value.includes(ch))
}

// 全选或清空
const toggleSelectAll = () => {
  if (isSelectAll.value) {
    // 清空选择
    localSelectedChannels.value = []
  } else {
    // 全选并初始化图例状态
    localSelectedChannels.value = props.data?.channels ? [...props.data.channels] : []
    
    // 如果是全选操作，将所有通道的图例状态设为显示
    if (props.data?.channels && props.data.channels.length > 0) {
      const newLegendStatus = {}
      props.data.channels.forEach(channel => {
        newLegendStatus[channel] = true
      })
      // 合并现有状态
      legendSelected.value = {...legendSelected.value, ...newLegendStatus}
    }
  }
  isSelectAll.value = !isSelectAll.value
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

// 确认通道选择
const confirmChannelSelect = () => {
  if (localSelectedChannels.value.length === 0) {
    ElMessage.warning('请至少选择一个通道')
    return
  }
  
  // 先关闭对话框
  channelSelectVisible.value = false
  
  // 确保更新父组件的选中通道
  const newSelectedChannels = [...localSelectedChannels.value]
  
  // 清理不再需要的图例状态
  const newLegendSelected = {}
  Object.keys(legendSelected.value).forEach(key => {
    if (newSelectedChannels.includes(key)) {
      newLegendSelected[key] = legendSelected.value[key]
    }
  })
  
  // 对于新选的通道，默认显示
  newSelectedChannels.forEach(channel => {
    if (newLegendSelected[channel] === undefined) {
      newLegendSelected[channel] = true
    }
  })
  
  // 更新图例状态
  legendSelected.value = newLegendSelected
  
  // 更新选中通道
  emit('update:selectedChannels', newSelectedChannels)
  
  // 强制刷新图表
  nextTick(updateChart)
}

// 打开通道选择对话框
const toggleChannelSelect = () => {
  channelSelectVisible.value = true
}

// 打开对话框时初始化选择状态
const initChannelSelect = () => {
  localSelectedChannels.value = [...props.selectedChannels]
  updateSelectAllState()
}

// 全屏切换
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
  
  return props.selectedChannels.map((channel, index) => {
    const value = props.data.data[channel]?.[timeIndex]?.toFixed(3) || 0
    return {
      channel,
      value,
      color: chart?.getOption()?.series?.[index]?.itemStyle?.color || '#000'
    }
  })
})

// 监听
watch(() => props.selectedChannels, (newVal) => {
  localSelectedChannels.value = [...newVal]
  if (channelSelectVisible.value) {
    updateSelectAllState()
  }
}, { immediate: true })

// 监听本地选择通道变化
watch(() => localSelectedChannels.value, () => {
  if (channelSelectVisible.value && props.data?.channels) {
    updateSelectAllState()
  }
}, { deep: true })

// 监听对话框关闭
watch(() => channelSelectVisible.value, (newVal) => {
  if (!newVal) {
    localSelectedChannels.value = [...props.selectedChannels]
    updateSelectAllState()
  }
})

// 图表相关监听
watch([() => props.data, () => props.timeRange, () => props.selectedChannels], () => {
  if (chart) updateChart()
}, { deep: true })

// 生命周期
onMounted(() => {
  if (props.data) {
    initChart()
    chartRef.value.addEventListener('click', showChannelCompare)
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
    
    <div ref="chartRef" class="chart-container"></div>
    
    <el-dialog v-model="channelSelectVisible" title="选择要显示的通道" width="50%" @open="initChannelSelect">
      <div class="channel-select-header">
        <el-button size="small" type="primary" @click="toggleSelectAll">
          {{ isSelectAll ? '清空' : '全选' }}
        </el-button>
      </div>
      <el-checkbox-group v-model="localSelectedChannels" class="channel-grid">
        <el-checkbox v-for="channel in props.data?.channels" :key="channel" :label="channel">
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
</style>
