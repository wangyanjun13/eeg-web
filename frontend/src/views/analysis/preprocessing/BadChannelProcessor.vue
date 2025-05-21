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
  processing: false,
  detecting: false
});

// 检测到的坏通道
const detectedBadChannels = ref([]);

// 自定义坏通道输入
const customBadChannelInput = ref('');

// 坏通道结果
const badChannelsResult = ref(null);

// 可用的通道列表
const availableChannels = computed(() => {
  if (props.processingChannels && props.processingChannels.length > 0) {
    return props.processingChannels;
  } else if (props.originalData && props.originalData.channels) {
    return props.originalData.channels;
  }
  return [];
});

// 更新自定义坏通道列表
const updateCustomBadChannels = () => {
  if (!customBadChannelInput.value) {
    props.preprocessParams.bad_channels.custom_bad_channels = [];
    return;
  }
  
  // 解析用逗号或空格分隔的通道名称
  const channels = customBadChannelInput.value
    .split(/[,\s]+/)
    .map(ch => ch.trim())
    .filter(ch => ch);
    
  // 验证通道名称有效性
  const validChannels = channels.filter(ch => 
    availableChannels.value.includes(ch)
  );
  
  if (validChannels.length !== channels.length) {
    ElMessage.warning('部分通道名称无效，已被过滤');
  }
  
  props.preprocessParams.bad_channels.custom_bad_channels = validChannels;
  
  // 如果有有效通道，自动开启使用自定义坏通道
  if (validChannels.length > 0) {
    props.preprocessParams.bad_channels.use_custom_bads = true;
  }
};

// 添加测试模式开关
const testModeEnabled = ref(false);

// 检测是否为开发环境
const isDevelopment = typeof process !== 'undefined' && 
                       process.env && 
                       process.env.NODE_ENV === 'development';

// 检测坏通道
const detectBadChannels = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 发送实际的坏通道检测API调用，添加测试模式参数
    const response = await withLoading(
      analysisService.detectBadChannels(props.datasetId, props.subjectId, {
        detect_bad_channels: props.preprocessParams.bad_channels.detect_bad_channels,
        bad_channel_method: props.preprocessParams.bad_channels.bad_channel_method,
        threshold: props.preprocessParams.bad_channels.threshold,
        use_custom_bads: false, // 检测阶段不使用自定义列表
        rejection_mode: "zero", // 检测阶段使用零填充模式
        test_mode_trigger: testModeEnabled.value // 添加测试模式参数
      }),
      'detecting'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    badChannelsResult.value = response.data;
    detectedBadChannels.value = response.data.bad_channels || [];
    
    ElMessage.success(`检测到 ${detectedBadChannels.value.length} 个坏通道`);
    
    // 如果有检测结果，自动关闭自定义坏通道模式
    if (detectedBadChannels.value.length > 0) {
      props.preprocessParams.bad_channels.use_custom_bads = false;
    }
  } catch (error) {
    console.error('坏通道检测失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`坏通道检测失败: ${errorMessage}`);
  }
};

// 应用坏通道处理
const applyBadChannelProcessing = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 确定使用的坏通道列表
    let badChannelsList = [];
    
    if (props.preprocessParams.bad_channels.use_custom_bads) {
      // 使用自定义列表
      if (!props.preprocessParams.bad_channels.custom_bad_channels || 
          props.preprocessParams.bad_channels.custom_bad_channels.length === 0) {
        updateCustomBadChannels(); // 尝试从输入框更新
      }
      
      badChannelsList = props.preprocessParams.bad_channels.custom_bad_channels || [];
      
      if (badChannelsList.length === 0) {
        ElMessage.warning('自定义坏通道列表为空，请输入有效的通道名称');
        return;
      }
    } else {
      // 使用检测结果
      if (!detectedBadChannels.value || detectedBadChannels.value.length === 0) {
        ElMessage.warning('未检测到坏通道，请先运行检测或提供自定义列表');
        return;
      }
      
      badChannelsList = detectedBadChannels.value;
    }
    
    // 发送处理请求
    const response = await withLoading(
      analysisService.detectBadChannels(props.datasetId, props.subjectId, {
        detect_bad_channels: props.preprocessParams.bad_channels.detect_bad_channels,
        bad_channel_method: props.preprocessParams.bad_channels.bad_channel_method,
        threshold: props.preprocessParams.bad_channels.threshold,
        rejection_mode: props.preprocessParams.bad_channels.rejection_mode,
        use_custom_bads: props.preprocessParams.bad_channels.use_custom_bads,
        custom_bad_channels: badChannelsList
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    ElMessage.success(`坏通道处理成功，处理模式: ${props.preprocessParams.bad_channels.rejection_mode}`);
  } catch (error) {
    console.error('坏通道处理失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`坏通道处理失败: ${errorMessage}`);
  }
};
</script>

<template>
  <div class="bad-channel-processor">
    <h3>坏通道检测与处理</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <el-form-item label="开启检测">
        <el-switch v-model="preprocessParams.bad_channels.detect_bad_channels" />
      </el-form-item>
      
      <el-form-item label="检测方法" v-if="preprocessParams.bad_channels.detect_bad_channels">
        <el-select v-model="preprocessParams.bad_channels.bad_channel_method" size="small">
          <el-option label="相关性方法" value="correlation" />
          <el-option label="方差法" value="variance" />
          <el-option label="功率谱法" value="spectrum" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="处理方式" v-if="preprocessParams.bad_channels.detect_bad_channels">
        <el-select v-model="preprocessParams.bad_channels.rejection_mode" size="small">
          <el-option label="置零" value="zero" />
          <el-option label="插值" value="interpolate" />
          <el-option label="移除" value="remove" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="自定义">
        <el-switch v-model="preprocessParams.bad_channels.use_custom_bads" />
      </el-form-item>
      
      <el-form-item label="通道列表" v-if="preprocessParams.bad_channels.use_custom_bads">
        <el-input 
          v-model="customBadChannelInput"
          type="textarea"
          :rows="2"
          placeholder="输入通道名称，用逗号分隔"
          @blur="updateCustomBadChannels"
        />
      </el-form-item>
      
      <el-form-item label="检测结果" v-if="detectedBadChannels.length > 0">
        <div class="bad-channels-container">
          <el-tag 
            v-for="channel in detectedBadChannels" 
            :key="channel"
            type="danger"
            class="bad-channel-tag"
            size="small"
          >
            {{ channel }}
          </el-tag>
        </div>
      </el-form-item>
      
      <!-- 操作按钮 - 位于表单底部 -->
      <el-form-item class="action-item">
        <div class="action-buttons">
          <el-button 
            size="small"
            @click="detectBadChannels" 
            :loading="isLoading.detecting"
            :disabled="!originalData || !preprocessParams.bad_channels.detect_bad_channels"
            class="detect-btn"
          >
            检测坏通道
          </el-button>
          
          <el-button 
            type="primary" 
            size="small"
            @click="applyBadChannelProcessing" 
            :loading="isLoading.processing"
            :disabled="!originalData || 
                      (!preprocessParams.bad_channels.use_custom_bads && detectedBadChannels.length === 0)"
          >
            处理坏通道
          </el-button>
        </div>
      </el-form-item>
      
      <el-form-item v-if="isDevelopment" label="测试模式">
        <el-switch v-model="testModeEnabled" />
        <div v-if="testModeEnabled" class="help-text">
          测试模式将模拟坏通道数据
        </div>
      </el-form-item>
    </el-form>
    
    <div v-if="badChannelsResult && badChannelsResult.from_cache" class="cache-info">
      <el-tag size="small" type="success">从缓存加载 ({{ badChannelsResult.process_time.toFixed(2) }}秒)</el-tag>
    </div>
  </div>
</template>

<style scoped>
.bad-channel-processor {
  padding: 10px;
  max-width: 260px;
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

.bad-channels-container {
  max-height: 100px;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
}

.bad-channel-tag {
  margin-right: 4px;
  margin-bottom: 4px;
  font-size: 10px;
}

.action-item {
  margin-top: 15px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.cache-info {
  margin-top: 10px;
  font-size: 12px;
}

.detect-btn {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

.detect-btn:hover {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  opacity: 0.9 !important;
}
</style> 