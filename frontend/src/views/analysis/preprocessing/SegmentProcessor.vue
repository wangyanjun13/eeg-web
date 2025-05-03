<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import analysisService from '@/services/analysisService';
import { useLoading } from '@/composables/useLoading';

const props = defineProps({
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

const emit = defineEmits(['update:processedData', 'process-complete']);

const { isLoading, withLoading } = useLoading({
  processing: false
});

// 分段模式
const segmentMode = ref('time'); // 'time', 'event'

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

// 增加强制使用原始数据的选项
const useOriginalFullData = ref(false);

// 事件类型计算属性
const uniqueEventTypes = computed(() => {
  const eventTypes = {};
  
  // 计算每种事件类型的数量
  for (const event of availableEvents.value) {
    const id = event.id || 'unknown';
    // 提取更友好的事件名称
    let name = event.name || id;
    // 如果名称是数字，添加"事件"前缀
    if (!isNaN(name) && name.trim() !== '') {
      name = `事件${name}`;
    }
    
    if (!eventTypes[id]) {
      eventTypes[id] = {
        id,
        name,
        count: 0
      };
    }
    
    eventTypes[id].count++;
  }
  
  // 转换为数组并排序：先按名称字母顺序，再按数量降序
  return Object.values(eventTypes).sort((a, b) => {
    // 首先按名称排序
    const nameCompare = a.name.localeCompare(b.name);
    if (nameCompare !== 0) return nameCompare;
    // 名称相同时按计数降序排序
    return b.count - a.count;
  });
});

// 获取可用事件列表
const fetchAvailableEvents = async () => {
  try {
    if (!props.datasetId || !props.subjectId) return;
    
    // 尝试通过API获取事件信息
    const response = await analysisService.getEvents(props.datasetId, props.subjectId);
    if (response && response.status === 'success' && response.data && response.data.events) {
      // 获取所有事件
      const allEvents = response.data.events;
      
      // 如果是时间窗口模式并且不使用完整数据，则过滤事件
      if (segmentMode.value === 'event' && !useOriginalFullData.value) {
        // 筛选当前时间窗口内的事件
        availableEvents.value = allEvents.filter(event => {
          const onset = parseFloat(event.onset || 0);
          return onset >= timeSegmentStart.value && onset <= timeSegmentEnd.value;
        });
        
        // 如果当前选中的事件在筛选后的列表中不存在，清空选择
        if (selectedEvent.value && !availableEvents.value.some(e => e.id == selectedEvent.value)) {
          selectedEvent.value = '';
        }
      } else {
        // 使用所有事件
        availableEvents.value = allEvents;
      }
      
      // 如果有事件，选择第一个事件类型
      if (availableEvents.value.length > 0 && uniqueEventTypes.value.length > 0) {
        if (!selectedEvent.value) {
          selectedEvent.value = uniqueEventTypes.value[0].id;
        }
      } else {
        selectedEvent.value = '';
      }
    } else {
      availableEvents.value = [];
      selectedEvent.value = '';
    }
  } catch (error) {
    availableEvents.value = [];
    selectedEvent.value = '';
  }
};

// 应用分段的实现
const applySegmentation = async () => {
  if (!props.originalData) {
    ElMessage.warning('请先加载原始数据');
    return;
  }

  try {
    // 收集分段参数
    const segmentParams = {
      segment_mode: segmentMode.value,
      use_original_full_data: useOriginalFullData.value,
      apply_baseline: applyBaseline.value,
      baseline_start: baselineStart.value,
      baseline_end: baselineEnd.value
    };
    
    // 根据分段模式设置不同参数
    if (segmentMode.value === 'time') {
      segmentParams.start_time = timeSegmentStart.value;
      segmentParams.end_time = timeSegmentEnd.value;
    } else if (segmentMode.value === 'event') {
      if (!selectedEvent.value) {
        ElMessage.warning('请选择事件类型');
        return;
      }
      
      // 验证所选事件类型在当前时间窗口中是否有事件
      if (!useOriginalFullData.value) {
        const eventsInWindow = availableEvents.value.filter(e => e.id == selectedEvent.value);
        if (eventsInWindow.length === 0) {
          ElMessage.warning(`当前时间窗口 ${timeSegmentStart.value}-${timeSegmentEnd.value}s 内没有找到 "${selectedEvent.value}" 类型的事件`);
          return;
        }
      }
      
      segmentParams.event_id = selectedEvent.value;
      segmentParams.time_before = preEventTime.value;
      segmentParams.time_after = postEventTime.value;
    }
    
    // 发送请求到服务器
    const response = await withLoading(
      analysisService.segmentData(props.datasetId, props.subjectId, segmentParams),
      'processing'
    );
    
    if (!response || !response.data) {
      throw new Error('服务器返回的数据无效');
    }
    
    // 获取分段结果
    const segmentResult = response.data;
    
    // 发送处理完成事件
    emit('process-complete', segmentResult);
    ElMessage.success('分段处理完成');
  } catch (error) {
    console.error('应用分段失败:', error);
    
    // 提取详细错误信息
    let errorMessage = error.message || '未知错误';
    if (error.response && error.response.data && error.response.data.detail) {
      errorMessage = error.response.data.detail;
    }
    
    // 给出更明确的错误提示
    if (errorMessage.includes('未找到指定的事件类型')) {
      ElMessage.error(`当前时间范围内未找到所选事件类型，请尝试选择其他事件类型或勾选"使用完整原始数据"`);
    } else {
      ElMessage.error(`分段处理失败: ${errorMessage}`);
    }
  }
};

// 初始化
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
  
  // 获取事件数据
  fetchAvailableEvents();
});

// 监听数据集和受试者变化
watch(
  () => [props.datasetId, props.subjectId], 
  () => {
    if (props.datasetId && props.subjectId) {
      fetchAvailableEvents();
    }
  },
  { immediate: true }
);

// 添加监听时间窗口变化的函数，自动更新事件列表
watch(
  [timeSegmentStart, timeSegmentEnd, useOriginalFullData, segmentMode],
  () => {
    if (props.datasetId && props.subjectId) {
      fetchAvailableEvents();
    }
  }
);
</script>

<template>
  <div class="segment-processor">
    <h3>数据分段设置</h3>
    
    <el-form label-position="left" label-width="100px" class="compact-form">
      <!-- 分段模式选择 -->
      <el-form-item label="分段模式">
        <el-radio-group v-model="segmentMode" size="small">
          <el-radio label="time">时间窗口</el-radio>
          <el-radio label="event" v-if="availableEvents.length > 0">事件相关</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 使用原始全部数据的选项 -->
      <el-form-item label="数据范围" v-if="segmentMode === 'time'">
        <el-switch
          v-model="useOriginalFullData"
          active-text="使用完整原始数据"
          inactive-text="使用当前选择的时间段"
        />
      </el-form-item>
      
      <!-- 时间窗口分段 -->
      <template v-if="segmentMode === 'time' && !useOriginalFullData">
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
        
        <!-- 添加回缺失的应用按钮 -->
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
      </template>
      
      <!-- 事件相关分段 -->
      <template v-if="segmentMode === 'event'">
        <div class="info-box" v-if="!useOriginalFullData && segmentMode === 'event'">
          <div class="info-title">
            <el-icon><Warning /></el-icon> 注意
          </div>
          <div class="info-content">
            您当前处理的是时间窗口 <strong>{{ timeSegmentStart }}-{{ timeSegmentEnd }}s</strong> 内的数据。
            事件分段将仅考虑此窗口内的事件。
          </div>
        </div>
        
        <!-- 当窗口内没有事件时显示警告 -->
        <div class="warning-box" v-if="!useOriginalFullData && availableEvents.length === 0">
          <div class="warning-title">
            <el-icon><Warning /></el-icon> 警告
          </div>
          <div class="warning-content">
            当前时间窗口 <strong>{{ timeSegmentStart }}-{{ timeSegmentEnd }}s</strong> 内没有找到任何事件。
            请尝试选择更大的时间窗口或勾选"使用完整原始数据"选项。
          </div>
          <el-button 
            size="small" 
            type="primary" 
            style="margin-top: 10px;"
            @click="useOriginalFullData = true"
          >
            使用完整数据
          </el-button>
        </div>
        
        <el-form-item v-if="availableEvents.length > 0" label="事件类型">
          <el-select 
            v-model="selectedEvent" 
            size="small" 
            placeholder="选择事件类型"
            style="width: 100%"
          >
            <el-option
              v-for="event in uniqueEventTypes"
              :key="event.id"
              :label="`${event.name} (${event.count}个)`"
              :value="event.id"
            />
          </el-select>
          <div class="form-help-text" v-if="uniqueEventTypes.length > 0">
            {{ segmentMode === 'time' && !useOriginalFullData ? 
               `当前时间窗口内有 ${uniqueEventTypes.length} 种事件类型，共 ${availableEvents.length} 个事件实例` : 
               `共有 ${uniqueEventTypes.length} 种事件类型，${availableEvents.length} 个事件实例` }}
          </div>
          <div class="warning-text" v-if="uniqueEventTypes.length === 0">
            当前时间窗口内没有找到任何事件，请尝试扩大时间窗口或选择"使用完整原始数据"
          </div>
        </el-form-item>
        
        <template v-if="availableEvents.length > 0">
          <el-form-item label="事件前时间" title="事件发生前的时间窗口，常用作基线校正">
            <el-input-number 
              v-model="preEventTime" 
              :min="0" 
              :max="2"
              :step="0.1"
              size="small"
              class="small-input"
            />
            <span class="unit">秒</span>
          </el-form-item>
          
          <el-form-item label="事件后时间" title="事件发生后的分析时间窗口">
            <el-input-number 
              v-model="postEventTime" 
              :min="0.1" 
              :max="5"
              :step="0.1"
              size="small"
              class="small-input"
            />
            <span class="unit">秒</span>
          </el-form-item>
          
          <div class="info-box info-event">
            <div class="info-title"><strong>事件相关分段说明</strong></div>
            <p>在事件相关分段中，时间以事件发生时刻为基准（0秒）：</p>
            <div class="event-timeline">
              <div class="timeline-marker start">-{{ preEventTime }}s</div>
              <div class="timeline-line">
                <div class="timeline-event">事件</div>
              </div>
              <div class="timeline-marker end">+{{ postEventTime }}s</div>
            </div>
            <p class="event-count">
              当前选择：{{ selectedEvent ? `${selectedEvent} 类事件` : '未选择' }}
              <span v-if="selectedEvent">
                (共{{ uniqueEventTypes.find(t => t.id == selectedEvent)?.count || 0 }}个)
              </span>
            </p>
          </div>
          
          <div class="info-text">
            选择事件相关模式将围绕每个选定类型的事件创建时间窗口，并叠加平均这些数据段。
          </div>
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
      </template>
    </el-form>
    
    <!-- 在处理完成后显示原始事件信息 -->
    <div v-if="processedData && processedData.segment_info && processedData.segment_info.type === 'event_related'" class="event-info-box">
      <div class="info-title"><strong>事件分段信息</strong></div>
      <p>事件类型: {{ processedData.segment_info.event_id }}</p>
      <p>分析的事件数量: {{ processedData.segment_info.event_count }}</p>
      <p>相对时间范围: -{{ processedData.segment_info.time_before }}s 到 {{ processedData.segment_info.time_after }}s</p>
      
      <div v-if="processedData.segment_info.original_events && processedData.segment_info.original_events.length">
        <p>原始事件时间点:</p>
        <ul class="event-list">
          <li v-for="(time, index) in processedData.segment_info.original_events.slice(0, 5)" :key="index">
            {{ time.toFixed(2) }}秒
          </li>
          <li v-if="processedData.segment_info.original_events.length > 5">
            ...等共{{ processedData.segment_info.original_events.length }}个事件
          </li>
        </ul>
      </div>
      
      <div v-if="processedData.segment_info.original_time_window">
        <p>原始时间窗口: {{ processedData.segment_info.original_time_window[0] }}s - {{ processedData.segment_info.original_time_window[1] }}s</p>
      </div>
    </div>
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

.form-help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.info-text {
  font-size: 12px;
  color: #606266;
  background-color: #f4f6f8;
  padding: 8px;
  border-radius: 4px;
  margin: 5px 0 10px;
  line-height: 1.4;
}

.info-box {
  margin: 0 0 15px;
  padding: 8px 12px;
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
}

.info-title {
  font-weight: bold;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #1890ff;
}

.warning-text {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}

.warning-box {
  margin: 0 0 15px;
  padding: 8px 12px;
  background-color: #fff3f0;
  border: 1px solid #ffd6b5;
  border-radius: 4px;
}

.warning-title {
  font-weight: bold;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #ffa53e;
}

.warning-content {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
}

.event-info-box {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
}

.event-list {
  margin: 5px 0;
  padding-left: 20px;
}

.event-timeline {
  display: flex;
  align-items: center;
  margin: 10px 0;
  height: 30px;
}

.timeline-line {
  flex: 1;
  height: 2px;
  background: #dcdfe6;
  position: relative;
}

.timeline-event {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  background: #409eff;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.timeline-marker {
  font-size: 12px;
  color: #606266;
  padding: 0 5px;
}

.info-event {
  background-color: #f0f9ff;
  border-color: #a5d8ff;
}

.event-count {
  margin-top: 5px;
  font-weight: bold;
  color: #409eff;
}
</style>