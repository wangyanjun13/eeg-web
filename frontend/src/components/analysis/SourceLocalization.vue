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
    console.warn('源定位数据对象不存在或不是对象类型');
    return false;
  }
  
  // 对于源定位，至少需要positions数据
  if (!props.data.positions || !Array.isArray(props.data.positions) || props.data.positions.length === 0) {
    console.warn('无效的positions数据');
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
  
  return true;
}

function initChart() {
  if (!chartRef.value) {
    console.warn('源定位图表DOM元素不存在');
    return;
  }
  
  try {
    // 如果已存在图表实例，先销毁
    if (chart) {
      chart.dispose();
    }
    
    chart = echarts.init(chartRef.value);
    
    // 设置一个简单的没有3D元素的初始图表
    chart.setOption({
      title: {
        text: '数据正在加载或无效',
        left: 'center',
        top: 'center'
      }
    });
    
    // 添加窗口大小变化监听
    window.addEventListener('resize', handleResize);
    
    // 检查数据是否有效,有效才更新图表
    if (isValidData()) {
      hasRendered = true;
      updateChart();
    } else {
      console.warn('源定位视图初始化时数据无效，等待有效数据');
    }
  } catch (e) {
    console.error('初始化源定位图表时出错:', e);
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
    console.warn('图表实例不存在，无法更新源定位图表');
    return;
  }
  
  if (!isValidData()) {
    console.warn('数据无效，无法更新源定位图表');
    
    // 显示友好的提示，使用纯2D元素避免3D渲染错误
    chart.setOption({
      title: {
        text: '数据无效或不完整',
        subtext: '请确保数据包含有效的位置信息',
        left: 'center',
        top: 'center'
      },
      series: [] // 移除所有系列，避免3D渲染
    }, true);
    
    return;
  }
  
  try {
    // 创建简化的大脑模型
    const brainRadius = 0.4;
    const resolution = 50;
    const brainMesh = createBrainMesh(brainRadius, resolution);
    
    // 创建电极位置和活动源点
    const electrodePositions = props.data && props.data.positions ? props.data.positions : [];
    const values = props.data && props.data.values ? props.data.values : [];
    
    // 验证电极位置数据
    if (!electrodePositions.length) {
      console.warn('没有有效的电极位置数据');
      
      // 显示友好的提示，使用纯2D元素避免3D渲染错误
      chart.setOption({
        title: {
          text: '无法创建源定位视图',
          subtext: '没有有效的电极位置数据',
          left: 'center',
          top: 'center'
        },
        series: [] // 移除所有系列，避免3D渲染
      }, true);
      
      return;
    }
    
    // 确保安全生成源点
    const sources = generateSourcePoints(electrodePositions, values);
    
    // 验证源点数据
    if (!sources.length) {
      console.warn('没有有效的源点数据');
      
      // 显示友好的提示，使用纯2D元素避免3D渲染错误
      chart.setOption({
        title: {
          text: '无法创建源定位视图',
          subtext: '生成源点失败',
          left: 'center',
          top: 'center'
        },
        series: [] // 移除所有系列，避免3D渲染
      }, true);
      
      return;
    }
    
    // 计算值的范围
    const valuesArray = sources.map(s => s.value).filter(v => typeof v === 'number' && !isNaN(v));
    if (!valuesArray.length) {
      console.warn('没有有效的源点数值');
      
      // 显示友好的提示，使用纯2D元素避免3D渲染错误
      chart.setOption({
        title: {
          text: '无法创建源定位视图',
          subtext: '没有有效的源点数值',
          left: 'center',
          top: 'center'
        },
        series: [] // 移除所有系列，避免3D渲染
      }, true);
      
      return;
    }
    
    const min = Math.min(...valuesArray);
    const max = Math.max(...valuesArray);
    
    // 颜色映射
    let colors = ['#00007F', '#0000FF', '#00FFFF', '#FFFF00', '#FF0000']; // 默认jet
    
    if (props.colorMap === 'viridis') {
      colors = ['#440154', '#433982', '#30678D', '#218F8B', '#36B677', '#8ED542', '#FDE725'];
    } else if (props.colorMap === 'plasma') {
      colors = ['#0D0887', '#5B02A3', '#9A179B', '#CB4678', '#EB7852', '#FBB32F', '#F0F921'];
    } else if (props.colorMap === 'inferno') {
      colors = ['#000004', '#320A5A', '#781C6D', '#BC3754', '#ED6925', '#FBB32F', '#FCFEA4'];
    }
    
    // 基本图表配置，避免3D特定属性
    const baseOption = {
      title: {
        text: props.title || '源定位（示例）',
        left: 'center'
      },
      tooltip: {},
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
          // 初始禁用自动旋转和动画，避免渲染错误
          autoRotate: false,
          autoRotateSpeed: 10,
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
          name: 'brain',
          type: 'surface',
          data: brainMesh.data,
          itemStyle: {
            color: '#e0e0e0',
            opacity: 0.6
          },
          wireframe: {
            show: true,
            lineStyle: {
              color: '#aaa',
              width: 1
            }
          }
        },
        {
          name: 'sources',
          type: 'scatter3D',
          data: sources.map(source => {
            // 验证位置和值的有效性
            if (!source.position || !Array.isArray(source.position) || source.position.length < 3 ||
                typeof source.value !== 'number' || isNaN(source.value)) {
              return {
                value: [0, 0, 0],
                symbolSize: 5,
                itemStyle: {
                  color: '#CCCCCC',
                  opacity: 0.5
                }
              };
            }
            
            return {
              value: source.position,
              symbolSize: Math.max(5, Math.min(20, 5 + (source.value - min) / (max - min) * 15)),
              itemStyle: {
                color: getColorFromValue(source.value, min, max, colors),
                opacity: 0.9
              }
            };
          }),
          blendMode: 'source-over'
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
                    autoRotateSpeed: 10,
                    animation: true,
                    enableMouseAction: true
                  }
                }
              });
              hasRendered = true;
            } catch (e) {
              console.error('启用源定位3D视图控制时出错:', e);
            }
          }
        }, 2000); // 延长延迟时间，确保图表已完全渲染
      }, 200);
    } catch (e) {
      console.error('设置源定位图表时出错:', e);
      
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
    console.error('更新源定位图表时出错:', e);
    
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

// 创建简化的大脑网格模型
function createBrainMesh(radius, resolution) {
  try {
    // 确保分辨率合理
    const safeResolution = Math.max(10, Math.min(100, resolution));
    
    const data = {
      data: [],
      rows: safeResolution,
      columns: safeResolution
    };
    
    for (let i = 0; i < safeResolution; i++) {
      for (let j = 0; j < safeResolution; j++) {
        // 参数化坐标
        const u = i / (safeResolution - 1) * Math.PI;
        const v = j / (safeResolution - 1) * 2 * Math.PI;
        
        // 椭球方程
        let x = radius * 1.1 * Math.sin(u) * Math.cos(v);
        let y = radius * 0.9 * Math.sin(u) * Math.sin(v);
        let z = radius * 1.2 * Math.cos(u);
        
        // 添加一些变形模拟大脑形状
        if (u < Math.PI / 2) {  // 前半部分
          x *= 1.1;
          z *= 0.9;
        } else {  // 后半部分
          y *= 1.1;
        }
        
        // 扁平化底部
        if (z < -radius * 0.5) {
          z = -radius * 0.5;
        }
        
        // 组装数据点
        data.data.push([x, y, z]);
      }
    }
    
    return data;
  } catch (e) {
    console.error('创建大脑网格模型时出错:', e);
    return { data: [], rows: 0, columns: 0 };
  }
}

// 根据电极位置和值生成活动源点
function generateSourcePoints(electrodePositions, values) {
  try {
    const sources = [];
    
    // 如果没有电极位置数据，生成一些默认的源点
    if (!electrodePositions || !Array.isArray(electrodePositions) || electrodePositions.length === 0) {
      console.log('没有电极位置数据，生成默认源点');
      // 生成20个随机源点，减少数量以减轻渲染负担
      for (let i = 0; i < 20; i++) {
        const theta = Math.random() * Math.PI;
        const phi = Math.random() * 2 * Math.PI;
        const radius = 0.3 * (0.8 + Math.random() * 0.2); // 源点位于大脑内部
        
        const x = radius * Math.sin(theta) * Math.cos(phi);
        const y = radius * Math.sin(theta) * Math.sin(phi);
        const z = radius * Math.cos(theta);
        
        sources.push({
          position: [x, y, z],
          value: Math.random() * 10
        });
      }
      return sources;
    }
    
    // 使用电极数据生成源点（这只是一个演示，实际的源定位算法更复杂）
    electrodePositions.forEach((pos, index) => {
      if (!pos || !Array.isArray(pos) || pos.length < 2 || 
          typeof pos[0] !== 'number' || isNaN(pos[0]) ||
          typeof pos[1] !== 'number' || isNaN(pos[1])) {
        console.warn('跳过无效的电极位置数据:', pos);
        return;
      }
      
      const [x2d, y2d] = pos;
      // 从2D投影到3D，深入到大脑内部
      const r2d = Math.sqrt(x2d * x2d + y2d * y2d);
      const phi = Math.atan2(y2d, x2d);
      // 源点位置在电极位置的正下方，但在大脑内部
      const depth = 0.15 + Math.random() * 0.15;
      const r3d = Math.max(0.1, r2d - depth);
      
      const x = r3d * Math.cos(phi);
      const y = r3d * Math.sin(phi);
      // 根据2D坐标计算合理的z坐标
      const z = r3d < 0.3 ? Math.sqrt(0.3*0.3 - r3d*r3d) * (Math.random() > 0.5 ? 1 : -1) : 0;
      
      // 确保值是有效数字
      let value = Math.random() * 10; // 默认随机值
      if (Array.isArray(values) && index < values.length && 
          typeof values[index] === 'number' && !isNaN(values[index])) {
        value = values[index];
      }
      
      sources.push({
        position: [x, y, z],
        value: value
      });
    });
    
    // 确保至少有一些源点
    if (sources.length === 0) {
      console.warn('没有有效的源点生成，创建默认源点');
      // 减少数量到10个，避免渲染压力过大
      for (let i = 0; i < 10; i++) {
        sources.push({
          position: [
            (Math.random() - 0.5) * 0.5,
            (Math.random() - 0.5) * 0.5,
            (Math.random() - 0.5) * 0.5
          ],
          value: Math.random() * 10
        });
      }
    }
    
    return sources;
  } catch (e) {
    console.error('生成源点时出错:', e);
    // 返回一些默认源点，防止渲染失败，减少到5个点
    return Array(5).fill().map(() => ({
      position: [
        (Math.random() - 0.5) * 0.5,
        (Math.random() - 0.5) * 0.5,
        (Math.random() - 0.5) * 0.5
      ],
      value: Math.random() * 10
    }));
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
  <div>
    <div class="source-info">
      <p>源定位功能提供EEG信号的大脑皮层源推断，当前为示意图。</p>
      <p>完整源定位功能需要更多计算资源和头部模型（BEM/FEM）。</p>
    </div>
    <div ref="chartRef" style="width: 100%; height: 400px;"></div>
  </div>
</template>

<style scoped>
.source-info {
  text-align: center;
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}
</style> 