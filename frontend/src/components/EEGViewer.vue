<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue'
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

// 图表状态
const chartRef = ref(null)
let chart = null
const isFullScreen = ref(false)
const themeStyle = ref('light')
const channelSelectVisible = ref(false)
const localSelectedChannels = ref([])
const channelCompareVisible = ref(false)

// 初始化本地选中通道
watch(() => props.selectedChannels, (newVal) => {
  localSelectedChannels.value = newVal.length ? [...newVal] : props.data.channels?.slice(0, 5) || []
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
  
  const series = props.selectedChannels.map((channel, index) => ({
    name: channel,
    type: 'line',
    showSymbol: true,
    symbolSize: 5,     // 增大数据点以便于交互
    symbol: 'circle',  // 使用圆形数据点
    sampling: 'lttb',  // 使用LTTB采样提高性能
    data: props.data.data[channel]?.map((value, index) => [
      props.data.times[index],
      value
    ]).filter(point => 
      point[0] >= props.timeRange[0] && 
      point[0] <= props.timeRange[1]
    ) || [],
    animationDuration: 0,
    emphasis: {
      focus: 'none'  // 不淡化其他序列
    },
    itemStyle: {
      color: chart?.getOption()?.series?.[index]?.itemStyle?.color,
      opacity: 0  // 默认不可见
    },
    tooltip: {
      formatter: (params) => {
        const time = params.data[0]?.toFixed(3) || params.data[0]
        const value = params.data[1]?.toFixed(3) || params.data[1]
        return `<span style="color: ${params.color}">${params.seriesName}</span><br/>时间: ${time} s<br/>振幅: ${value} μV`
      }
    }
  }))

  const option = {
    tooltip: {
      show: true,
      trigger: 'item',  // 只在数据点上触发
      axisPointer: {
        type: 'cross',
        snap: true,
        label: {
          show: true  // 显示坐标轴标签
        }
      },
      showContent: false,  // 默认不显示内容
      position: function (pos, params, el, elRect, size) {
        return [pos[0] + 10, pos[1] - 10]  // 位于鼠标右上方
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
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
  }

  chart.setOption(option)
  
  // 添加事件处理
  chart.off('mouseover')
  chart.off('mouseout')
  
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
    chart.setOption({
      tooltip: {
        showContent: false
      }
    })
  })
}

// 获取当前时间点
const getCurrentTime = () => {
  if (!chart || !props.data?.times) return 0
  
  // 获取当前鼠标位置对应的时间
  const axisPointer = chart.getOption().axisPointer
  if (axisPointer && axisPointer[0]?.value) {
    return axisPointer[0].value.toFixed(3)
  }
  
  // 如果没有轴指针位置，则使用当前显示范围的中点
  const xAxis = chart.getOption().xAxis[0]
  if (xAxis) {
    const min = xAxis.min || props.timeRange[0]
    const max = xAxis.max || props.timeRange[1]
    return ((min + max) / 2).toFixed(3)
  }
  
  return props.timeRange[0].toFixed(3)
}

// 通道数据对比窗口内容
const channelCompareContent = computed(() => {
  if (!props.data || !props.selectedChannels.length) return []
  
  const currentTime = getCurrentTime()
  // 找到最接近当前时间的数据点索引
  const timeIndex = props.data.times.findIndex(t => t >= currentTime) || 0
  
  return props.selectedChannels.map((channel, index) => {
    const value = props.data.data[channel]?.[timeIndex]?.toFixed(3) || 0
    const color = chart?.getOption().series[index]?.itemStyle?.color || '#000'
    return {
      channel,
      value,
      color
    }
  })
})

// 切换通道选择对话框
const toggleChannelSelect = () => {
  channelSelectVisible.value = !channelSelectVisible.value
}

// 通道数据对比窗口
const showChannelCompare = (event) => {
  if (event.detail === 2) { // 双击事件
    channelCompareVisible.value = true
  }
}

// 确认通道选择
const confirmChannelSelect = () => {
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

// 添加点击事件控制状态
const isShowingAllChannels = ref(false)

// 监听props变化
watch(() => props.data, initChart, { deep: true })
watch(() => props.timeRange, updateChart, { deep: true })
watch(() => props.selectedChannels, updateChart, { deep: true })

// 生命周期钩子
onMounted(() => {
  if (props.data) {
    initChart()
    
    // 添加双击事件监听
    chartRef.value.addEventListener('click', showChannelCompare)
  }
  
  chart.on('click', () => {
    isShowingAllChannels.value = !isShowingAllChannels.value
  })
})

onBeforeUnmount(() => {
  if (chart) {
    chart.dispose()
    chartRef.value?.removeEventListener('click', showChannelCompare)
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
    
    <!-- 通道对比窗口 -->
    <el-dialog
      v-model="channelCompareVisible"
      title="通道数据对比"
      width="30%"
      :modal-append-to-body="true"
      :append-to-body="true"
    >
      <div class="channel-compare">
        <div class="time-info">当前时间: {{ getCurrentTime() }} s</div>
        <div 
          v-for="item in channelCompareContent" 
          :key="item.channel"
          class="channel-item"
        >
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
