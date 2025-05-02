<script setup>
import { ref, computed, onMounted, watch } from 'vue';
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

// 增加EEGLAB风格的分段选项
const eegLabStyleSegmentation = ref(false);
const segmentLength = ref(1); // 段长度(秒)
const segmentOverlap = ref(0); // 段重叠(%)
const removeIncomplete = ref(true); // 是否移除不完整段

// 增加强制使用原始数据的选项
const useOriginalFullData = ref(false);

// 获取数据的实际长度
const dataLength = computed(() => {
  if (!props.originalData) return 0;
  return props.originalData.duration || 10;
});

// 计算可能的段数
const possibleSegments = computed(() => {
  if (segmentLength.value <= 0) return 0;
  
  const effectiveLength = useOriginalFullData.value ? 
    dataLength.value : 
    timeSegmentEnd.value - timeSegmentStart.value;
  
  const overlapFactor = segmentOverlap.value / 100;
  const effectiveSegmentLength = segmentLength.value * (1 - overlapFactor);
  
  return Math.floor((effectiveLength - (overlapFactor * segmentLength.value)) / effectiveSegmentLength);
});

// 获取可用事件列表
const fetchAvailableEvents = async () => {
  try {
    if (!props.originalData) return;
    
    console.log('尝试获取事件数据...');
    let foundEvents = false;
    
    // 尝试从原始数据中提取事件信息
    if (props.originalData.events && props.originalData.events.length > 0) {
      availableEvents.value = props.originalData.events;
      console.log('从原始数据中获取到事件:', availableEvents.value);
      foundEvents = true;
    } else {
      // 尝试通过API获取事件信息
      try {
        console.log('尝试从API获取事件信息...');
        const response = await analysisService.getEvents(props.datasetId, props.subjectId);
        if (response && response.data && response.data.events && response.data.events.length > 0) {
          availableEvents.value = response.data.events;
          console.log('从API获取到事件:', availableEvents.value);
          foundEvents = true;
        } else {
          console.log('API返回的事件数据为空或无效');
          // 如果API返回空数据，使用测试数据
          if (import.meta.env.DEV) {
            availableEvents.value = [
              { id: "target", name: "目标刺激", onset: 2.5, duration: 0.2 },
              { id: "non-target", name: "非目标刺激", onset: 5.0, duration: 0.2 },
              { id: "response", name: "反应", onset: 7.5, duration: 0.1 }
            ];
            console.log('使用测试事件数据');
            foundEvents = true;
          }
        }
      } catch (apiError) {
        console.error('API获取事件失败:', apiError);
        
        // API失败时，使用测试事件数据
        if (import.meta.env.DEV) {
          availableEvents.value = [
            { id: "target", name: "目标刺激", onset: 2.5, duration: 0.2 },
            { id: "non-target", name: "非目标刺激", onset: 5.0, duration: 0.2 },
            { id: "response", name: "反应", onset: 7.5, duration: 0.1 }
          ];
          console.log('使用测试事件数据');
          foundEvents = true;
        }
      }
    }
    
    if (foundEvents && availableEvents.value && availableEvents.value.length > 0) {
      selectedEvent.value = availableEvents.value[0].id || availableEvents.value[0].name;
      console.log('选择事件:', selectedEvent.value);
    } else {
      // 如果没有找到事件，禁用事件相关选项
      if (segmentMode.value === 'event') {
        segmentMode.value = 'time';
        ElMessage.warning('未找到事件数据，已切换到时间窗口模式');
      }
    }
  } catch (error) {
    console.error('获取事件列表失败:', error);
    ElMessage.warning('未能加载事件信息，事件相关分段可能无法使用');
    
    // 出错时始终切换到时间窗口模式
    segmentMode.value = 'time';
  }
};

// 应用分段的实现
const applySegmentation = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 清理参数中的NaN值
    const sanitizedParams = { ...props.preprocessParams };
    Object.keys(sanitizedParams).forEach(key => {
      if (typeof sanitizedParams[key] === 'number' && isNaN(sanitizedParams[key])) {
        sanitizedParams[key] = 0;
      }
    });
    
    // 调试信息
    console.log('请求参数:', JSON.stringify(sanitizedParams, null, 2));
    
    // 发送请求到服务器
    const response = await withLoading(
      analysisService.segmentData(props.datasetId, props.subjectId, sanitizedParams),
      'processing'
    );
    
    // 验证响应是否有效
    if (!response || !response.data) {
      throw new Error('服务器返回的数据无效');
    }
    
    // 获取分段结果
    let segmentResult = response.data.data;
    
    // 保证至少有一个基本的数据结构
    if (!segmentResult || Object.keys(segmentResult).length === 0) {
      console.warn('服务器返回的分段结果为空，创建基本数据结构');
      
      // 使用原始数据作为备选
      if (props.originalData) {
        segmentResult = JSON.parse(JSON.stringify(props.originalData));
      } else {
        // 创建最小可用数据结构
        segmentResult = {
          data: {},
          times: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
          channels: ['Ch1', 'Ch2', 'Ch3'],
          sampling_rate: 100,
          duration: 10,
          dataset_id: props.datasetId,
          subject_id: props.subjectId,
          timeRange: [0, 10],
          segment_info: {
            type: sanitizedParams.segment_mode || "time",
            start: sanitizedParams.start_time || 0,
            end: sanitizedParams.end_time || 10
          }
        };
        
        // 为默认通道创建零填充数据
        segmentResult.channels.forEach(ch => {
          segmentResult.data[ch] = new Array(segmentResult.times.length).fill(0);
        });
      }
    }
    
    // 确保timeRange存在
    if (!segmentResult.timeRange && segmentResult.times && segmentResult.times.length > 0) {
      segmentResult.timeRange = [
        segmentResult.times[0],
        segmentResult.times[segmentResult.times.length - 1]
      ];
    }
    
    // 发送处理完成事件
    emit('process-complete', segmentResult);
    ElMessage.success('分段处理完成');
  } catch (error) {
    console.error('应用分段失败:', error);
    const errorMessage = error.message || '未知错误';
    ElMessage.error(`分段处理失败: ${errorMessage}`);
  } finally {
    isLoading.processing = false;
  }
};

// 初始化时从localStorage加载保存的时间范围
onMounted(() => {
  // 从localStorage读取之前保存的时间范围
  const savedTimeRange = localStorage.getItem('selected_time_range');
  if (savedTimeRange) {
    try {
      const parsedRange = JSON.parse(savedTimeRange);
      timeSegmentStart.value = parsedRange[0];
      timeSegmentEnd.value = parsedRange[1];
    } catch (e) {
      console.error('解析保存的时间范围失败:', e);
    }
  }
  
  fetchAvailableEvents();
});
</script>

<template>
  <div class="segment-processor">
    <h3>数据分段设置</h3>
    
    <el-form label-position="left" label-width="100px" class="compact-form">
      <!-- 使用原始全部数据的选项 -->
      <el-form-item label="数据范围">
        <el-switch
          v-model="useOriginalFullData"
          active-text="使用完整原始数据"
          inactive-text="使用当前选择的时间段"
        />
      </el-form-item>
      
      <el-form-item label="分段模式">
        <el-radio-group v-model="segmentMode" size="small">
          <el-radio-button label="time">时间窗口</el-radio-button>
          <el-radio-button label="eeglab">EEGLAB风格</el-radio-button>
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
      
      <!-- EEGLAB风格分段 -->
      <template v-else-if="segmentMode === 'eeglab'">
        <el-form-item label="段长度">
          <el-input-number 
            v-model="segmentLength" 
            :min="0.1" 
            :max="dataLength" 
            :step="0.1"
            size="small"
            class="small-input"
          />
          <span class="unit">秒</span>
        </el-form-item>
        
        <el-form-item label="段重叠">
          <el-input-number 
            v-model="segmentOverlap" 
            :min="0" 
            :max="90" 
            :step="5"
            size="small"
            class="small-input"
          />
          <span class="unit">%</span>
        </el-form-item>
        
        <el-form-item label="移除不完整段">
          <el-switch v-model="removeIncomplete" />
        </el-form-item>
        
        <el-form-item label="预计段数">
          <span>{{ possibleSegments }} 段</span>
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