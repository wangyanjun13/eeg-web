<script setup>
import { ref } from 'vue';
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

// 应用重采样
const applyResampling = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 参数验证
    if (props.preprocessParams.resample.resample && 
        (props.preprocessParams.resample.resample_freq <= 0)) {
      throw new Error('重采样频率必须大于0Hz');
    }

    // TODO: 实际的重采样API调用实现
    ElMessage.info('重采样功能正在开发中');
    
    /* 当后端API完成后，可以使用类似的代码
    const response = await withLoading(
      analysisService.applyResampling(props.datasetId, props.subjectId, {
        resample: props.preprocessParams.resample.resample,
        resample_freq: props.preprocessParams.resample.resample_freq,
        channels: props.processingChannels // 传递处理通道
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    ElMessage.success('重采样应用成功');
    */
    
    // 临时模拟
    setTimeout(() => {
      // 模拟后端返回的数据，保持通道一致性
      const simulatedData = {
        ...props.originalData,
        sampling_rate: props.preprocessParams.resample.resample_freq,
        channels: props.processingChannels,
        // 保持数据不变，但需确保通道列表与处理通道一致
        data: Object.fromEntries(
          props.processingChannels.map(ch => [ch, props.originalData.data[ch]])
        )
      };
      emit('process-complete', simulatedData);
      ElMessage.success('重采样模拟应用成功');
    }, 1000);
    
  } catch (error) {
    console.error('应用重采样失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用重采样失败: ${errorMessage}`);
  }
};
</script>

<template>
  <div class="resample-processor">
    <h3>重采样设置</h3>
    
    <el-form label-position="top" label-width="100px">
      <el-form-item label="启用重采样">
        <el-switch v-model="preprocessParams.resample.resample" />
      </el-form-item>
      
      <el-form-item label="采样频率" v-if="preprocessParams.resample.resample">
        <el-input-number 
          v-model="preprocessParams.resample.resample_freq" 
          :min="50" 
          :max="1000" 
          :step="10"
          size="small"
        />
        <span class="unit">Hz</span>
      </el-form-item>
      
      <el-alert 
        v-if="preprocessParams.resample.resample && originalData"
        type="info"
        show-icon
        :closable="false"
      >
        当前采样率: {{ originalData.sampling_rate }} Hz
      </el-alert>
    </el-form>
    
    <div class="actions">
      <el-button 
        type="primary" 
        @click="applyResampling" 
        :loading="isLoading.processing"
        :disabled="!originalData || !preprocessParams.resample.resample"
      >
        应用重采样
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.resample-processor {
  padding: 10px;
}

h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 18px;
  color: #303133;
}

.unit {
  margin-left: 5px;
  color: #606266;
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style> 