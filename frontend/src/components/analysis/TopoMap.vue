<script setup>
import { ref, onMounted, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  colorMap: {
    type: String,
    default: 'jet'
  },
  title: {
    type: String,
    default: ''
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
  if (!chart || !props.data || !props.data.positions || !props.data.values) return;
  
  const positions = props.data.positions;
  const values = props.data.values;
  
  // 创建头皮轮廓
  const scalpRadius = 0.5;
  const scalpPoints = [];
  for (let i = 0; i <= 360; i += 5) {
    const angle = (i * Math.PI) / 180;
    scalpPoints.push([
      scalpRadius * Math.cos(angle),
      scalpRadius * Math.sin(angle)
    ]);
  }
  
  // 创建耳朵和鼻子标记
  const nosePoint = [0, -0.55];
  const leftEarPoints = [
    [-0.55, 0],
    [-0.6, 0.1],
    [-0.58, 0],
  ];
  const rightEarPoints = [
    [0.55, 0],
    [0.6, 0.1],
    [0.58, 0],
  ];
  
  // 确定颜色范围
  const min = Math.min(...values);
  const max = Math.max(...values);
  
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
  } else if (props.colorMap === 'RdBu') {
    colorStops = [
      { offset: 0, color: '#053061' },
      { offset: 0.5, color: '#F7F7F7' },
      { offset: 1, color: '#67001F' }
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
      formatter: function(params) {
        if (params.seriesName === 'electrodes') {
          const index = params.dataIndex;
          const channelName = props.data.channels[index];
          const value = values[index].toFixed(2);
          return `${channelName}: ${value}`;
        }
        return '';
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
      text: [`最大值: ${max.toFixed(2)}`, `最小值: ${min.toFixed(2)}`],
      textStyle: {
        color: '#333'
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      top: '10%',
      bottom: '15%'
    },
    xAxis: {
      show: false,
      min: -0.7,
      max: 0.7,
      type: 'value'
    },
    yAxis: {
      show: false,
      min: -0.7,
      max: 0.7,
      type: 'value'
    },
    series: [
      {
        name: 'scalp',
        type: 'line',
        data: scalpPoints,
        symbol: 'none',
        lineStyle: {
          color: '#000',
          width: 2
        },
        z: 10
      },
      {
        name: 'nose',
        type: 'scatter',
        data: [nosePoint],
        symbol: 'triangle',
        symbolSize: 15,
        itemStyle: {
          color: '#000'
        },
        z: 10
      },
      {
        name: 'leftEar',
        type: 'line',
        data: leftEarPoints,
        symbol: 'none',
        lineStyle: {
          color: '#000',
          width: 2
        },
        z: 10
      },
      {
        name: 'rightEar',
        type: 'line',
        data: rightEarPoints,
        symbol: 'none',
        lineStyle: {
          color: '#000',
          width: 2
        },
        z: 10
      },
      {
        name: 'heatmap',
        type: 'heatmap',
        data: positions.map((pos, index) => [pos[0], pos[1], values[index]]),
        pointSize: 10,
        blurSize: 20,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      },
      {
        name: 'electrodes',
        type: 'scatter',
        data: positions.map((pos, index) => [pos[0], pos[1]]),
        symbol: 'circle',
        symbolSize: 5,
        itemStyle: {
          color: '#000',
          borderColor: '#fff',
          borderWidth: 1
        },
        z: 11
      }
    ]
  };
  
  chart.setOption(option);
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template>