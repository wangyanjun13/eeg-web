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
  
  // 简化颜色映射：使用固定颜色数组而不是动态添加colorStops
  let colors = ['#00007F', '#0000FF', '#00FFFF', '#FFFF00', '#FF0000']; // 默认jet
  
  if (props.colorMap === 'viridis') {
    colors = ['#440154', '#433982', '#30678D', '#218F8B', '#36B677', '#8ED542', '#FDE725'];
  } else if (props.colorMap === 'plasma') {
    colors = ['#0D0887', '#5B02A3', '#9A179B', '#CB4678', '#EB7852', '#FBB32F', '#F0F921'];
  } else if (props.colorMap === 'inferno') {
    colors = ['#000004', '#320A5A', '#781C6D', '#BC3754', '#ED6925', '#FBB32F', '#FCFEA4'];
  }
  
  // 准备插值数据点
  const interpolationData = [];
  try {
    // 从电极位置和值创建插值数据
    for (let i = 0; i < positions.length; i++) {
      if (positions[i] && positions[i].length === 2 && !isNaN(values[i])) {
        interpolationData.push({
          value: [positions[i][0], positions[i][1], values[i]]
        });
      }
    }
  } catch (e) {
    console.error('准备插值数据时出错:', e);
  }
  
  // 创建热力图数据点
  const resolution = props.data.interpolation?.resolution || 64;
  const gridStep = 1.4 / resolution;
  const gridData = [];
  
  // 使用电极位置作为散点图数据，使用大小和颜色表示值
  const pointData = positions.map((pos, idx) => {
    return {
      value: [pos[0], pos[1], values[idx]],
      symbolSize: Math.max(5, Math.min(20, 5 + values[idx] / max * 15)), // 根据值调整大小
    };
  });
  
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
        } else if (params.seriesName === 'values') {
          return `值: ${params.value[2].toFixed(2)}`;
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
        color: colors
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
      bottom: '15%',
      containLabel: true
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
        name: 'values',
        type: 'scatter',
        data: pointData,
        large: true,
        largeThreshold: 500,
        dimensions: ['x', 'y', 'value'],
        itemStyle: {
          opacity: 0.7
        },
        encode: {
          tooltip: 2
        }
      },
      {
        name: 'electrodes',
        type: 'scatter',
        data: positions.map((pos, index) => [pos[0], pos[1]]),
        symbol: 'circle',
        symbolSize: 5,
        itemStyle: {
          color: '#fff',
          borderColor: '#000',
          borderWidth: 1
        },
        z: 11
      }
    ]
  };
  
  try {
    chart.setOption(option);
  } catch (e) {
    console.error('设置图表选项时出错:', e);
  }
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template>