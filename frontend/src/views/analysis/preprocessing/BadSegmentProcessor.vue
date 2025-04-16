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

// 坏段检测方法
const detectionMethod = ref('auto'); // 'auto', 'threshold', 'manual'

// 阈值设置
const amplitudeThreshold = ref(100); // μV
const gradientThreshold = ref(10); // μV/ms

// 坏段信息
const badSegments = ref([]);

// 自动检测坏段
const detectBadSegments = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    const params = {
      detection_method: detectionMethod.value,
      amplitude_threshold: amplitudeThreshold.value,
      gradient_threshold: gradientThreshold.value
    };

    // 实际API调用
    const response = await withLoading(
      analysisService.detectBadSegments(props.datasetId, props.subjectId, params),
      'processing'
    );
    
    // 处理响应
    badSegments.value = response.data.bad_segments || [];

    ElMessage.success(`检测到 ${badSegments.value.length} 个坏数据段`);
  } catch (error) {
    console.error('坏段检测失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`坏段检测失败: ${errorMessage}`);
  }
};

// 应用坏段剔除
const applyBadSegmentRejection = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  if (badSegments.value.length === 0) {
    ElMessage.warning('未检测到坏段，请先运行检测');
    return;
  }

  try {
    const params = {
      bad_segments: badSegments.value,
      reject_method: 'zero' // 'zero', 'interpolate', 'remove'
    };

    // TODO: 实际API调用
    // const response = await withLoading(
    //   analysisService.rejectBadSegments(props.datasetId, props.subjectId, params),
    //   'processing'
    // );
    
    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const response = {
      data: {
        ...props.originalData,
        // 标记剔除的坏段
        removed_segments: badSegments.value,
        from_cache: false,
        process_time: 0.7
      }
    };

    emit('process-complete', response.data);
    ElMessage.success('坏段剔除应用成功');
  } catch (error) {
    console.error('应用坏段剔除失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用坏段剔除失败: ${errorMessage}`);
  }
};
</script>

<template>
  <div class="bad-segment-processor">
    <h3>坏段检测与剔除</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <el-form-item label="检测方法">
        <el-select v-model="detectionMethod" size="small">
          <el-option label="自动检测" value="auto" />
          <el-option label="阈值检测" value="threshold" />
          <el-option label="手动标记" value="manual" />
        </el-select>
      </el-form-item>
      
      <!-- 阈值检测参数 -->
      <template v-if="detectionMethod === 'threshold'">
        <el-form-item label="振幅阈值">
          <el-input-number 
            v-model="amplitudeThreshold" 
            :min="10" 
            :max="500" 
            :step="10"
            size="small"
            class="small-input"
          />
          <span class="unit">μV</span>
        </el-form-item>
        
        <el-form-item label="梯度阈值">
          <el-input-number 
            v-model="gradientThreshold" 
            :min="1" 
            :max="50" 
            :step="1"
            size="small"
            class="small-input"
          />
          <span class="unit">μV/ms</span>
        </el-form-item>
      </template>
      
      <!-- 检测的坏段列表 -->
      <el-form-item label="检测结果" v-if="badSegments.length > 0">
        <div class="bad-segment-list">
          <div v-for="(segment, index) in badSegments" :key="index" class="bad-segment-item">
            <div class="segment-time">
              {{ segment.start.toFixed(1) }}s - {{ segment.end.toFixed(1) }}s
            </div>
            <div class="segment-reason">{{ segment.reason }}</div>
          </div>
        </div>
      </el-form-item>
      
      <!-- 操作按钮 -->
      <el-form-item class="action-item">
        <el-button 
          @click="detectBadSegments" 
          :loading="isLoading.processing"
          :disabled="!originalData"
          size="small"
        >
          检测坏段
        </el-button>
        
        <el-button 
          type="primary" 
          @click="applyBadSegmentRejection" 
          :loading="isLoading.processing"
          :disabled="!originalData || badSegments.length === 0"
          size="small"
        >
          应用剔除
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.bad-segment-processor {
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

.unit {
  margin-left: 5px;
  color: #606266;
  font-size: 12px;
}

.bad-segment-list {
  max-height: 120px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 5px;
}

.bad-segment-item {
  padding: 5px;
  margin-bottom: 5px;
  border-bottom: 1px solid #f2f6fc;
}

.bad-segment-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.segment-time {
  font-weight: bold;
  font-size: 12px;
}

.segment-reason {
  font-size: 11px;
  color: #909399;
}

.action-item {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
}
</style>