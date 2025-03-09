<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: Object,
  selectedChannels: Array
})

const chartRef = ref(null)
let chart = null

onMounted(() => {
  chart = echarts.init(chartRef.value)
})

watch(() => props.data, (newData) => {
  if (!newData || !chart) return
  
  const option = {
    title: { text: 'EEG数据可视化' },
    tooltip: { trigger: 'axis' },
    legend: { data: props.selectedChannels },
    xAxis: { type: 'value', name: '时间 (s)' },
    yAxis: { type: 'value', name: '振幅' },
    series: props.selectedChannels.map(channel => ({
      name: channel,
      type: 'line',
      data: newData.data[channel]
    }))
  }
  
  chart.setOption(option)
}, { deep: true })
</script>

<template>
  <div ref="chartRef" style="height: 500px;"></div>
</template> 
<style scoped>
.echarts {
  width: 100%;
  height: 100%;
}
</style>
