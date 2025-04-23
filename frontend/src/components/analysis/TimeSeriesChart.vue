<script setup>
import { ref, onMounted, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  data: {
    type: Array,
    required: true
  },
  channels: {
    type: Array,
    default: () => []
  },
  timeRange: {
    type: Array,
    default: () => [0, 10]
  },
  sampling: {
    type: Number,
    default: 256
  }
});

const emit = defineEmits(['timePointSelected']);

const chartRef = ref(null);
let chart = null;

onMounted(() => {
  initChart();
});

watch(() => props.data, () => {
  updateChart();
}, { deep: true });

watch(() => props.channels, () => {
  updateChart();
}, { deep: true });

watch(() => props.timeRange, () => {
  updateChart();
}, { deep: true });

function initChart() {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value);
    chart.on('click', (params) => {
      emit('timePointSelected', params.value[0]);
    });
    updateChart();
    
    window.addEventListener('resize', () => {
      chart.resize();
    });
  }
}

function updateChart() {
  if (!chart || !props.data || props.data.length === 0) return;
  
  const series = props.channels.map((channel, index) => {
    // 计算偏移量，使不同通道的数据在图表上分开显示
    const offset = index * 50;
    
    return {
      name: channel,
      type: 'line',
      data: props.data.filter(d => d.channel === channel).map(d => [d.time, d.value + offset]),
      showSymbol: false,
      animation: false,
      lineStyle: {
        width: 1
      }
    };
  });
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const time = params[0].value[0].toFixed(3);
        let result = `时间: ${time}s<br/>`;
        params.forEach(param => {
          const value = (param.value[1] - param.seriesIndex * 50).toFixed(2);
          result += `${param.seriesName}: ${value}μV<br/>`;
        });
        return result;
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
      name: '时间 (秒)',
      min: props.timeRange[0],
      max: props.timeRange[1]
    },
    yAxis: {
      type: 'value',
      name: '振幅 (μV)',
      axisLabel: {
        formatter: function(value, index) {
          // 隐藏Y轴刻度值，只显示通道名称
          return '';
        }
      }
    },
    series: series,
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none'
      }
    ]
  };
  
  chart.setOption(option);
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template> 