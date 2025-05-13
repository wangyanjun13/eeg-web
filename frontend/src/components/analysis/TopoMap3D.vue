<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import 'echarts-gl';

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
let hasRendered = false;
let viewControlTimer = null;

onMounted(() => {
  // 使用setTimeout延迟初始化，避免过早渲染导致的问题
  setTimeout(() => {
    initChart();
  }, 200);
});

onBeforeUnmount(() => {
  // 在组件销毁前清理图表和计时器，防止内存泄漏
  if (viewControlTimer) {
    clearTimeout(viewControlTimer);
    viewControlTimer = null;
  }
  
  if (chart) {
    chart.dispose();
    chart = null;
  }
  
  // 移除事件监听器
  window.removeEventListener('resize', handleResize);
});

watch(() => props.data, () => {
  // 延迟更新，确保DOM已经就绪
  setTimeout(() => {
    updateChart();
  }, 100);
}, { deep: true });

watch(() => props.colorMap, () => {
  if (hasRendered) {
    updateChart();
  }
});

// 验证数据是否有效，进行更严格的检查
function isValidData() {
  if (!props.data || typeof props.data !== 'object') {
    console.warn('数据对象不存在或不是对象类型');
    return false;
  }
  
  if (!props.data.positions || !Array.isArray(props.data.positions) || props.data.positions.length === 0) {
    console.warn('无效的positions数据');
    return false;
  }
  
  if (!props.data.values || !Array.isArray(props.data.values) || props.data.values.length === 0) {
    console.warn('无效的values数据');
    return false;
  }
  
  // 检查数组长度是否匹配
  if (props.data.positions.length !== props.data.values.length) {
    console.warn('positions和values数组长度不匹配');
    return false;
  }
  
  // 检查positions中是否有有效的位置坐标
  let hasValidPosition = false;
  for (const pos of props.data.positions) {
    if (Array.isArray(pos) && pos.length >= 2 && 
        typeof pos[0] === 'number' && !isNaN(pos[0]) && 
        typeof pos[1] === 'number' && !isNaN(pos[1])) {
      hasValidPosition = true;
      break;
    }
  }
  
  if (!hasValidPosition) {
    console.warn('positions中没有有效的位置坐标');
    return false;
  }
  
  // 检查values中是否有有效的数值
  if (!props.data.values.some(v => typeof v === 'number' && !isNaN(v))) {
    console.warn('values中没有有效的数值');
    return false;
  }
  
  return true;
}

function initChart() {
  // 确保DOM元素存在
  if (!chartRef.value) {
    console.warn('3D图表DOM元素不存在');
    return;
  }
  
  try {
    // 如果已有图表实例，先销毁
    if (chart) {
      chart.dispose();
    }
    
    // 初始化图表
    chart = echarts.init(chartRef.value);
    
    // 添加窗口大小变化监听
    window.addEventListener('resize', handleResize);
    
    // 设置一个简单的没有3D元素的初始图表
    chart.setOption({
      title: {
        text: '数据正在加载或无效',
        left: 'center',
        top: 'center'
      }
    });
    
    // 检查数据是否有效,有效才更新图表
    if (isValidData()) {
      hasRendered = true;
      updateChart();
    } else {
      console.warn('3D视图初始化时数据无效，等待有效数据');
    }
  } catch (e) {
    console.error('初始化3D图表时出错:', e);
  }
}

// 窗口大小变化处理函数
function handleResize() {
  if (chart) {
    try {
      chart.resize();
    } catch (e) {
      console.error('图表调整大小时出错:', e);
    }
  }
}

function updateChart() {
  if (!chart) {
    console.warn('图表实例不存在，无法更新');
    return;
  }
  
  if (!isValidData()) {
    console.warn('数据无效，无法更新3D图表');
    
    // 显示友好的提示，使用纯2D元素避免3D渲染错误
    chart.setOption({
      title: {
        text: '数据无效或不完整',
        subtext: '请确保数据包含有效的位置和数值信息',
        left: 'center',
        top: 'center'
      },
      series: [] // 移除所有系列，避免3D渲染
    }, true);
    
    return;
  }
  
  try {
    const positions = props.data.positions;
    const values = props.data.values;
    
    // 过滤无效值，避免计算最大/最小值时出错
    const validValues = values.filter(v => typeof v === 'number' && !isNaN(v));
    if (validValues.length === 0) {
      console.warn('没有有效的数值，使用默认范围');
      return;
    }
    
    // 确定颜色范围
    const min = Math.min(...validValues);
    const max = Math.max(...validValues);
    
    // 简化颜色映射
    let colors = ['#00007F', '#0000FF', '#00FFFF', '#FFFF00', '#FF0000']; // 默认jet
    
    if (props.colorMap === 'viridis') {
      colors = ['#440154', '#433982', '#30678D', '#218F8B', '#36B677', '#8ED542', '#FDE725'];
    } else if (props.colorMap === 'plasma') {
      colors = ['#0D0887', '#5B02A3', '#9A179B', '#CB4678', '#EB7852', '#FBB32F', '#F0F921'];
    } else if (props.colorMap === 'inferno') {
      colors = ['#000004', '#320A5A', '#781C6D', '#BC3754', '#ED6925', '#FBB32F', '#FCFEA4'];
    }
    
    // 创建3D球体数据
    const sphereRadius = 0.5;
    const sphereCenter = [0, 0, 0];
    
    // 创建网格数据
    const resolution = props.data.interpolation?.resolution || 32;
    const [data3D, indices] = createSphereData(sphereRadius, resolution);
    
    // 创建头皮表面数据
    const surfaceData = [];
    const channels = props.data.channels || [];
    
    // 将电极位置转换为3D坐标
    const positions3D = [];
    
    for (let i = 0; i < positions.length; i++) {
      const pos = positions[i];
      if (!Array.isArray(pos) || pos.length < 2 || 
          typeof pos[0] !== 'number' || isNaN(pos[0]) ||
          typeof pos[1] !== 'number' || isNaN(pos[1])) {
        console.warn('跳过无效的位置数据:', pos);
        // 添加一个默认位置，保持数组索引一致
        positions3D.push([0, 0, 0]);
      } else {
        const [x, y] = pos;
        // 使用平面坐标计算球面坐标
        const r = Math.sqrt(x*x + y*y);
        const phi = Math.atan2(y, x);
        // z坐标使用球面方程计算: r^2 = x^2 + y^2 + z^2, 其中r是球半径
        const z = r > sphereRadius ? 0 : Math.sqrt(sphereRadius*sphereRadius - r*r);
        positions3D.push([x, y, z]);
      }
    }
    
    // 确保有足够的有效位置
    if (positions3D.filter(p => p[0] !== 0 || p[1] !== 0 || p[2] !== 0).length === 0) {
      console.warn('没有有效的3D位置数据');
      
      // 显示友好的错误提示
      chart.setOption({
        title: {
          text: '无法创建3D视图',
          subtext: '没有有效的位置数据',
          left: 'center',
          top: 'center'
        },
        series: [] // 移除所有系列，避免3D渲染
      }, true);
      
      return;
    }
    
    // 基本图表配置，避免3D特定属性
    const baseOption = {
      title: {
        text: props.title,
        left: 'center'
      },
      tooltip: {
        formatter: function(params) {
          if (params.seriesName === 'electrodes') {
            const index = params.dataIndex;
            if (index >= 0 && index < channels.length && index < values.length) {
              const channelName = channels[index] || `CH${index+1}`;
              const value = typeof values[index] === 'number' ? values[index].toFixed(2) : 'N/A';
              return `${channelName}: ${value}`;
            }
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
      }
    };
    
    // 添加3D特定配置
    const option = {
      ...baseOption,
      grid3D: {
        viewControl: {
          // 初始禁用自动旋转和动画，避免不必要的渲染和错误
          autoRotate: false, 
          autoRotateSpeed: 5,
          distance: 150,
          animation: false,
          // 禁用交互，先让图表稳定渲染
          enableMouseAction: false
        },
        boxWidth: 100, // 明确设置盒子尺寸，避免自动计算出错
        boxHeight: 100,
        boxDepth: 100,
        axisTick: {
          show: false // 禁用刻度，减少渲染复杂性
        }
      },
      xAxis3D: {
        type: 'value',
        min: -0.7,
        max: 0.7,
        axisLine: {
          show: false
        },
        axisLabel: {
          show: false
        },
        splitLine: {
          show: false
        }
      },
      yAxis3D: {
        type: 'value',
        min: -0.7,
        max: 0.7,
        axisLine: {
          show: false
        },
        axisLabel: {
          show: false
        },
        splitLine: {
          show: false
        }
      },
      zAxis3D: {
        type: 'value',
        min: -0.7,
        max: 0.7,
        axisLine: {
          show: false
        },
        axisLabel: {
          show: false
        },
        splitLine: {
          show: false
        }
      },
      series: [
        {
          name: 'surface',
          type: 'scatter3D',
          data: positions3D.map((pos, index) => {
            if (index < values.length && typeof values[index] === 'number' && !isNaN(values[index])) {
              return {
                value: pos,
                itemStyle: {
                  color: getColorFromValue(values[index], min, max, colors)
                }
              };
            } else {
              return {
                value: pos,
                itemStyle: {
                  color: '#CCCCCC' // 默认灰色
                }
              };
            }
          }),
          symbolSize: 10,
          blendMode: 'source-over'
        },
        {
          name: 'electrodes',
          type: 'scatter3D',
          data: positions3D.filter(pos => pos[0] !== 0 || pos[1] !== 0 || pos[2] !== 0), // 只使用有效位置
          symbolSize: 8,
          itemStyle: {
            color: '#fff',
            borderColor: '#000',
            borderWidth: 1
          }
        }
      ]
    };
    
    try {
      // 应用基本选项，不包含3D内容
      chart.setOption(baseOption, true);
      
      // 短暂延迟后应用完整3D选项
      setTimeout(() => {
        chart.setOption(option, true);
        
        // 清除之前的计时器
        if (viewControlTimer) {
          clearTimeout(viewControlTimer);
        }
        
        // 延迟启用视图控制和动画，避免初始化时的错误
        viewControlTimer = setTimeout(() => {
          if (chart) {
            try {
              chart.setOption({
                grid3D: {
                  viewControl: {
                    autoRotate: true,
                    autoRotateSpeed: 5,
                    animation: true,
                    enableMouseAction: true
                  }
                }
              });
              hasRendered = true;
            } catch (e) {
              console.error('启用3D视图控制时出错:', e);
            }
          }
        }, 2000); // 延长延迟时间，确保图表已完全渲染
      }, 200);
    } catch (e) {
      console.error('设置3D图表选项时出错:', e);
      // 确保图表至少显示一些内容
      chart.setOption({
        title: {
          text: '3D渲染出错，请稍后重试',
          left: 'center'
        },
        series: [] // 移除所有系列，避免继续渲染出错
      });
    }
  } catch (e) {
    console.error('更新3D图表时出错:', e);
    
    // 显示错误提示
    if (chart) {
      chart.setOption({
        title: {
          text: '3D渲染出错',
          subtext: e.message || '未知错误',
          left: 'center'
        },
        series: [] // 移除所有系列，避免继续渲染出错
      });
    }
  }
}

// 创建球面数据
function createSphereData(radius, resolution) {
  try {
    // 确保分辨率合理
    const safeResolution = Math.max(10, Math.min(100, resolution));
    
    const data = [];
    const indices = [];
    
    for (let i = 0; i <= safeResolution; i++) {
      const latAngle = (Math.PI * i) / safeResolution;
      const sinLat = Math.sin(latAngle);
      const cosLat = Math.cos(latAngle);
      
      for (let j = 0; j <= safeResolution; j++) {
        const lonAngle = (2 * Math.PI * j) / safeResolution;
        const sinLon = Math.sin(lonAngle);
        const cosLon = Math.cos(lonAngle);
        
        const x = radius * sinLat * cosLon;
        const y = radius * sinLat * sinLon;
        const z = radius * cosLat;
        
        data.push([x, y, z]);
      }
    }
    
    return [data, indices];
  } catch (e) {
    console.error('创建球面数据出错:', e);
    return [[], []];
  }
}

// 根据值获取颜色
function getColorFromValue(value, min, max, colors) {
  try {
    // 确保value是有效数字
    if (typeof value !== 'number' || isNaN(value)) {
      console.warn('无效的颜色值:', value);
      return '#CCCCCC'; // 默认灰色
    }
    
    // 将值归一化到0-1范围
    const normalizedValue = (value - min) / (max - min || 1);
    
    // 计算颜色数组的索引
    const index = Math.min(
      Math.floor(normalizedValue * (colors.length - 1)),
      colors.length - 2
    );
    
    // 获取相邻的两个颜色
    const color1 = colors[index];
    const color2 = colors[index + 1];
    
    // 计算两个颜色之间的插值比例
    const ratio = (normalizedValue * (colors.length - 1)) % 1;
    
    // 颜色插值函数
    return interpolateColor(color1, color2, ratio);
  } catch (e) {
    console.error('获取颜色映射出错:', e);
    return '#CCCCCC'; // 默认灰色
  }
}

// 颜色插值函数
function interpolateColor(color1, color2, ratio) {
  try {
    // 检查颜色格式是否有效
    if (!color1 || typeof color1 !== 'string' || !color1.startsWith('#') || color1.length < 7) {
      console.warn('无效的颜色1:', color1);
      return '#CCCCCC';
    }
    
    if (!color2 || typeof color2 !== 'string' || !color2.startsWith('#') || color2.length < 7) {
      console.warn('无效的颜色2:', color2);
      return '#CCCCCC';
    }
    
    // 转换颜色到RGB格式
    const r1 = parseInt(color1.substring(1, 3), 16);
    const g1 = parseInt(color1.substring(3, 5), 16);
    const b1 = parseInt(color1.substring(5, 7), 16);
    
    const r2 = parseInt(color2.substring(1, 3), 16);
    const g2 = parseInt(color2.substring(3, 5), 16);
    const b2 = parseInt(color2.substring(5, 7), 16);
    
    // 线性插值
    const r = Math.round(r1 * (1 - ratio) + r2 * ratio);
    const g = Math.round(g1 * (1 - ratio) + g2 * ratio);
    const b = Math.round(b1 * (1 - ratio) + b2 * ratio);
    
    // 转换回16进制格式
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  } catch (e) {
    console.error('颜色插值出错:', e);
    return '#CCCCCC'; // 默认灰色
  }
}
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 500px;"></div>
</template> 