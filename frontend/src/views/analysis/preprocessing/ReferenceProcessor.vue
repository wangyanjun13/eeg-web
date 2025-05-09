<script setup>
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import analysisService from '@/services/analysisService';
import { useLoading } from '@/composables/useLoading';

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

// 可用的通道列表
const availableChannels = computed(() => {
  if (props.processingChannels && props.processingChannels.length > 0) {
    return props.processingChannels;
  } else if (props.originalData && props.originalData.channels) {
    return props.originalData.channels;
  }
  return [];
});

// 应用重参考
const applyReference = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 参数验证
    if (props.preprocessParams.reference.reference === 'custom' && 
        (!props.preprocessParams.reference.custom_ref_channels || 
         props.preprocessParams.reference.custom_ref_channels.length === 0)) {
      throw new Error('使用自定义参考时，必须选择至少一个参考通道');
    }

    // 双侧乳突参考检查
    if (props.preprocessParams.reference.reference === 'mastoids') {
      const hasMastoids = availableChannels.value.some(ch => ['M1', 'M2', 'TP9', 'TP10'].includes(ch));
      if (!hasMastoids) {
        throw new Error('未检测到乳突通道(M1/M2或TP9/TP10)，无法应用乳突参考');
      }
    }

    console.log('应用重参考处理:', props.preprocessParams.reference);
    console.log('处理通道列表:', props.processingChannels);
    
    // 验证处理通道列表
    if (!props.processingChannels || props.processingChannels.length === 0) {
      console.warn('未指定处理通道列表，将使用所有可用通道');
    }
    
    // 确保原始数据有效
    if (!props.originalData.data || !props.originalData.times) {
      throw new Error('原始数据无效，缺少数据或时间信息');
    }
    
    // 记录原始数据的时间范围信息，用于后续处理
    const originalTimeRange = props.originalData.timeRange || 
                             [props.originalData.times[0], props.originalData.times[props.originalData.times.length - 1]];
    console.log('原始数据时间范围:', originalTimeRange);
    
    // 创建完整的参数对象，确保正确传递channels参数和时间范围
    const requestParams = {
      reference: props.preprocessParams.reference.reference,
      custom_ref_channels: props.preprocessParams.reference.custom_ref_channels || [],
      channels: props.processingChannels.length > 0 ? props.processingChannels : null,
      // 传递时间范围到后端，以确保处理的一致性
      time_range: originalTimeRange
    };
    
    // 调用重参考API，传递完整参数对象
    const response = await withLoading(
      analysisService.applyReference(props.datasetId, props.subjectId, requestParams),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }
    
    // 验证返回的数据结构
    if (!response.data.data || !response.data.times) {
      console.warn('服务器返回的数据结构可能不完整，可能影响显示效果');
    }
    
    // 检查时间数据的有效性
    const times = response.data.times || [];
    if (times.length > 1) {
      const timeRange = times[times.length - 1] - times[0];
      if (timeRange < 0.001) {
        console.warn('重参考结果的时间范围异常小，可能影响显示效果', timeRange);
      }
      if (times.length > 5 && times.slice(0, 5).every(t => Math.abs(t - times[0]) < 0.0001)) {
        console.warn('重参考结果的前几个时间点几乎相同，可能影响显示效果');
      }
    } else if (times.length <= 1) {
      console.warn('重参考结果没有有效的时间数据，可能影响显示效果');
    }
    
    // 确保数据和时间点的长度匹配
    const firstChannel = Object.keys(response.data.data || {})[0];
    if (firstChannel && response.data.data[firstChannel]) {
      const channelLength = response.data.data[firstChannel].length;
      if (times.length !== channelLength) {
        console.warn(`数据长度(${channelLength})与时间点长度(${times.length})不匹配，可能影响显示效果`);
      }
    }
    
    // 确保结果中包含原始数据的时间范围
    if (!response.data.timeRange) {
      console.log('添加原始数据的时间范围信息到结果:', originalTimeRange);
      response.data.timeRange = originalTimeRange;
    }
    
    console.log('参考处理完成，数据结构:', {
      通道数: response.data.channels?.length,
      时间点数: response.data.times?.length,
      数据对象大小: Object.keys(response.data.data || {}).length,
      时间范围: response.data.timeRange
    });

    emit('process-complete', response.data);
    ElMessage.success('重参考应用成功');
  } catch (error) {
    console.error('应用重参考失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用重参考失败: ${errorMessage}`);
  }
};

// 打开通道选择器
const showChannelSelector = ref(false);

// 选择通道 - 确保只能从处理通道中选择
const selectChannels = () => {
  showChannelSelector.value = true;
};
</script>

<template>
  <div class="reference-processor">
    <h3>重参考设置</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <el-form-item label="参考方式">
        <el-radio-group v-model="preprocessParams.reference.reference">
          <el-radio label="average">平均参考</el-radio>
          <el-radio label="mastoids">双侧乳突参考</el-radio>
          <el-radio label="custom">自定义参考</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 添加简单的重参考解释 -->
      <div class="reference-explanation">
        <p class="explanation-text">
          重参考将改变信号的基准点，使得通道间电位差更准确反映大脑活动。
        </p>
      </div>
      
      <el-form-item label="参考通道" v-if="preprocessParams.reference.reference === 'custom'">
        <div class="help-text">
          <small>
            请选择要作为参考的通道（数据会减去这些通道的平均值）
          </small>
        </div>
        <el-select 
          v-model="preprocessParams.reference.custom_ref_channels" 
          multiple 
          placeholder="选择参考通道"
          style="width: 100%"
        >
          <el-option 
            v-for="channel in availableChannels" 
            :key="channel" 
            :label="channel" 
            :value="channel"
          />
        </el-select>
      </el-form-item>
      
      <el-alert 
        v-if="preprocessParams.reference.reference === 'average'"
        type="info"
        show-icon
        :closable="false"
      >
        平均参考：将所有通道的平均值作为参考，适合电极分布均匀的情况
      </el-alert>
      
      <el-alert 
        v-if="preprocessParams.reference.reference === 'mastoids'"
        type="info"
        show-icon
        :closable="false"
      >
        使用 M1/M2 或 TP9/TP10 作为参考，适合前额和中央区域分析
      </el-alert>
      
      <el-alert 
        v-if="preprocessParams.reference.reference === 'custom'"
        type="info"
        show-icon
        :closable="false"
      >
        自定义参考：选择特定通道作为参考，适合针对性研究特定脑区
      </el-alert>
      
      <el-alert 
        v-if="preprocessParams.reference.reference === 'mastoids' && 
              (!availableChannels.includes('M1') || !availableChannels.includes('M2'))"
        type="warning"
        show-icon
        :closable="false"
      >
        警告: 未检测到M1/M2乳突通道
      </el-alert>
      
      <!-- 操作按钮 - 位于表单底部，水平居中 -->
      <el-form-item class="action-item">
        <el-button 
          type="primary" 
          @click="applyReference" 
          :loading="isLoading.processing"
          :disabled="!originalData"
          size="small"
        >
          应用重参考
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.reference-processor {
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

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}

:deep(.el-radio__label) {
  font-size: 12px;
}

.help-text {
  margin-bottom: 5px;
  color: #606266;
  font-size: 12px;
}

/* 重参考解释的样式 */
.reference-explanation {
  margin: 8px 0;
  padding: 0 8px;
  border-left: 2px solid #909399;
}

.explanation-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  margin: 0;
}
</style> 