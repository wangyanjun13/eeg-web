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
      if (chart) {
        chart.resize();
      }
    });
  }
}

function updateChart() {
  if (!chart || !props.data) return;
  
  try {
    console.log('更新时频图表，数据:', {
      hasData: !!props.data,
      hasTimes: !!props.data.times,
      hasFreqs: !!props.data.frequencies,
      hasPower: !!props.data.power,
      powerType: props.data.power ? typeof props.data.power : 'undefined'
    });
    
    // 检查数据格式
    if (!props.data.times || !Array.isArray(props.data.times) || props.data.times.length === 0 || 
        !props.data.frequencies || !Array.isArray(props.data.frequencies) || props.data.frequencies.length === 0 || 
        !props.data.power || !Array.isArray(props.data.power) || props.data.power.length === 0) {
      console.warn('时频数据格式不正确或为空', props.data);
      
      // 显示一个空图表或错误提示
      chart.setOption({
        title: {
          text: '数据格式不正确或为空',
          left: 'center',
          textStyle: {
            color: '#f56c6c',
            fontSize: 16
          }
        },
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '请检查时频数据是否包含有效的times、frequencies和power数组',
            fill: '#999',
            fontSize: 14
          }
        }
      }, true);
      return;
    }
    
    const times = props.data.times;
    const frequencies = props.data.frequencies;
    let power = props.data.power;
    
    // 检查power数组的维度
    const is3D = power.length > 0 && Array.isArray(power[0]) && 
                power[0].length > 0 && Array.isArray(power[0][0]);
                
    if (is3D) {
      console.log('检测到三维功率数据 (通道x频率x时间)，使用第一个通道');
      // 使用第一个通道的数据
      power = power[0];
    } else if (power.length > 0 && !Array.isArray(power[0])) {
      console.warn('功率数据格式不正确，应为二维数组 [频率][时间]', power);
      
      chart.setOption({
        title: {
          text: '功率数据格式不正确',
          left: 'center',
          textStyle: {
            color: '#f56c6c',
            fontSize: 16
          }
        }
      }, true);
      return;
    }
    
    // 检查power数组的维度与frequencies和times长度是否匹配
    if (power.length !== frequencies.length) {
      console.warn(`功率数组第一维长度(${power.length})与频率数组长度(${frequencies.length})不匹配`);
    }
    
    if (power.length > 0 && power[0].length !== times.length) {
      console.warn(`功率数组第二维长度(${power[0].length})与时间点数组长度(${times.length})不匹配`);
    }
    
    // 将二维数组转换为echarts需要的格式
    const data = [];
    for (let i = 0; i < frequencies.length; i++) {
      if (i >= power.length) continue; // 防止越界
      for (let j = 0; j < times.length; j++) {
        if (j >= power[i].length) continue; // 防止越界
        // 确保值有效
        const value = isNaN(power[i][j]) ? 0 : power[i][j];
        data.push([j, i, value]);
      }
    }
    
    if (data.length === 0) {
      console.warn('转换后的数据为空');
      
      chart.setOption({
        title: {
          text: '无有效数据点',
          left: 'center',
          textStyle: {
            color: '#f56c6c',
            fontSize: 16
          }
        }
      }, true);
      return;
    }
    
    // 确定颜色范围 - 使用安全的方式计算
    let min = 0, max = 1;
    try {
      // 从数据点中提取值
      const values = data.map(item => item[2]).filter(v => !isNaN(v) && isFinite(v));
      if (values.length > 0) {
        min = Math.min(...values);
        max = Math.max(...values);
        
        // 避免min和max相等
        if (min === max) {
          min = max - 1;
        }
      }
      console.log(`功率值范围: ${min.toFixed(2)} - ${max.toFixed(2)}`);
    } catch (e) {
      console.warn('计算功率范围出错', e);
    }
    
    // 采用简化版配置，减少可能的错误
    const option = {
      animation: false,
      title: {
        text: props.title,
        left: 'center'
      },
      tooltip: {
        position: 'top',
        formatter: function(params) {
          const timeIdx = params.value[0];
          const freqIdx = params.value[1];
          
          // 安全获取时间和频率
          const timeValue = timeIdx < times.length ? times[timeIdx] : 0;
          const freq = freqIdx < frequencies.length ? frequencies[freqIdx].toFixed(1) : '0';
          const value = params.value[2].toFixed(2);
          
          // 时间单位转换
          const timeUnit = Math.abs(timeValue) > 1 ? 'ms' : 's';
          const timeDisplay = timeUnit === 's' ? timeValue.toFixed(2) : (timeValue * 1000).toFixed(0);
          
          return `时间: ${timeDisplay}${timeUnit}<br/>频率: ${freq}Hz<br/>功率: ${value}`;
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
        data: times.map(t => {
          // 根据数值大小决定单位
          if (Math.abs(t) > 1) {
            return `${t.toFixed(0)}ms`;
          } else {
            return `${t.toFixed(2)}s`;
          }
        }),
        name: '时间',
        nameLocation: 'middle',
        nameGap: 30,
        axisLabel: {
          interval: Math.floor(times.length / 10),
          rotate: 30
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
        // 使用固定的颜色数组，避免生成问题
        inRange: {
          color: ['#00007F', '#0000FF', '#00FFFF', '#FFFF00', '#FF0000']
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
    
    // 添加事件标记线 - 移动到外部添加
    let markLines = [];
    if (props.data.events && Array.isArray(props.data.events) && props.data.events.length > 0) {
      props.data.events.forEach(event => {
        // 找到最接近的时间点索引
        let timeValue = event.time || 0;
        // 根据时间单位转换
        if (typeof timeValue === 'number' && Math.abs(times[0]) <= 1) {
          // 如果时间是以秒为单位的，但事件时间是毫秒，则转换
          if (timeValue > 100) {
            timeValue = timeValue / 1000;
          }
        }
        
        const timeIndex = times.findIndex(t => t >= timeValue);
        if (timeIndex >= 0) {
          markLines.push({
            xAxis: timeIndex,
            name: event.name || '事件',
            lineStyle: {
              color: event.color || '#333',
              type: 'solid',
              width: 2
            },
            label: {
              formatter: event.name || '事件',
              position: 'insideEndTop',
              fontSize: 12,
              color: event.color || '#333'
            }
          });
        }
      });
    }
    
    // 如果有事件标记线，再添加到选项中
    if (markLines.length > 0) {
      option.series[0].markLine = {
        silent: true,
        data: markLines
      };
    }
    
    // 清理并重置图表
    try {
      // 使用dispose销毁后重建图表，解决某些渲染问题
      if (chart) {
        chart.dispose();
      }
      chart = echarts.init(chartRef.value);
      chart.setOption(option, true);
      console.log('时频图表更新完成');
    } catch (err) {
      console.error('重建图表失败:', err);
      // 尝试使用最简单的配置
      if (chart) {
        try {
          const simpleOption = {
            title: {
              text: props.title,
              left: 'center'
            },
            series: [{
              type: 'heatmap',
              data: data
            }]
          };
          chart.setOption(simpleOption, true);
        } catch (finalError) {
          console.error('使用简化选项也失败:', finalError);
        }
      }
    }
  } catch (e) {
    console.error('更新时频图出错:', e);
    // 显示错误信息
    if (chart) {
      chart.dispose();
      chart = echarts.init(chartRef.value);
      chart.setOption({
        title: {
          text: '图表更新出错',
          left: 'center',
          textStyle: {
            color: '#f56c6c',
            fontSize: 16
          }
        },
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: e.message || '未知错误',
            fill: '#999',
            fontSize: 14
          }
        }
      }, true);
    }
  }
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 500px;"></div>
</template> 