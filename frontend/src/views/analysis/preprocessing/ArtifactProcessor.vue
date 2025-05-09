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

// 记录处理结果
const processingResult = ref(null);

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

    // 处理通道参数
    const channels = props.processingChannels.length > 0 ? 
      props.processingChannels : 
      props.originalData.channels;
    
    if (!channels || channels.length === 0) {
      throw new Error('没有可用的处理通道');
    }

    console.log('伪迹处理参数:', {
      ...props.preprocessParams.artifacts,
      channels
    });

    // 调用后端API执行伪迹处理
    const response = await withLoading(
      analysisService.removeArtifacts(props.datasetId, props.subjectId, {
        ...props.preprocessParams.artifacts,
        channels // 传递处理通道
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    // 保存处理结果的信息
    processingResult.value = response.data;
    
    // 检查是否有伪迹处理信息
    if (response.data.segment_info && response.data.segment_info.artifact_info) {
      processingResult.value.artifact_info = response.data.segment_info.artifact_info;
    }

    // 保留原始时间范围
    if (props.originalData.timeRange && !response.data.timeRange) {
      response.data.timeRange = props.originalData.timeRange;
    }

    emit('process-complete', response.data);
    
    // 显示成功消息
    ElMessage.success('伪迹处理成功');
  } catch (error) {
    console.error('应用伪迹处理失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用伪迹处理失败: ${errorMessage}`);
  }
};

// 伪迹方法说明
const artifactMethodDescriptions = {
  threshold: {
    name: "幅度阈值",
    description: "检测并处理超出设定幅度阈值的信号"
  },
  ica: {
    name: "基于ICA",
    description: "利用ICA分析结果移除已识别的伪迹组件"
  },
  wavelet: {
    name: "小波分析",
    description: "使用小波变换检测和移除突发伪迹"
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
      
      <!-- 伪迹处理说明 -->
      <div class="artifact-explanation" v-if="preprocessParams.artifacts.remove_artifacts">
        <p class="explanation-text">
          伪迹处理用于检测和去除EEG信号中的非大脑活动，如肌肉活动、电极位移等。有效的伪迹处理可提高信号质量和分析可靠性。
        </p>
      </div>
      
      <template v-if="preprocessParams.artifacts.remove_artifacts">
        <el-form-item label="检测方法">
          <el-select v-model="preprocessParams.artifacts.artifact_detection_method" size="small">
            <el-option label="幅度阈值" value="threshold" />
            <el-option label="基于ICA" value="ica" />
            <el-option label="小波分析" value="wavelet" />
          </el-select>
          <div class="method-description" v-if="artifactMethodDescriptions[preprocessParams.artifacts.artifact_detection_method]">
            <small>{{ artifactMethodDescriptions[preprocessParams.artifacts.artifact_detection_method].description }}</small>
          </div>
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
          <div class="help-text">
            <small>超过此阈值的信号将被视为伪迹</small>
          </div>
        </el-form-item>
        
        <el-form-item label="处理方式">
          <el-select v-model="preprocessParams.artifacts.artifact_handling" size="small">
            <el-option label="线性插值" value="interpolate" />
            <el-option label="置零" value="zero" />
            <el-option label="移除" value="remove" />
          </el-select>
          <div class="help-text">
            <small>
              <template v-if="preprocessParams.artifacts.artifact_handling === 'interpolate'">
                使用线性插值替换伪迹
              </template>
              <template v-if="preprocessParams.artifacts.artifact_handling === 'zero'">
                将伪迹区域置为零值
              </template>
              <template v-if="preprocessParams.artifacts.artifact_handling === 'remove'">
                从数据中移除伪迹区域
              </template>
            </small>
          </div>
        </el-form-item>
        
        <el-form-item label="按标记拒绝">
          <el-switch v-model="preprocessParams.artifacts.reject_by_annotation" />
          <div class="help-text" v-if="preprocessParams.artifacts.reject_by_annotation">
            <small>拒绝带有标记的时间段</small>
          </div>
        </el-form-item>
      </template>
      
      <!-- 处理结果信息 -->
      <div v-if="processingResult" class="result-info">
        <el-alert
          type="success"
          :closable="false"
          show-icon
        >
          <template #title>
            伪迹处理完成
          </template>
          <div>
            <p>处理通道数: {{ processingResult.channels ? processingResult.channels.length : 0 }}</p>
            <p v-if="processingResult.artifact_info">
              检测到的伪迹区域: {{ processingResult.artifact_info.detected_segments || 0 }} 个
            </p>
            <p v-if="processingResult.artifact_info && processingResult.artifact_info.method">
              使用方法: {{ artifactMethodDescriptions[processingResult.artifact_info.method]?.name || processingResult.artifact_info.method }}
            </p>
            <p v-if="processingResult.artifact_info && processingResult.artifact_info.handling">
              处理方式: {{ 
                processingResult.artifact_info.handling === 'interpolate' ? '线性插值' : 
                processingResult.artifact_info.handling === 'zero' ? '置零' : 
                processingResult.artifact_info.handling === 'remove' ? '移除' : 
                processingResult.artifact_info.handling 
              }}
            </p>
          </div>
        </el-alert>
      </div>
      
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
  max-width: 280px;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
  border-bottom: 1px solid #EBEEF5;
  padding-bottom: 8px;
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

/* 伪迹说明样式 */
.artifact-explanation {
  margin: 8px 0 16px;
  padding: 0 8px;
  border-left: 3px solid #409EFF;
  background-color: #ecf5ff;
  border-radius: 0 4px 4px 0;
}

.explanation-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  margin: 8px 0;
}

.method-description {
  margin-top: 4px;
  color: #606266;
  font-size: 12px;
  padding-left: 4px;
}

.help-text {
  margin-top: 4px;
  color: #606266;
  font-size: 12px;
}

.result-info {
  margin: 12px 0;
}
</style> 