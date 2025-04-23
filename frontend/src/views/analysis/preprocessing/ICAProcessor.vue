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

// 应用ICA分析
const applyICA = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 参数验证
    if (props.preprocessParams.ica.n_components <= 0) {
      throw new Error('组件数量必须大于0');
    }

    // TODO: 实际的ICA API调用实现
    ElMessage.info('ICA分析功能正在开发中');
    
    /* 当后端API完成后，可以使用类似的代码
    const response = await withLoading(
      analysisService.runICA(props.datasetId, props.subjectId, {
        run_ica: props.preprocessParams.ica.run_ica,
        ica_method: props.preprocessParams.ica.ica_method,
        n_components: props.preprocessParams.ica.n_components,
        auto_detect_artifacts: props.preprocessParams.ica.auto_detect_artifacts,
        channels: props.processingChannels // 传递处理通道
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    ElMessage.success('ICA分析应用成功');
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
      ElMessage.success('ICA分析模拟应用成功');
    }, 1000);
    
  } catch (error) {
    console.error('应用ICA分析失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用ICA分析失败: ${errorMessage}`);
  }
};
</script>

<template>
  <div class="ica-processor">
    <h3>ICA分析设置</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <el-form-item label="运行ICA">
        <el-switch v-model="preprocessParams.ica.run_ica" />
      </el-form-item>
      
      <template v-if="preprocessParams.ica.run_ica">
        <el-form-item label="ICA方法">
          <el-select v-model="preprocessParams.ica.ica_method" size="small">
            <el-option label="FastICA" value="fastica" />
            <el-option label="InfoMax" value="infomax" />
            <el-option label="Extended-InfoMax" value="extended-infomax" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="组件数量">
          <el-input-number 
            v-model="preprocessParams.ica.n_components" 
            :min="5" 
            :max="50" 
            :step="1"
            size="small"
            class="small-input"
          />
          <el-tooltip content="设置为0表示自动选择组件数量" placement="top">
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </el-form-item>
        
        <el-form-item label="自动检测">
          <el-switch 
            v-model="preprocessParams.ica.auto_detect_artifacts"
            :disabled="!preprocessParams.ica.run_ica"
          />
        </el-form-item>
      </template>
      
      <!-- 操作按钮 - 位于表单底部，水平居中 -->
      <el-form-item class="action-item">
        <el-button 
          type="primary" 
          @click="applyICA" 
          :loading="isLoading.processing"
          :disabled="!originalData || !preprocessParams.ica.run_ica"
          size="small"
        >
          运行ICA分析
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.ica-processor {
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

.small-input {
  width: 80px;
}

.info-icon {
  margin-left: 8px;
  color: #909399;
  cursor: help;
}

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}
</style> 