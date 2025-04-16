<script setup>
import { ref, computed, onMounted } from 'vue';
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

// 分段模式
const segmentMode = ref('time'); // 'time', 'event', 'epoch'

// 时间分段参数
const timeSegmentStart = ref(0);
const timeSegmentEnd = ref(10);
const segmentDuration = computed(() => timeSegmentEnd.value - timeSegmentStart.value);

// 事件分段参数
const selectedEvent = ref('');
const preEventTime = ref(0.2);
const postEventTime = ref(0.8);
const availableEvents = ref([]);

// 基线校正参数
const applyBaseline = ref(true);
const baselineStart = ref(-0.2);
const baselineEnd = ref(0);

// 获取可用事件列表
const fetchAvailableEvents = async () => {
  try {
    if (!props.originalData) return;
    
    // 实际情况下应通过API获取
    availableEvents.value = props.originalData.events || [];
    
    if (availableEvents.value.length > 0) {
      selectedEvent.value = availableEvents.value[0].name;
    }
  } catch (error) {
    console.error('获取事件列表失败:', error);
    ElMessage.error('获取事件列表失败');
  }
};

// 应用分段
const applySegmentation = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    const params = {
      segment_mode: segmentMode.value,
      // 时间分段参数
      start_time: timeSegmentStart.value,
      end_time: timeSegmentEnd.value,
      // 事件分段参数
      event_name: selectedEvent.value,
      pre_event: preEventTime.value,
      post_event: postEventTime.value,
      // 额外是否应用基线校正
      apply_baseline: applyBaseline.value,
      baseline_start: baselineStart.value,
      baseline_end: baselineEnd.value
    };

    // TODO: 实际API调用
    // const response = await withLoading(
    //   analysisService.segmentData(props.datasetId, props.subjectId, params),
    //   'processing'
    // );
    
    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const response = {
      data: {
        ...props.originalData,
        // 模拟分段后的数据
        segment_info: {
          mode: segmentMode.value,
          segments: segmentMode.value === 'time' 
            ? [{ start: timeSegmentStart.value, end: timeSegmentEnd.value }]
            : [{ event: selectedEvent.value, pre: preEventTime.value, post: postEventTime.value }]
        },
        from_cache: false,
        process_time: 0.5
      }
    };

    emit('process-complete', response.data);
    ElMessage.success('数据分段应用成功');
  } catch (error) {
    console.error('应用分段失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用分段失败: ${errorMessage}`);
  }
};

// 组件挂载后获取事件列表
onMounted(fetchAvailableEvents);
</script>

<template>
  <div class="segment-processor">
    <h3>数据分段设置</h3>
    
    <el-form label-position="left" label-width="80px" class="compact-form">
      <el-form-item label="分段模式">
        <el-radio-group v-model="segmentMode" size="small">
          <el-radio-button label="time">时间窗口</el-radio-button>
          <el-radio-button label="event">事件相关</el-radio-button>
        </el-radio-group>
      </el-form-item>
      
      <!-- 时间窗口分段 -->
      <template v-if="segmentMode === 'time'">
        <el-form-item label="起始时间">
          <el-input-number 
            v-model="timeSegmentStart" 
            :min="0" 
            :max="originalData?.duration - 1 || 100" 
            :step="0.1"
            size="small"
            class="small-input"
          />
          <span class="unit">秒</span>
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-input-number 
            v-model="timeSegmentEnd" 
            :min="timeSegmentStart + 0.1" 
            :max="originalData?.duration || 100" 
            :step="0.1"
            size="small"
            class="small-input"
          />
          <span class="unit">秒</span>
        </el-form-item>
        
        <el-form-item label="分段长度">
          <span>{{ segmentDuration.toFixed(2) }} 秒</span>
        </el-form-item>
      </template>
      
      <!-- 事件相关分段 -->
      <template v-else-if="segmentMode === 'event'">
        <el-form-item label="选择事件">
          <el-select v-model="selectedEvent" size="small">
            <el-option 
              v-for="event in availableEvents" 
              :key="event.name" 
              :label="event.name" 
              :value="event.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="事件前">
          <el-input-number 
            v-model="preEventTime" 
            :min="0" 
            :max="10" 
            :step="0.1"
            size="small"
            class="small-input"
          />
          <span class="unit">秒</span>
        </el-form-item>
        
        <el-form-item label="事件后">
          <el-input-number 
            v-model="postEventTime" 
            :min="0" 
            :max="10" 
            :step="0.1"
            size="small"
            class="small-input"
          />
          <span class="unit">秒</span>
        </el-form-item>
        
        <el-form-item label="分段长度">
          <span>{{ (preEventTime + postEventTime).toFixed(2) }} 秒</span>
        </el-form-item>
      </template>
      
      <!-- 基线校正 -->
      <el-form-item label="基线校正">
        <el-switch v-model="applyBaseline" />
      </el-form-item>
      
      <template v-if="applyBaseline">
        <el-form-item label="基线窗口">
          <div class="baseline-range">
            <el-input-number 
              v-model="baselineStart" 
              :min="-2" 
              :max="0" 
              :step="0.1"
              size="small"
              class="small-input"
            />
            <span class="to-text">至</span>
            <el-input-number 
              v-model="baselineEnd" 
              :min="baselineStart" 
              :max="1" 
              :step="0.1"
              size="small"
              class="small-input"
            />
            <span class="unit">秒</span>
          </div>
        </el-form-item>
      </template>
      
      <!-- 操作按钮 -->
      <el-form-item class="action-item">
        <el-button 
          type="primary" 
          @click="applySegmentation" 
          :loading="isLoading.processing"
          :disabled="!originalData"
          size="small"
        >
          应用分段
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.segment-processor {
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

.to-text {
  margin: 0 5px;
  color: #606266;
  font-size: 12px;
}

.baseline-range {
  display: flex;
  align-items: center;
}

.action-item {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}
</style>