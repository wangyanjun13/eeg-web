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
      if (chart) {
        chart.resize();
      }
    });
  }
}

function updateChart() {
  if (!chart || !props.data) return;
  
  try {
    // 检查数据格式
    if (!props.data.frequencies || !Array.isArray(props.data.frequencies) || 
        !props.data.powers || typeof props.data.powers !== 'object') {
      console.warn('频谱数据格式不正确', props.data);
      // 显示一个空图表或错误提示
      chart.setOption({
        title: {
          text: '数据格式不正确',
          left: 'center',
          textStyle: {
            color: '#999',
            fontSize: 14
          }
        }
      }, true);
      return;
    }
    
    // 安全提取频率数组
    const frequencies = props.data.frequencies.map(f => 
      typeof f === 'number' && !isNaN(f) ? f : 0
    );
    
    // 处理通道数据 - 使用更健壮的方式
    let channels = [];
    try {
      if (props.data.channels && Array.isArray(props.data.channels)) {
        // 新格式：数据中包含通道列表
        channels = props.data.channels.filter(ch => ch && typeof ch === 'string').map(ch => {
          const values = Array.isArray(props.data.powers[ch]) ? 
            props.data.powers[ch] : 
            Array(frequencies.length).fill(0);
          return { name: ch, values };
        });
      } else if (props.data.powers) {
        // 兼容格式：直接从powers对象中提取通道
        channels = Object.keys(props.data.powers)
          .filter(ch => ch && typeof ch === 'string')
          .map(ch => {
            const rawValues = props.data.powers[ch] || [];
            // 确保values是数组
            const values = Array.isArray(rawValues) ? 
              rawValues : 
              Array(frequencies.length).fill(0);
            return { name: ch, values };
        });
      }
    } catch (err) {
      console.error('处理通道数据时出错:', err);
      // 创建一个默认通道
      channels = [{ name: 'Channel1', values: Array(frequencies.length).fill(1) }];
    }
    
    if (channels.length === 0) {
      console.warn('没有有效的通道数据，创建默认通道');
      channels = [{ name: 'Channel1', values: Array(frequencies.length).fill(1) }];
    }
    
    // 数据验证和转换为图表格式
    const series = channels.map(channel => {
      // 确保值数组是有效的
      const valueArray = Array.isArray(channel.values) ? channel.values : [];
      
      // 创建安全的数据点数组
      const safeData = [];
      for (let index = 0; index < Math.min(valueArray.length, frequencies.length); index++) {
        // 确保频率索引有效
        const freqValue = index < frequencies.length ? frequencies[index] : index;
        // 处理无效值
        let yValue = typeof valueArray[index] === 'number' && !isNaN(valueArray[index]) ? 
                    valueArray[index] : 0;
        // 如果使用对数刻度，对值进行转换（注意处理零值和负值）
        if (props.logScale) {
          yValue = yValue <= 0 ? 0 : Math.log10(yValue);
        }
        safeData.push([freqValue, yValue]);
      }
      
      return {
        name: channel.name,
        type: 'line',
        data: safeData,
        showSymbol: false,
        smooth: true
      };
    });
    
    // 添加频段标记 - 使用安全的方式
    const markAreas = [];
    if (props.data.bands && Array.isArray(props.data.bands)) {
      props.data.bands.forEach(band => {
        if (band && band.range && Array.isArray(band.range) && band.range.length === 2) {
          // 确保range中的值是有效数字
          const range = [
            typeof band.range[0] === 'number' && !isNaN(band.range[0]) ? band.range[0] : 0,
            typeof band.range[1] === 'number' && !isNaN(band.range[1]) ? band.range[1] : 0
          ];
          
          // 确保颜色是有效的
          const color = band.color && typeof band.color === 'string' ? 
                      band.color : 'rgba(0, 0, 0, 0.1)';
          
          markAreas.push([
            { xAxis: range[0], name: band.name || '', itemStyle: { color } },
            { xAxis: range[1] }
          ]);
        }
      });
    }
    
    // 创建图表选项 - 使用简化配置减少潜在问题
    const option = {
      animation: false, // 禁用动画以减少渲染问题
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
            if (param.value && Array.isArray(param.value) && param.value.length > 1) {
              let value = param.value[1];
              // 如果使用对数刻度，将显示值转换回原始值
              if (props.logScale && value > 0) {
                value = Math.pow(10, value).toFixed(2);
                result += `${param.seriesName}: ${value} (log)<br/>`;
              } else {
                value = value.toFixed(2);
                result += `${param.seriesName}: ${value}<br/>`;
              }
            } else {
              result += `${param.seriesName}: 无数据<br/>`;
            }
          });
          
          return result;
        }
      },
      legend: {
        data: channels.map(c => c.name),
        bottom: 10,
        type: channels.length > 10 ? 'scroll' : 'plain'
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
      ]
    };
    
    // 只有在有标记区域时才添加
    if (markAreas.length > 0) {
      option.series[0].markArea = {
        silent: true,
        data: markAreas
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
    } catch (err) {
      console.error('重建频谱图表失败:', err);
      // 尝试使用最简单的配置
      if (chartRef.value) {
        try {
          chart = echarts.init(chartRef.value);
          const simpleOption = {
            title: {
              text: props.title,
              left: 'center'
            },
            xAxis: {
              type: 'value',
              name: '频率 (Hz)'
            },
            yAxis: {
              type: 'value',
              name: '功率'
            },
            series: [{
              type: 'line',
              data: frequencies.map((f, i) => [f, i % 5 + 1]),
              showSymbol: false
            }]
          };
          chart.setOption(simpleOption, true);
        } catch (finalError) {
          console.error('使用简化选项也失败:', finalError);
        }
      }
    }
  } catch (e) {
    console.error('更新频谱图出错:', e);
    // 显示错误信息
    if (chart) {
      try {
        chart.dispose();
      } catch (disposeError) {
        console.error('销毁图表失败:', disposeError);
      }
      
      try {
        chart = echarts.init(chartRef.value);
        chart.setOption({
          title: {
            text: '图表更新出错',
            left: 'center',
            textStyle: {
              color: '#f56c6c',
              fontSize: 14
            }
          },
          graphic: {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
              text: e.message || '未知错误',
              fill: '#999',
              fontSize: 12
            }
          }
        }, true);
      } catch (finalError) {
        console.error('创建错误提示图表也失败:', finalError);
      }
    }
  }
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template> 