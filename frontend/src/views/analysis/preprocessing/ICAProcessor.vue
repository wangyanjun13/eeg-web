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

// 记录处理结果
const processingResult = ref(null);
const excludedComponents = ref([]);

// 计算建议的组件数量
const suggestedComponents = computed(() => {
  if (props.processingChannels && props.processingChannels.length > 0) {
    // 最大组件数量为通道数的70%，常用经验值
    return Math.max(5, Math.min(15, Math.floor(props.processingChannels.length * 0.7)));
  }
  return 10; // 默认值
});

// 当组件加载时，设置默认值
const initializeDefaults = () => {
  if (props.preprocessParams && props.preprocessParams.ica) {
    // 如果n_components未设置或为0，使用建议值
    if (!props.preprocessParams.ica.n_components || props.preprocessParams.ica.n_components <= 0) {
      props.preprocessParams.ica.n_components = suggestedComponents.value;
    }
    
    // 确保设置了默认ICA方法
    if (!props.preprocessParams.ica.ica_method) {
      props.preprocessParams.ica.ica_method = 'infomax';
    }
    
    // 默认启用自动检测伪迹
    if (props.preprocessParams.ica.auto_detect_artifacts === undefined) {
      props.preprocessParams.ica.auto_detect_artifacts = true;
    }
  }
};

// 应用ICA分析
const applyICA = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  // 重置处理结果
  processingResult.value = null;
  excludedComponents.value = [];

  try {
    // 参数验证
    if (props.preprocessParams.ica.n_components <= 0) {
      throw new Error('组件数量必须大于0');
    }

    // 处理通道参数
    const channels = props.processingChannels.length > 0 ? 
      props.processingChannels : 
      props.originalData.channels;
    
    if (!channels || channels.length === 0) {
      throw new Error('没有可用的处理通道');
    }
    
    // 确保在ICA参数中更新当前处理通道
    props.preprocessParams.ica.channels = channels;

    console.log('ICA参数:', {
      ...props.preprocessParams.ica,
      channels
    });

    // 调用后端API执行ICA
    const response = await withLoading(
      analysisService.runICA(props.datasetId, props.subjectId, {
        ...props.preprocessParams.ica,
        channels // 传递处理通道
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    // 保存处理结果的信息
    processingResult.value = response.data;
    
    // 提取被排除的组件信息
    if (response.data.segment_info && response.data.segment_info.ica_info) {
      excludedComponents.value = response.data.segment_info.ica_info.excluded_components || [];
    }

    // 保留原始时间范围
    if (props.originalData.timeRange && !response.data.timeRange) {
      response.data.timeRange = props.originalData.timeRange;
    }

    emit('process-complete', response.data);
    
    // 根据是否自动检测和排除了组件，显示不同的成功消息
    if (props.preprocessParams.ica.auto_detect_artifacts && excludedComponents.value.length > 0) {
      ElMessage.success(`ICA分析成功，自动检测并排除了${excludedComponents.value.length}个伪迹组件`);
    } else {
      ElMessage.success('ICA分析应用成功');
    }
  } catch (error) {
    console.error('应用ICA分析失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用ICA分析失败: ${errorMessage}`);
  }
};

// ICA方法说明
const icaMethodDescriptions = {
  fastica: {
    name: "FastICA",
    description: "快速高效的ICA算法，适用于大多数EEG数据处理场景"
  },
  infomax: {
    name: "InfoMax",
    description: "最大化信息熵的算法，对非高斯信号分离效果好，稳定性高"
  }
};

// 计算当前选择的ICA方法描述
const currentMethodDescription = computed(() => {
  const method = props.preprocessParams.ica.ica_method;
  return method ? icaMethodDescriptions[method]?.description : "";
});

// 组件初始化
initializeDefaults();
</script>

<template>
  <div class="ica-processor">
    <h3>ICA分析设置</h3>
    
    <el-form label-position="left" label-width="120px" class="compact-form">
      <el-form-item label="运行ICA">
        <el-switch v-model="preprocessParams.ica.run_ica" />
      </el-form-item>
      
      <!-- ICA说明 -->
      <div class="ica-explanation">
        <p class="explanation-text">
          ICA (独立成分分析)用于分离EEG信号中的独立成分，帮助识别和去除眨眼、肌肉等伪迹。ICA可提高信号质量，去除干扰，增强脑电信号的可靠性。
        </p>
      </div>
      
      <template v-if="preprocessParams.ica.run_ica">
        <el-form-item label="ICA方法">
          <el-select v-model="preprocessParams.ica.ica_method" size="small" style="width: 100%">
            <el-option label="FastICA（快速）" value="fastica" />
            <el-option label="InfoMax（高精度）" value="infomax" />
          </el-select>
          <div class="method-description" v-if="currentMethodDescription">
            <small>{{ currentMethodDescription }}</small>
          </div>
        </el-form-item>
        
        <el-form-item label="组件数量">
          <el-input-number 
            v-model="preprocessParams.ica.n_components" 
            :min="1" 
            :max="processingChannels.length - 1"
            :step="1"
            size="small"
            class="small-input"
          />
          <div class="suggestion-text">
            <small>建议值: {{ suggestedComponents }} (最多{{ processingChannels.length - 1 }})</small>
          </div>
        </el-form-item>
        
        <el-form-item label="自动检测伪迹">
          <el-switch 
            v-model="preprocessParams.ica.auto_detect_artifacts"
            :disabled="!preprocessParams.ica.run_ica"
          />
          <div class="help-text" v-if="preprocessParams.ica.auto_detect_artifacts">
            <small>自动检测并移除眨眼等伪迹组件（基于眼电或前额通道相关性）</small>
          </div>
        </el-form-item>
        
        <!-- 处理结果信息 -->
        <div v-if="processingResult && excludedComponents.length > 0" class="result-info">
          <el-alert
            type="success"
            :closable="false"
            show-icon
          >
            <template #title>
              已自动排除 {{ excludedComponents.length }} 个伪迹组件
            </template>
            <div v-if="excludedComponents.length > 0">
              <p>排除的组件: {{ excludedComponents.join(', ') }}</p>
            </div>
          </el-alert>
        </div>
        
        <el-alert
          type="info"
          :closable="false"
          show-icon
          class="info-alert"
        >
          <p>当前处理通道数: {{ 
            preprocessParams.ica.channels ? 
            preprocessParams.ica.channels.length : 
            processingChannels.length 
          }}</p>
          <p>最大可设置组件数: {{ processingChannels.length - 1 }}</p>
          <p>组件越多分离越精细，但计算量越大</p>
        </el-alert>
        
        <!-- ICA说明卡片 -->
        <div class="ica-method-card">
          <h4>各类ICA方法说明</h4>
          <ul class="method-list">
            <li>
              <strong>FastICA</strong>: 快速计算，适合常规处理
            </li>
            <li>
              <strong>InfoMax</strong>: 精度高，适合复杂信号
            </li>
          </ul>
          <p class="tip">提示: 对于常规EEG数据，InfoMax通常效果最好且稳定性高</p>
        </div>
      </template>
      
      <!-- 操作按钮 - 位于表单底部，水平居中 -->
      <el-form-item class="action-item">
        <el-button 
          type="primary" 
          @click="applyICA" 
          :loading="isLoading.processing"
          :disabled="!originalData || !preprocessParams.ica.run_ica"
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
  max-width: 320px;
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

.small-input {
  width: 100px;
}

.suggestion-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
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

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* ICA说明样式 */
.ica-explanation {
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

.result-info {
  margin: 12px 0;
}

.info-alert {
  margin: 12px 0;
}

.ica-method-card {
  margin-top: 15px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  padding: 12px;
  background-color: #F5F7FA;
}

.ica-method-card h4 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #303133;
}

.method-list {
  padding-left: 20px;
  margin: 8px 0;
}

.method-list li {
  margin-bottom: 4px;
  font-size: 12px;
  color: #606266;
}

.tip {
  font-size: 12px;
  color: #909399;
  font-style: italic;
  margin: 8px 0 0;
}
</style> 