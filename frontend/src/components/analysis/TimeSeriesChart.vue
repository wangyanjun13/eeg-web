<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
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
    
    // 优化resize处理，使用防抖
    let resizeTimer = null;
    window.addEventListener('resize', () => {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (chart) {
          chart.resize();
        }
      }, 100);
    });
  }
}

function updateChart() {
  if (!chart || !props.data || props.data.length === 0) return;
  
  // 确保图表已准备好
  nextTick(() => {
    // 重新调整图表大小，确保填充容器
    chart.resize();
    
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
          width: 1.5
        },
        emphasis: {
          lineStyle: {
            width: 2.5
          }
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
        left: '80px', // 增加左侧空间放置通道标签
        right: '4%',
        bottom: '3%',
        top: '3%',
        containLabel: false // 修改为false，确保轴标签不占用通道标签空间
      },
      xAxis: {
        type: 'value',
        name: '时间 (秒)',
        nameLocation: 'end',
        min: props.timeRange[0],
        max: props.timeRange[1],
        axisLabel: {
          showMinLabel: true,
          showMaxLabel: true
        }
      },
      yAxis: {
        type: 'value',
        name: '电压 (μV)',
        nameLocation: 'end',
        axisLabel: {
          formatter: function(value, index) {
            // 隐藏Y轴刻度值，只显示通道名称
            return '';
          }
        },
        // 添加通道名称标记
        axisPointer: {
          show: false
        }
      },
      series: series,
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          filterMode: 'none'
        }
      ],
      // 添加工具栏
      toolbox: {
        feature: {
          dataZoom: {
            yAxisIndex: 'none'
          },
          restore: {},
          saveAsImage: {}
        },
        right: 20
      }
    };
    
    chart.setOption(option);
    
    // 添加通道标签
    addChannelLabels();
  });
}

// 添加通道名称标签
function addChannelLabels() {
  if (!chart || !props.channels || props.channels.length === 0 || !chartRef.value) return;
  
  // 移除之前的标签
  const container = chartRef.value;
  const oldLabels = container.querySelectorAll('.channel-label');
  oldLabels.forEach(label => label.remove());
  
  // 获取图表区域信息
  const gridPos = chart.getModel().getComponent('grid').positionInfo;
  
  // 为每个通道添加标签 - 固定在左侧Y轴位置
  props.channels.forEach((channel, index) => {
    const offset = index * 50;
    const y = chart.convertToPixel('grid', [0, offset]);
    
    if (typeof y === 'number') {
      const label = document.createElement('div');
      label.className = 'channel-label';
      label.innerText = channel;
      
      // 固定位置设置 - 精确放置在Y轴左侧
      label.style.position = 'absolute';
      label.style.left = '0px'; // 固定在最左侧
      label.style.top = `${y - 9}px`; // 垂直对齐调整
      
      // 基本样式设置
      label.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
      label.style.padding = '2px 8px 2px 5px';
      label.style.borderRadius = '0 3px 3px 0';
      label.style.fontSize = '12px';
      label.style.fontWeight = '500';
      label.style.color = '#606266';
      label.style.textAlign = 'left';
      label.style.zIndex = '10';
      label.style.boxShadow = '1px 1px 2px rgba(0,0,0,0.1)';
      label.style.borderLeft = '2px solid var(--button-use)';
      
      // 添加通道索引编号
      const channelNumber = document.createElement('span');
      channelNumber.style.color = '#999';
      channelNumber.style.fontSize = '9px';
      channelNumber.style.marginLeft = '3px';
      channelNumber.innerText = `#${index+1}`;
      label.appendChild(channelNumber);
      
      // 鼠标悬停高亮对应线条
      label.addEventListener('mouseover', () => {
        chart.dispatchAction({
          type: 'highlight',
          seriesIndex: index
        });
        label.style.color = 'var(--button-use)';
        label.style.fontWeight = 'bold';
        label.style.backgroundColor = 'rgba(232, 244, 255, 0.95)';
      });
      
      label.addEventListener('mouseout', () => {
        chart.dispatchAction({
          type: 'downplay',
          seriesIndex: index
        });
        label.style.color = '#606266';
        label.style.fontWeight = '500';
        label.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
      });
      
      container.appendChild(label);
    }
  });
}

// 监听窗口大小变化时更新标签位置
window.addEventListener('resize', () => {
  // 使用防抖确保不会频繁触发
  if (chart && chartRef.value) {
    clearTimeout(window.channelLabelTimer);
    window.channelLabelTimer = setTimeout(() => {
      addChannelLabels();
    }, 200);
  }
});
</script>

<template>
  <div ref="chartRef" class="time-series-chart"></div>
</template>

<style scoped>
.time-series-chart {
  width: 100%;
  height: 100%;
  min-height: 500px;
  position: relative; /* 添加相对定位以支持通道标签的绝对定位 */
}

/* 通道标签样式不再需要，样式已在addChannelLabels函数中直接设置 */
/* 在小屏幕上设置最小高度 */
@media (max-width: 1200px) {
  .time-series-chart {
    min-height: 450px;
  }
}
</style> 