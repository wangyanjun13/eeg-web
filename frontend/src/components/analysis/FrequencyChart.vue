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
    default: '频谱分析'
  },
  logScale: {
    type: Boolean,
    default: false
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

watch(() => props.logScale, () => {
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
  if (!chart || !props.data || !props.data.frequencies || !props.data.channels) return;
  
  const frequencies = props.data.frequencies;
  const channels = props.data.channels;
  
  const series = channels.map(channel => {
    return {
      name: channel.name,
      type: 'line',
      data: channel.values.map((value, index) => {
        // 如果使用对数刻度，对值进行转换
        return [frequencies[index], props.logScale ? Math.log10(value) : value];
      }),
      showSymbol: false,
      smooth: true
    };
  });
  
  // 添加频段标记
  const markAreas = [];
  if (props.data.bands) {
    props.data.bands.forEach(band => {
      markAreas.push([
        { xAxis: band.range[0], name: band.name, itemStyle: { color: band.color || 'rgba(0, 0, 0, 0.1)' } },
        { xAxis: band.range[1] }
      ]);
    });
  }
  
  const option = {
    title: {
      text: props.title,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const freq = params[0].value[0].toFixed(1);
        let result = `频率: ${freq}Hz<br/>`;
        
        params.forEach(param => {
          let value = param.value[1];
          // 如果使用对数刻度，将显示值转换回原始值
          if (props.logScale) {
            value = Math.pow(10, value).toFixed(2);
            result += `${param.seriesName}: ${value} (log)<br/>`;
          } else {
            value = value.toFixed(2);
            result += `${param.seriesName}: ${value}<br/>`;
          }
        });
        
        return result;
      }
    },
    legend: {
      data: channels.map(c => c.name),
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '频率 (Hz)',
      axisLabel: {
        formatter: '{value} Hz'
      }
    },
    yAxis: {
      type: 'value',
      name: props.logScale ? '功率 (log)' : '功率',
      scale: true
    },
    series: series,
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none'
      },
      {
        type: 'slider',
        xAxisIndex: 0,
        filterMode: 'none'
      }
    ],
    markArea: {
      silent: true,
      data: markAreas
    }
  };
  
  chart.setOption(option);
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template> 