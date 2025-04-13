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

// 应用滤波
const applyFilter = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 参数验证
    if (props.preprocessParams.filter.highpass_filter && 
        (props.preprocessParams.filter.highpass <= 0 || props.preprocessParams.filter.highpass >= 100)) {
      throw new Error('高通滤波截止频率必须在0-100Hz之间');
    }

    if (props.preprocessParams.filter.lowpass_filter && 
        (props.preprocessParams.filter.lowpass <= 0 || props.preprocessParams.filter.lowpass >= 500)) {
      throw new Error('低通滤波截止频率必须在0-500Hz之间');
    }

    console.log('应用滤波器，参数:', {
      highpass_filter: props.preprocessParams.filter.highpass_filter,
      highpass: props.preprocessParams.filter.highpass,
      lowpass_filter: props.preprocessParams.filter.lowpass_filter,
      lowpass: props.preprocessParams.filter.lowpass,
      notch_filter: props.preprocessParams.filter.notch_filter,
      line_freqs: props.preprocessParams.filter.line_freqs
    });

    const response = await withLoading(
      analysisService.applyFilter(props.datasetId, props.subjectId, {
        highpass_filter: props.preprocessParams.filter.highpass_filter,
        highpass: props.preprocessParams.filter.highpass,
        lowpass_filter: props.preprocessParams.filter.lowpass_filter,
        lowpass: props.preprocessParams.filter.lowpass,
        notch_filter: props.preprocessParams.filter.notch_filter,
        line_freqs: props.preprocessParams.filter.line_freqs
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    ElMessage.success('滤波器应用成功');
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
      <!-- 高通滤波 -->
      <el-form-item label="高通滤波">
        <div class="filter-control">
          <el-switch v-model="preprocessParams.filter.highpass_filter" />
          <el-input-number 
            v-if="preprocessParams.filter.highpass_filter"
            v-model="preprocessParams.filter.highpass" 
            :min="0.1" 
            :max="100" 
            :step="0.1"
            :disabled="!preprocessParams.filter.highpass_filter"
            size="small"
            class="small-input"
          />
          <span v-if="preprocessParams.filter.highpass_filter" class="unit">Hz</span>
        </div>
      </el-form-item>
      
      <!-- 低通滤波 -->
      <el-form-item label="低通滤波">
        <div class="filter-control">
          <el-switch v-model="preprocessParams.filter.lowpass_filter" />
          <el-input-number 
            v-if="preprocessParams.filter.lowpass_filter"
            v-model="preprocessParams.filter.lowpass" 
            :min="1" 
            :max="500" 
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
      
      <!-- 操作按钮 - 现在位于表单底部，水平居中 -->
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

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}

:deep(.el-checkbox__label) {
  font-size: 12px;
}
</style> 