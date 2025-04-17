<script setup>
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue';
import { ElMessage } from 'element-plus';
import analysisService from '@/services/analysisService';
import { useLoading } from '@/composables/useLoading';
import * as echarts from 'echarts';

const props = defineProps({
  preprocessParams: {
    type: Object,
    required: true
  },
  datasetId: {
    type: String,
    required: true
  },
  subjectId: {
    type: String,
    required: true
  },
  originalData: {
    type: Object,
    default: null
  },
  processingChannels: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['process-complete']);

const { isLoading, withLoading } = useLoading({
  processing: false
});

// 滤波器响应可视化
const showFilterResponse = ref(false);
const filterResponseRef = ref(null);
let filterResponseChart = null;

// 计算滤波器响应
const filterResponse = computed(() => {
  if (!showFilterResponse.value) return null;
  
  // 生成频率范围 (0-100Hz)
  const freqs = Array.from({length: 101}, (_, i) => i);
  
  // 计算滤波器响应
  return freqs.map(f => {
    let gain = 1.0;
    
    // 简单模拟高通滤波
    if (props.preprocessParams.filter.highpass_filter) {
      const hpFreq = props.preprocessParams.filter.highpass;
      // 衰减曲线：低于高通频率的信号衰减
      if (f < hpFreq) {
        // 使用温和的衰减曲线
        gain *= Math.pow(f / hpFreq, 2);
      }
    }
    
    // 简单模拟低通滤波
    if (props.preprocessParams.filter.lowpass_filter) {
      const lpFreq = props.preprocessParams.filter.lowpass;
      // 衰减曲线：高于低通频率的信号衰减
      if (f > lpFreq) {
        // 使用温和的衰减曲线
        gain *= Math.max(0, Math.pow(1 - (f - lpFreq) / (lpFreq), 2));
      }
    }
    
    // 陷波滤波
    if (props.preprocessParams.filter.notch_filter) {
      for (const lineFreq of props.preprocessParams.filter.line_freqs) {
        // 简单模拟陷波（在线频率附近有凹陷）
        const dist = Math.abs(f - lineFreq);
        if (dist < 2) {
          gain *= Math.min(dist / 2, 0.1); // 在线频率处衰减至少90%
        }
      }
    }
    
    return [f, gain];
  });
});

// 初始化滤波器响应图表
const initFilterResponseChart = () => {
  if (filterResponseChart) filterResponseChart.dispose();
  if (!filterResponseRef.value) return;
  
  filterResponseChart = echarts.init(filterResponseRef.value);
  updateFilterResponseChart();
  
  window.addEventListener('resize', () => filterResponseChart?.resize());
};

// 更新滤波器响应图表
const updateFilterResponseChart = () => {
  if (!filterResponseChart || !showFilterResponse.value) return;
  
  const option = {
    title: {
      text: '滤波器频率响应',
      textStyle: {
        fontSize: 14
      },
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const data = params[0].data;
        return `频率: ${data[0]} Hz<br/>增益: ${data[1].toFixed(3)}`;
      }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '25%'
    },
    xAxis: {
      type: 'value',
      name: '频率 (Hz)',
      nameLocation: 'middle',
      nameGap: 25,
      max: 100
    },
    yAxis: {
      type: 'value',
      name: '增益',
      nameLocation: 'middle',
      nameGap: 30,
      nameRotate: 90,
      min: 0,
      max: 1.05
    },
    series: [
      {
        type: 'line',
        data: filterResponse.value,
        smooth: true,
        showSymbol: false,
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(64, 158, 255, 0.4)'
              },
              {
                offset: 1,
                color: 'rgba(64, 158, 255, 0.1)'
              }
            ]
          }
        }
      }
    ]
  };
  
  filterResponseChart.setOption(option);
};

// 监听滤波器参数变化，更新响应图
watch(() => props.preprocessParams.filter, () => {
  if (showFilterResponse.value) {
    nextTick(updateFilterResponseChart);
  }
}, { deep: true });

// 监听是否显示滤波器响应
watch(showFilterResponse, (newValue) => {
  if (newValue) {
    nextTick(() => {
      initFilterResponseChart();
    });
  }
});

// 组件挂载完成
onMounted(() => {
  if (showFilterResponse.value) {
    nextTick(initFilterResponseChart);
  }
});

// 组件卸载前清理
onBeforeUnmount(() => {
  if (filterResponseChart) {
    filterResponseChart.dispose();
    filterResponseChart = null;
  }
  window.removeEventListener('resize', () => filterResponseChart?.resize());
});

// 应用滤波
const applyFilter = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 参数验证 - 调整为更合理的范围
    if (props.preprocessParams.filter.highpass_filter && 
        (props.preprocessParams.filter.highpass < 0.1 || props.preprocessParams.filter.highpass > 30)) {
      throw new Error('高通滤波截止频率建议在0.1-30Hz之间');
    }

    if (props.preprocessParams.filter.lowpass_filter && 
        (props.preprocessParams.filter.lowpass < 30 || props.preprocessParams.filter.lowpass > 120)) {
      throw new Error('低通滤波截止频率建议在30-120Hz之间');
    }

    // 验证处理通道不为空
    if (!props.processingChannels || props.processingChannels.length === 0) {
      throw new Error('请至少选择一个通道进行处理');
    }

    console.log('应用滤波器，参数:', {
      highpass_filter: props.preprocessParams.filter.highpass_filter,
      highpass: props.preprocessParams.filter.highpass,
      lowpass_filter: props.preprocessParams.filter.lowpass_filter,
      lowpass: props.preprocessParams.filter.lowpass,
      notch_filter: props.preprocessParams.filter.notch_filter,
      line_freqs: props.preprocessParams.filter.line_freqs,
      channels: props.processingChannels
    });

    // 显示提示正在处理
    const loadingMessage = ElMessage({
      type: 'info',
      message: '正在应用滤波处理，这可能需要几秒钟...',
      duration: 0
    });

    const response = await withLoading(
      analysisService.applyFilter(props.datasetId, props.subjectId, {
        highpass_filter: props.preprocessParams.filter.highpass_filter,
        highpass: props.preprocessParams.filter.highpass,
        lowpass_filter: props.preprocessParams.filter.lowpass_filter,
        lowpass: props.preprocessParams.filter.lowpass,
        notch_filter: props.preprocessParams.filter.notch_filter,
        line_freqs: props.preprocessParams.filter.line_freqs,
        channels: props.processingChannels
      }),
      'processing'
    );

    // 关闭加载提示
    loadingMessage.close();

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    
    // 根据是否从缓存获取，显示不同的成功消息
    if (response.from_cache) {
      ElMessage.success('从缓存获取滤波结果成功');
    } else {
      ElMessage.success('滤波器应用成功');
    }
  } catch (error) {
    console.error('应用滤波器失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用滤波器失败: ${errorMessage}`);
  }
};
</script>

<template>
  <div class="filter-processor">
    <h3>滤波设置</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <!-- 高通滤波 - 调整范围 -->
      <el-form-item label="高通滤波">
        <div class="filter-control">
          <el-switch v-model="preprocessParams.filter.highpass_filter" />
          <el-input-number 
            v-if="preprocessParams.filter.highpass_filter"
            v-model="preprocessParams.filter.highpass" 
            :min="0.1" 
            :max="30" 
            :step="0.1"
            :disabled="!preprocessParams.filter.highpass_filter"
            size="small"
            class="small-input"
          />
          <span v-if="preprocessParams.filter.highpass_filter" class="unit">Hz</span>
        </div>
      </el-form-item>
      
      <!-- 低通滤波 - 调整范围 -->
      <el-form-item label="低通滤波">
        <div class="filter-control">
          <el-switch v-model="preprocessParams.filter.lowpass_filter" />
          <el-input-number 
            v-if="preprocessParams.filter.lowpass_filter"
            v-model="preprocessParams.filter.lowpass" 
            :min="30" 
            :max="120" 
            :step="1"
            :disabled="!preprocessParams.filter.lowpass_filter"
            size="small"
            class="small-input"
          />
          <span v-if="preprocessParams.filter.lowpass_filter" class="unit">Hz</span>
        </div>
      </el-form-item>
      
      <!-- 陷波滤波 -->
      <el-form-item label="陷波滤波">
        <div class="filter-control">
          <el-switch v-model="preprocessParams.filter.notch_filter" />
          <div v-if="preprocessParams.filter.notch_filter" class="notch-frequencies">
            <el-checkbox-group v-model="preprocessParams.filter.line_freqs">
              <el-checkbox :label="50" size="small">50Hz</el-checkbox>
              <el-checkbox :label="60" size="small">60Hz</el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>
      
      <!-- 滤波器响应可视化 -->
      <el-form-item label="显示响应">
        <el-switch v-model="showFilterResponse" />
      </el-form-item>
      
      <div v-if="showFilterResponse" class="filter-response">
        <div ref="filterResponseRef" class="filter-chart"></div>
        <div class="filter-explanation">
          <p>滤波器频率响应表示各频率成分的保留程度</p>
          <p>增益=1表示信号完全保留，0表示完全抑制</p>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <el-form-item class="action-item">
        <el-button 
          type="primary" 
          @click="applyFilter" 
          :loading="isLoading.processing"
          :disabled="!originalData"
          size="small"
        >
          应用滤波器
        </el-button>
      </el-form-item>
    </el-form>
    
    <!-- 在表单底部添加一个提示 -->
    <div class="channels-hint" v-if="processingChannels.length > 0">
      <el-alert
        title="通道选择提示"
        type="info"
        description="请先在右侧图表选择要显示和处理的通道，将应用于后续流程，不可更改。"
        :closable="false"
        show-icon
        class="custom-alert"
      />
    </div>
  </div>
</template>

<style scoped>
.filter-processor {
  padding: 10px;
  max-width: 250px;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.filter-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.small-input {
  width: 80px;
}

.unit {
  color: #606266;
  font-size: 12px;
}

.notch-frequencies {
  margin-left: 5px;
}

.filter-response {
  margin-top: 5px;
  margin-bottom: 15px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  padding: 10px;
}

.filter-chart {
  height: 180px;
  width: 100%;
}

.filter-explanation {
  margin-top: 8px;
  padding-top: 5px;
  border-top: 1px dashed #EBEEF5;
  font-size: 12px;
  color: #909399;
}

.filter-explanation p {
  margin: 5px 0;
}

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}

:deep(.el-checkbox__label) {
  font-size: 12px;
}

/* 添加通道提示样式 */
.channels-hint {
  margin-top: 10px;
  margin-bottom: 10px;
}

/* 自定义提示图标大小 */
.custom-alert :deep(.el-alert__icon) {
  font-size: 14px; /* 减小图标大小 */
  margin-right: 6px; /* 稍微调整间距 */
}
</style> 