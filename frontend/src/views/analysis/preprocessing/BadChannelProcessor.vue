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

// 检测到的坏通道
const detectedBadChannels = ref([]);

// 可用的通道列表
const availableChannels = computed(() => {
  if (props.processingChannels && props.processingChannels.length > 0) {
    return props.processingChannels;
  } else if (props.originalData && props.originalData.channels) {
    return props.originalData.channels;
  }
  return [];
});

// 检测坏通道
const detectBadChannels = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // TODO: 实际的坏通道检测API调用
    ElMessage.info('坏通道检测功能正在开发中');
    
    /* 当后端API完成后，可以使用类似的代码
    const response = await withLoading(
      analysisService.detectBadChannels(props.datasetId, props.subjectId, {
        detect_bad_channels: props.preprocessParams.bad_channels.detect_bad_channels,
        bad_channel_method: props.preprocessParams.bad_channels.bad_channel_method,
        channels: props.processingChannels // 传递处理通道
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    detectedBadChannels.value = response.data.bad_channels || [];
    ElMessage.success(`检测到 ${detectedBadChannels.value.length} 个坏通道`);
    */
    
    // 模拟检测结果 - 开发测试用
    detectedBadChannels.value = availableChannels.value.slice(0, 3);
    ElMessage.success(`模拟检测: 发现 ${detectedBadChannels.value.length} 个坏通道`);
  } catch (error) {
    console.error('坏通道检测失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`坏通道检测失败: ${errorMessage}`);
  }
};

// 应用坏通道检测结果
const applyBadChannelRemoval = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  if (detectedBadChannels.value.length === 0) {
    ElMessage.warning('未检测到坏通道，请先运行检测');
    return;
  }

  try {
    // TODO: 实际的坏通道移除API调用
    ElMessage.info('坏通道移除功能正在开发中');
    
    /* 当后端API完成后，可以使用类似的代码
    const response = await withLoading(
      analysisService.removeBadChannels(props.datasetId, props.subjectId, {
        bad_channels: detectedBadChannels.value,
        channels: props.processingChannels // 传递处理通道
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    emit('process-complete', response.data);
    ElMessage.success('坏通道处理成功');
    */
    
    // 临时模拟
    setTimeout(() => {
      // 过滤掉坏通道
      const goodChannels = props.processingChannels.filter(ch => 
        !detectedBadChannels.value.includes(ch)
      );
      
      // 模拟后端返回的数据，保持通道一致性
      const simulatedData = {
        ...props.originalData,
        channels: goodChannels,
        // 移除坏通道的数据
        data: Object.fromEntries(
          goodChannels.map(ch => [ch, props.originalData.data[ch]])
        )
      };
      emit('process-complete', simulatedData);
      ElMessage.success('坏通道移除模拟应用成功');
    }, 1000);
    
  } catch (error) {
    console.error('坏通道处理失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`坏通道处理失败: ${errorMessage}`);
  }
};
</script>

<template>
  <div class="bad-channel-processor">
    <h3>坏通道检测</h3>
    
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
      
      <el-form-item label="检测到的坏通道" v-if="detectedBadChannels.length > 0">
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
            :loading="isLoading.processing"
            :disabled="!originalData || !preprocessParams.bad_channels.detect_bad_channels"
          >
            检测坏通道
          </el-button>
          
          <el-button 
            type="primary" 
            size="small"
            @click="applyBadChannelRemoval" 
            :loading="isLoading.processing"
            :disabled="!originalData || detectedBadChannels.length === 0"
          >
            处理坏通道
          </el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.bad-channel-processor {
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

.bad-channels-container {
  max-height: 100px;
  overflow-y: auto;
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
</style> 