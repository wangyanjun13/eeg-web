<script setup>
import { ref, onMounted, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  title: {
    type: String,
    default: '时频分析'
  },
  colorMap: {
    type: String,
    default: 'jet'
  }
});

const chartRef = ref(null);
let chart = null;

onMounted(() => {
  initChart();
});

watch(() => props.data, () => {
  updateChart();
}, { deep: true });

watch(() => props.colorMap, () => {
  updateChart();
});

function initChart() {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value);
    updateChart();
    
    window.addEventListener('resize', () => {
      chart.resize();
    });
  }
}

function updateChart() {
  if (!chart || !props.data || !props.data.times || !props.data.frequencies || !props.data.power) return;
  
  const times = props.data.times;
  const frequencies = props.data.frequencies;
  const power = props.data.power;
  
  // 将二维数组转换为echarts需要的格式
  const data = [];
  for (let i = 0; i < frequencies.length; i++) {
    for (let j = 0; j < times.length; j++) {
      data.push([j, i, power[i][j]]);
    }
  }
  
  // 确定颜色范围
  const min = Math.min(...power.flat());
  const max = Math.max(...power.flat());
  
  // 选择颜色映射
  let colorStops;
  if (props.colorMap === 'jet') {
    colorStops = [
      { offset: 0, color: '#00007F' },
      { offset: 0.25, color: '#0000FF' },
      { offset: 0.5, color: '#00FFFF' },
      { offset: 0.75, color: '#FFFF00' },
      { offset: 1, color: '#FF0000' }
    ];
  } else if (props.colorMap === 'viridis') {
    colorStops = [
      { offset: 0, color: '#440154' },
      { offset: 0.25, color: '#3B528B' },
      { offset: 0.5, color: '#21918C' },
      { offset: 0.75, color: '#5EC962' },
      { offset: 1, color: '#FDE725' }
    ];
  } else {
    // 默认蓝红色映射
    colorStops = [
      { offset: 0, color: '#0000FF' },
      { offset: 0.5, color: '#FFFFFF' },
      { offset: 1, color: '#FF0000' }
    ];
  }
  
  const option = {
    title: {
      text: props.title,
      left: 'center'
    },
    tooltip: {
      position: 'top',
      formatter: function(params) {
        const time = times[params.value[0]].toFixed(0);
        const freq = frequencies[params.value[1]].toFixed(1);
        const value = params.value[2].toFixed(2);
        return `时间: ${time}ms<br/>频率: ${freq}Hz<br/>功率: ${value}`;
      }
    },
    grid: {
      left: '3%',
      right: '7%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: times.map(t => t.toFixed(0)),
      name: '时间 (ms)',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        interval: Math.floor(times.length / 10),
        formatter: '{value} ms'
      }
    },
    yAxis: {
      type: 'category',
      data: frequencies.map(f => f.toFixed(1)),
      name: '频率 (Hz)',
      nameLocation: 'middle',
      nameGap: 40,
      axisLabel: {
        interval: Math.floor(frequencies.length / 10),
        formatter: '{value} Hz'
      }
    },
    visualMap: {
      min: min,
      max: max,
      calculable: true,
      realtime: false,
      inRange: {
        color: colorStops.map(stop => stop.color)
      },
      right: 0,
      top: 'center',
      text: [`最大值: ${max.toFixed(2)}`, `最小值: ${min.toFixed(2)}`],
      textStyle: {
        color: '#333'
      }
    },
    series: [
      {
        name: '时频图',
        type: 'heatmap',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };
  
  // 添加事件标记线
  if (props.data.events) {
    option.markLine = {
      silent: true,
      data: props.data.events.map(event => ({
        xAxis: times.findIndex(t => t >= event.time),
        name: event.name,
        lineStyle: {
          color: event.color || '#333',
          type: 'solid',
          width: 2
        },
        label: {
          formatter: event.name,
          position: 'insideEndTop'
        }
      }))
    };
  }
  
  chart.setOption(option);
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 500px;"></div>
</template> 