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

    // TODO: 实际的重参考API调用实现
    ElMessage.info('重参考功能正在开发中');
    
    /* 当后端API完成后，可以使用类似的代码
    const response = await withLoading(
      analysisService.applyReference(props.datasetId, props.subjectId, {
        reference: props.preprocessParams.reference.reference,
        custom_ref_channels: props.preprocessParams.reference.custom_ref_channels,
        channels: props.processingChannels // 传递处理通道
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    ElMessage.success('重参考应用成功');
    */
    
    // 临时模拟
    setTimeout(() => {
      // 模拟后端返回的数据，保持通道一致性
      const simulatedData = {
        ...props.originalData,
        channels: props.processingChannels,
        // 保持数据不变，但需确保通道列表与处理通道一致
        data: Object.fromEntries(
          props.processingChannels.map(ch => [ch, props.originalData.data[ch]])
        )
      };
      emit('process-complete', simulatedData);
      ElMessage.success('重参考模拟应用成功');
    }, 1000);
    
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
      
      <el-form-item label="参考通道" v-if="preprocessParams.reference.reference === 'custom'">
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
</style> 