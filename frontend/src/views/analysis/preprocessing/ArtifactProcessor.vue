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
  }
});

const emit = defineEmits(['process-complete']);

const { isLoading, withLoading } = useLoading({
  processing: false
});

// 应用伪迹移除
const removeArtifacts = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 参数验证
    if (props.preprocessParams.artifacts.remove_artifacts && 
        props.preprocessParams.artifacts.artifact_detection_method === 'threshold' && 
        props.preprocessParams.artifacts.amplitude_threshold <= 0) {
      throw new Error('幅度阈值必须大于0');
    }

    // TODO: 实际的伪迹移除API调用
    ElMessage.info('伪迹移除功能正在开发中');
    
    /* 当后端API完成后，可以使用类似的代码
    const response = await withLoading(
      analysisService.removeArtifacts(props.datasetId, props.subjectId, {
        remove_artifacts: props.preprocessParams.artifacts.remove_artifacts,
        artifact_detection_method: props.preprocessParams.artifacts.artifact_detection_method,
        amplitude_threshold: props.preprocessParams.artifacts.amplitude_threshold,
        reject_by_annotation: props.preprocessParams.artifacts.reject_by_annotation
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    ElMessage.success('伪迹移除成功');
    */
  } catch (error) {
    console.error('应用伪迹移除失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用伪迹移除失败: ${errorMessage}`);
  }
};
</script>

<template>
  <div class="artifact-processor">
    <h3>伪迹处理</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <el-form-item label="移除伪迹">
        <el-switch v-model="preprocessParams.artifacts.remove_artifacts" />
      </el-form-item>
      
      <template v-if="preprocessParams.artifacts.remove_artifacts">
        <el-form-item label="检测方法">
          <el-select v-model="preprocessParams.artifacts.artifact_detection_method" size="small">
            <el-option label="幅度阈值" value="threshold" />
            <el-option label="基于ICA" value="ica" />
            <el-option label="小波分析" value="wavelet" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="幅度阈值" v-if="preprocessParams.artifacts.artifact_detection_method === 'threshold'">
          <el-input-number 
            v-model="preprocessParams.artifacts.amplitude_threshold" 
            :min="10" 
            :max="500" 
            :step="5"
            size="small"
            class="small-input"
          />
          <span class="unit">μV</span>
        </el-form-item>
        
        <el-form-item label="按标记拒绝">
          <el-switch v-model="preprocessParams.artifacts.reject_by_annotation" />
          <el-tooltip content="拒绝带有标记的时间段" placement="top">
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </el-form-item>
      </template>
      
      <!-- 操作按钮 - 位于表单底部，水平居中 -->
      <el-form-item class="action-item">
        <el-button 
          type="primary" 
          @click="removeArtifacts" 
          :loading="isLoading.processing"
          :disabled="!originalData || !preprocessParams.artifacts.remove_artifacts"
          size="small"
        >
          移除伪迹
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.artifact-processor {
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

.info-icon {
  margin-left: 8px;
  color: #909399;
  cursor: help;
}

.small-input {
  width: 80px;
}

.unit {
  margin-left: 5px;
  color: #606266;
  font-size: 12px;
}

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}
</style> 