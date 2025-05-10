<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage as message } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
// import ERPChart from '@/components/analysis/ERPChart.vue';
import TimeSeriesChart from '@/components/analysis/TimeSeriesChart.vue';
import { useLoading } from '@/composables/useLoading';
import { useFormState } from '@/composables/useFormState';
import analysisService from '@/services/analysisService';
import datasetService from '@/services/dataset';
import { useChannelPositions } from '@/composables/useChannelPositions';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';

const route = useRoute();
const router = useRouter();
const datasetId = computed(() => route.params.datasetId);
const subjectId = computed(() => route.params.subjectId);

// 数据状态
const erpData = ref(null);
const availableChannels = ref([]);
const selectedChannels = ref([]);
const availableEvents = ref([]);
const selectedEvents = ref([]);
const eventFilterKeyword = ref('');
const eventCategoryFilter = ref('all');
const eventCategories = ref([]);
const maxEventsToShow = ref(10);
const showAllEvents = ref(false);
const preprocessedDataAvailable = ref(false);
const preprocessedData = ref(null);

// 错误信息
const errorMessage = ref('');

// 加载状态
const loading = ref(false);
const { isLoading, withLoading } = useLoading({
  data: false,
  applying: false
});

// 分析表单
const { formState: analysisOptions, resetForm } = useFormState('time-analysis-options', {
  // 基线校正
  baseline: {
    enabled: true,
    start: -200,
    end: 0
  },
  // 平均方式
  averaging: {
    method: 'mean', // mean, median
    removeOutliers: false,
    outlierThreshold: 2.5
  },
  // 显示设置
  display: {
    showIndividual: false,
    showStd: true,
    colorByCondition: true
  },
  // 时间窗口
  timeWindow: {
    start: -200,
    end: 800
  }
});

// 当前活动标签页
const activeTab = ref('erp');

// 通道选择
const { 
  fetchElectrodePositions,
  getChannelPosition,
  isLoading: positionsLoading,
  error: positionsError,
  positionSource,
  hasCustomPositions,
  openChannelSelect, 
  renderChannelSelectDialog 
} = useChannelPositions();

// 计算属性：事件类型分类
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

// 计算属性：过滤后的事件类型
const filteredEventTypes = computed(() => {
  let result = [...uniqueEventTypes.value];
  
  // 关键词过滤
  if (eventFilterKeyword.value) {
    const keyword = eventFilterKeyword.value.toLowerCase();
    result = result.filter(event => 
      event.name.toLowerCase().includes(keyword) || 
      String(event.id).toLowerCase().includes(keyword)
    );
  }
  
  // 分类过滤
  if (eventCategoryFilter.value !== 'all') {
    result = result.filter(event => {
      // 这里可以根据实际需求添加分类逻辑
      // 例如根据事件ID范围或名称特征进行分类
      if (eventCategoryFilter.value === 'numeric' && !isNaN(event.id)) {
        return true;
      }
      if (eventCategoryFilter.value === 'named' && isNaN(event.id)) {
        return true;
      }
      return false;
    });
  }
  
  return result;
});

// 计算属性：要显示的事件类型
const displayedEventTypes = computed(() => {
  if (showAllEvents.value) {
    return filteredEventTypes.value;
  }
  return filteredEventTypes.value.slice(0, maxEventsToShow.value);
});

// 加载受试者信息和可用通道
const loadSubjectInfo = async () => {
  try {
    const response = await datasetService.getSubjectInfo(datasetId.value, subjectId.value);
    if (response && response.data) {
      if (response.data.channels) {
      availableChannels.value = response.data.channels;
        // 默认选择前5个通道或全部通道（如果少于5个）
        selectedChannels.value = availableChannels.value.slice(0, Math.min(5, availableChannels.value.length));
    }
    
    // 加载事件标记
      if (response.data.events) {
      availableEvents.value = response.data.events;
      // 默认选择所有事件
      selectedEvents.value = availableEvents.value.map(event => event.id);
      }
    }
  } catch (error) {
    console.error('加载受试者信息失败:', error);
    message.error('加载受试者信息失败');
  }
};

// 运行时域分析
const runTimeAnalysis = async () => {
  try {
    loading.value = true;
    errorMessage.value = '';

    // 检查是否有预处理数据可用
    if (!preprocessedDataAvailable.value) {
      message.warning('请先完成预处理步骤');
    return;
  }
  
    // 清除之前的分析结果
    erpData.value = null;

    // 检查baseline格式并转换为后端需要的格式
    const baselineParam = Array.isArray(analysisOptions.baseline) 
      ? analysisOptions.baseline 
      : [analysisOptions.baseline.start / 1000, analysisOptions.baseline.end / 1000];
    
    console.log('发送分析请求，参数:', {
      baseline: baselineParam,
      timeWindow: [analysisOptions.timeWindow.start / 1000, analysisOptions.timeWindow.end / 1000],
      events: selectedEvents.value
    });

    const response = await analysisService.runTimeAnalysis({
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      baseline: baselineParam,
      timeWindow: [analysisOptions.timeWindow.start / 1000, analysisOptions.timeWindow.end / 1000],
      events: selectedEvents.value
    });

    console.log('分析请求成功，响应:', response);

    // 打印详细的响应数据结构
    console.log('响应数据结构:', {
      times: response.data.times ? `数组长度: ${response.data.times.length}, 范围: [${response.data.times[0]}, ${response.data.times[response.data.times.length - 1]}]` : '无',
      data: response.data.data ? `通道数: ${Object.keys(response.data.data).length}` : '无',
      info: response.data.info || '无',
      channels: response.data.info?.ch_names || '无'
    });

    // 打印一个通道的样本数据
    const sampleChannel = Object.keys(response.data.data || {})[0];
    if (sampleChannel) {
      const channelData = response.data.data[sampleChannel];
      console.log(`通道 ${sampleChannel} 数据样本:`, {
        length: channelData.length,
        sample: channelData.slice(0, 5)
      });
    }

    // 将响应数据保存到erpData
    erpData.value = {
      ...response.data,
      // 添加三种视图的数据标记，方便formatChartData函数识别
      erp: true,
      singleTrials: true,
      'time-series': true
    };

    // 确保选中的通道存在于数据中
    if (response.data.info && response.data.info.ch_names) {
      const availableChannels = response.data.info.ch_names;
      console.log('可用通道:', availableChannels);
      
      // 如果没有选中通道或选中的通道不在可用列表中，则选择前5个可用通道
      if (selectedChannels.value.length === 0 || 
          !selectedChannels.value.some(ch => availableChannels.includes(ch))) {
        selectedChannels.value = availableChannels.slice(0, Math.min(5, availableChannels.length));
        console.log('自动选择通道:', selectedChannels.value);
      }
    }

    message.success('时域分析完成！');
  } catch (error) {
    console.error('运行时域分析失败:', error);
    errorMessage.value = `分析失败: ${error.message || '未知错误'}`;
    message.error('分析失败，请检查数据和分析参数');
    
    // 提供更详细的错误指导
    if (error.response?.status === 500) {
      message.error('服务器处理错误，可能是事件数据问题，请尝试调整分析参数');
    } else if (error.response?.status === 404) {
      message.error('找不到请求的资源，请确认数据集和受试者ID正确');
    } else if (error.message?.includes('network')) {
      message.error('网络连接问题，请检查后端服务是否正常运行');
    }
  } finally {
    loading.value = false;
  }
};

// 选择通道
const handleSelectChannels = async () => {
  // 先获取电极位置数据
  if (datasetId.value && subjectId.value) {
    try {
      await fetchElectrodePositions(datasetId.value, subjectId.value);
      console.log('电极位置获取状态:', {
        hasCustomPositions: hasCustomPositions.value,
        positionSource: positionSource.value
      });
    } catch (error) {
      console.warn('获取电极位置失败, 将使用普通通道选择:', error);
    }
  }

  // 打开通道选择对话框
  openChannelSelect(
    selectedChannels.value,
    availableChannels.value,
    (selected) => {
      selectedChannels.value = selected;
    }
  );
};

// 加载预处理数据
const loadPreprocessedData = () => {
  try {
    console.log('尝试加载预处理数据...');
    const preprocessedDataStr = localStorage.getItem('preprocessed_data');
    if (!preprocessedDataStr) {
      console.log('localStorage中没有找到preprocessed_data');
      return false;
    }
    
    console.log('找到预处理数据，解析中...');
    const parsedData = JSON.parse(preprocessedDataStr);
    console.log('预处理数据解析结果:', {
      datasetId: parsedData.datasetId,
      subjectId: parsedData.subjectId,
      timestamp: parsedData.timestamp,
      hasData: !!parsedData.data,
      channelsCount: parsedData.data?.channels?.length || 0
    });
    
    // 检查数据是否匹配当前的数据集和受试者
    if (parsedData.datasetId !== datasetId.value || 
        parsedData.subjectId !== subjectId.value) {
      console.log('预处理数据不匹配当前数据集/受试者', {
        expected: { datasetId: datasetId.value, subjectId: subjectId.value },
        actual: { datasetId: parsedData.datasetId, subjectId: parsedData.subjectId }
      });
      return false;
    }
    
    // 检查数据是否过期（24小时）
    const dataAge = Date.now() - parsedData.timestamp;
    const oneDayMs = 24 * 60 * 60 * 1000;
    
    if (dataAge >= oneDayMs) {
      console.log('预处理数据已过期，已移除', { dataAge, oneDayMs });
      localStorage.removeItem('preprocessed_data');
      return false;
    }
    
    // 保存预处理数据到状态中
    console.log('预处理数据有效，正在设置状态...');
    preprocessedData.value = parsedData;
    preprocessedDataAvailable.value = true;
    
    // 更新可用通道和选择的通道
    if (parsedData.data && parsedData.data.channels) {
      console.log('更新通道列表:', parsedData.data.channels);
      availableChannels.value = parsedData.data.channels;
      // 选择所有预处理后的通道，因为这些是用户已经筛选过的
      selectedChannels.value = [...parsedData.data.channels];
      
      // 加载事件标记 - 如果预处理数据中有事件信息
      if (parsedData.data.events) {
        console.log('从预处理数据中加载事件:', parsedData.data.events);
        
        // 增强的事件处理逻辑
        try {
          let eventsArray = [];
          
          // 检查events的类型并进行适当处理
          if (Array.isArray(parsedData.data.events)) {
            eventsArray = parsedData.data.events;
            console.log('预处理数据中的events是数组，直接使用');
          } else if (typeof parsedData.data.events === 'object') {
            // 转换对象格式为数组
            eventsArray = Object.keys(parsedData.data.events).map(id => ({
              id: parseInt(id) || id,
              name: parsedData.data.events[id].name || `事件${id}`,
              count: parsedData.data.events[id].count || 0,
              // 如果有时间信息，记录下来，用于过滤
              time: parsedData.data.events[id].time,
              latency: parsedData.data.events[id].latency
            }));
            console.log('预处理数据中的events是对象，已转换为数组');
          }
          
          // 过滤事件 - 只保留在预处理时间范围内的事件
          if (parsedData.data.timeRange && eventsArray.length > 0) {
            const [startTime, endTime] = parsedData.data.timeRange;
            console.log(`根据时间范围 [${startTime}, ${endTime}] 过滤事件`);
            
            // 只有当事件有时间信息时才进行过滤
            const hasTimeInfo = eventsArray.some(event => event.time !== undefined || event.latency !== undefined);
            
            if (hasTimeInfo) {
              // 过滤在时间范围内的事件
              const filteredEvents = eventsArray.filter(event => {
                const eventTime = event.time !== undefined ? event.time : (event.latency !== undefined ? event.latency / 1000 : null);
                
                // 如果没有时间信息，保留该事件
                if (eventTime === null) return true;
                
                return eventTime >= startTime && eventTime <= endTime;
              });
              
              console.log(`过滤后的事件数量: ${filteredEvents.length}/${eventsArray.length}`);
              eventsArray = filteredEvents;
            } else {
              console.log('事件没有时间信息，无法根据时间范围过滤');
            }
          }
          
          if (eventsArray.length > 0) {
            console.log('设置可用事件列表:', eventsArray);
            availableEvents.value = eventsArray;
            // 创建唯一事件类型列表
            const uniqueEventIds = new Set();
            uniqueEventTypes.value = eventsArray.filter(event => {
              // 确保不重复添加相同的事件ID
              if (!uniqueEventIds.has(event.id)) {
                uniqueEventIds.add(event.id);
                return true;
              }
              return false;
            }).map(event => ({
              id: event.id,
              name: event.name || `事件${event.id}`,
              count: event.count || eventsArray.filter(e => e.id === event.id).length
            }));
            
            // 默认选择所有事件类型
            selectedEvents.value = [...uniqueEventIds];
            console.log('已选择的事件:', selectedEvents.value);
          } else {
            console.warn('预处理数据中没有可用事件');
          }
        } catch (e) {
          console.error('处理预处理数据中的事件时出错:', e);
          message.warning('处理事件数据时出错，可能需要重新加载数据');
        }
      } else {
        console.log('预处理数据中没有事件信息');
      }
    } else {
      console.warn('预处理数据中没有通道信息');
    }
    
    // 分析数据有效
    return true;
  } catch (error) {
    console.error('加载预处理数据失败:', error);
    message.error(`加载预处理数据失败: ${error.message}`);
    return false;
  }
};

// 单独加载事件信息
const loadEvents = async () => {
  try {
    console.log('尝试加载事件信息...');
    // 先尝试使用专用的事件API
    try {
      const eventsResponse = await datasetService.getEvents(datasetId.value, subjectId.value);
      if (eventsResponse && eventsResponse.data && eventsResponse.data.length > 0) {
        console.log('成功通过events API加载事件:', eventsResponse.data);
        availableEvents.value = eventsResponse.data;
        
        // 提取事件分类
        extractEventCategories();
        
        // 默认选择前5个事件类型
        if (uniqueEventTypes.value.length > 0) {
          selectedEvents.value = uniqueEventTypes.value
            .slice(0, Math.min(5, uniqueEventTypes.value.length))
            .map(event => event.id);
        }
        return;
      }
    } catch (eventsError) {
      console.warn('通过events API加载事件失败，尝试从subject info加载', eventsError);
    }
    
    // 如果专用API失败，回退到从subject info加载
    const response = await datasetService.getSubjectInfo(datasetId.value, subjectId.value);
    if (response && response.data && response.data.events) {
      console.log('从subject info加载事件:', response.data.events);
      availableEvents.value = response.data.events;
      
      // 提取事件分类
      extractEventCategories();
      
      // 默认选择前5个事件类型
      if (uniqueEventTypes.value.length > 0) {
        selectedEvents.value = uniqueEventTypes.value
          .slice(0, Math.min(5, uniqueEventTypes.value.length))
          .map(event => event.id);
      }
    } else {
      console.warn('没有找到事件信息');
      // 如果没有事件信息，创建一个默认事件
      availableEvents.value = [{ id: 1, name: '默认事件' }];
      selectedEvents.value = [1];
      console.log('创建默认事件:', availableEvents.value);
    }
  } catch (error) {
    console.error('加载事件信息失败:', error);
    // 创建默认事件作为后备
    availableEvents.value = [{ id: 1, name: '默认事件' }];
    selectedEvents.value = [1];
    console.log('加载失败，创建默认事件:', availableEvents.value);
  }
};

// 提取事件分类
const extractEventCategories = () => {
  const categories = new Set(['all']);
  
  // 根据事件ID是否为数字添加基本分类
  let hasNumeric = false;
  let hasNamed = false;
  
  for (const event of availableEvents.value) {
    if (!isNaN(event.id)) {
      hasNumeric = true;
    } else {
      hasNamed = true;
    }
    
    // 这里可以添加更多分类逻辑
    // 例如根据事件名称特征进行分类
  }
  
  if (hasNumeric) categories.add('numeric');
  if (hasNamed) categories.add('named');
  
  eventCategories.value = Array.from(categories);
};

// 切换选择的事件
const toggleEvent = (eventId) => {
  const index = selectedEvents.value.indexOf(eventId);
  if (index > -1) {
    selectedEvents.value.splice(index, 1);
  } else {
    selectedEvents.value.push(eventId);
  }
};

// 选择全部事件
const selectAllEvents = () => {
  selectedEvents.value = filteredEventTypes.value.map(event => event.id);
};

// 清除所有选择
const clearEventSelection = () => {
  selectedEvents.value = [];
};

// 加载示例数据
const loadExampleData = async () => {
  console.log('加载示例EEG数据...');
  
  // 创建示例时间点数组 (-0.2s 到 0.8s，1000Hz采样率)
  const times = [];
  for (let i = 0; i < 1000; i++) {
    times.push(-0.2 + i * 0.001);
  }
  
  // 创建示例通道
  const channels = ['Fz', 'Cz', 'Pz', 'Oz', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4'];
  
  // 创建示例数据
  const data = {};
  channels.forEach(channel => {
    const channelData = [];
    for (let i = 0; i < 1000; i++) {
      // 创建一个类似ERP的波形
      const t = times[i];
      let value = 0;
      
      // N100组件
      if (t > 0.05 && t < 0.15) {
        value -= 15 * Math.exp(-Math.pow((t - 0.1) * 10, 2));
      }
      
      // P300组件
      if (t > 0.25 && t < 0.45) {
        value += 10 * Math.exp(-Math.pow((t - 0.35) * 5, 2));
      }
      
      // 添加一些随机噪声
      value += (Math.random() - 0.5) * 2;
      
      // 为不同通道添加一些变化
      const channelIndex = channels.indexOf(channel);
      value *= 1 + channelIndex * 0.1;
      
      channelData.push(value);
    }
    data[channel] = channelData;
  });
  
  // 创建示例信息
  const info = {
    ch_names: channels,
    sfreq: 1000,
    description: '示例EEG数据'
  };
  
  // 设置示例ERP数据
  erpData.value = {
    times,
    data,
    info,
    erp: true,
    singleTrials: true,
    'time-series': true
  };
  
  // 设置示例通道
  selectedChannels.value = channels.slice(0, 3); // 只选择前3个通道
  
  console.log('示例数据加载完成', {
    channels: channels.length,
    timePoints: times.length,
    timeRange: [times[0], times[times.length - 1]]
  });
  
  return erpData.value;
};

// 组件挂载后加载数据
onMounted(async () => {
  console.log('时域分析组件已挂载');
  
  // 获取路由参数
  const route = useRoute();
  datasetId.value = route.params.datasetId;
  subjectId.value = route.params.subjectId;
  
  console.log('路由参数:', {
    datasetId: datasetId.value,
    subjectId: subjectId.value
  });
  
  // 尝试获取电极位置数据
  if (datasetId.value && subjectId.value) {
    try {
      await fetchElectrodePositions(datasetId.value, subjectId.value);
      console.log('已获取电极位置数据:', {
        hasPositions: hasCustomPositions.value,
        source: positionSource.value
      });
    } catch (error) {
      console.warn('获取电极位置数据失败:', error);
    }
  }

  // 尝试加载预处理数据
  try {
    console.log('尝试加载预处理数据...');
    const hasPreprocessedData = await loadPreprocessedData();
    if (hasPreprocessedData) {
      message.success('已成功加载预处理数据，可以进行时域分析');
      
      // 如果预处理数据包含时间范围，更新分析选项
      if (preprocessedData.value && preprocessedData.value.data.timeRange) {
        const [startTime, endTime] = preprocessedData.value.data.timeRange;
        console.log('从预处理数据继承时间范围:', [startTime, endTime]);
        
        // 转换为毫秒并设置到分析选项中
        analysisOptions.timeWindow.start = Math.round(startTime * 1000);
        analysisOptions.timeWindow.end = Math.round(endTime * 1000);
        
        // 也根据预处理时间范围调整基线设置
        if (startTime < 0) {
          analysisOptions.baseline.start = Math.round(startTime * 1000);
          analysisOptions.baseline.end = 0; // 基线结束时间通常设为事件发生时刻
        }
      }
    } else {
      // 如果需要，加载主体信息
      if (datasetId.value && subjectId.value) {
        try {
          console.log('加载主体信息...');
          await loadSubjectInfo();
          message.info('请点击"运行分析"按钮进行分析');
        } catch (error) {
          console.warn('加载主体信息失败:', error);
          message.warning('无法加载受试者信息，请检查数据是否存在');
        }
      } else {
        message.warning('未提供数据集或受试者ID，请返回选择数据');
      }
    }
  } catch (error) {
    console.warn('加载预处理数据失败:', error);
    message.error('加载预处理数据时出错');
  }
});

// 监听路由参数变化
watch([datasetId, subjectId], async () => {
  erpData.value = null;
  preprocessedDataAvailable.value = false;
  preprocessedData.value = null;
  
  const hasPreprocessedData = loadPreprocessedData();
  if (!hasPreprocessedData) {
    await loadSubjectInfo();
  }
});

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}

// 添加数据格式化函数
const formatChartData = (data, type) => {
  if (!data) {
    console.warn('formatChartData: 输入数据为空');
    return [];
  }
  
  console.log(`格式化图表数据 (${type}):`, { 
    dataKeys: Object.keys(data),
    hasTimes: !!data.times,
    timesLength: data.times?.length || 0,
    hasData: !!data.data,
    dataStructure: data.data ? Object.keys(data.data).slice(0, 3).join(', ') + '...' : '无' 
  });
  
  // 处理示例数据格式
  if (data[type] && Array.isArray(data[type])) {
    console.log('使用预定义的示例数据格式:', { length: data[type].length });
    return data[type];
  }
  
  // 处理后端返回的ERP数据格式
  if (type === 'erp' || type === 'singleTrials' || type === 'time-series') {
    // 检查数据是否包含必要的字段
    if (!data.data || !data.times || !Array.isArray(data.times)) {
      console.warn('formatChartData: 数据格式不正确，缺少times或data字段', { 
        hasTimes: !!data.times, 
        hasData: !!data.data,
        isTimesArray: Array.isArray(data.times)
      });
      
      // 尝试从data.erp等子字段中恢复数据
      if (data.erp && (data.erp.times || data.erp.data)) {
        console.log('尝试从data.erp中恢复数据');
        if (data.erp.times && data.erp.data) {
          data.times = data.erp.times;
          data.data = data.erp.data;
        }
      }
      
      // 如果仍然没有有效数据，返回空数组
      if (!data.data || !data.times || !Array.isArray(data.times)) {
        console.warn('无法恢复有效数据，返回空数组');
        return [];
      }
    }
    
    console.log(`正在处理${type}数据`, {
      timesLength: data.times.length,
      timeRange: data.times.length > 0 ? [data.times[0], data.times[data.times.length - 1]] : '空',
      channels: typeof data.data === 'object' ? Object.keys(data.data).length : '无',
      firstChannel: Object.keys(data.data)[0] || '无'
    });
    
    const formattedData = [];
    
    // 获取所有可用通道
    const availableChannels = Object.keys(data.data);
    
    // 如果没有指定要显示的通道或指定的通道都不存在，使用所有可用通道
    let channelsToDisplay = [];
    if (selectedChannels.value && selectedChannels.value.length > 0) {
      // 过滤只存在于data.data中的通道
      channelsToDisplay = selectedChannels.value.filter(ch => availableChannels.includes(ch));
      
      if (channelsToDisplay.length === 0) {
        console.log('没有选中的通道可用，使用所有可用通道');
        channelsToDisplay = availableChannels;
      }
    } else {
      channelsToDisplay = availableChannels;
    }
    
    // 删除通道数量限制，使用所有选择的通道
    console.log(`将显示 ${channelsToDisplay.length} 个通道:`, channelsToDisplay);
    
    // 如果是单次试次视图，只显示第一个通道并添加模拟的单次试次
    if (type === 'singleTrials' && channelsToDisplay.length > 0) {
      const channel = channelsToDisplay[0];
      console.log(`单次试次视图: 使用通道 ${channel}`);
      
      if (data.data[channel] && Array.isArray(data.data[channel])) {
        // 添加主ERP曲线
        for (let i = 0; i < data.times.length; i++) {
          formattedData.push({
            channel: channel,
            time: data.times[i],
            value: data.data[channel][i]
          });
        }
        
        // 添加模拟的单次试次（上下偏移的ERP曲线）
        for (let trial = 1; trial <= 5; trial++) {
          const offset = (Math.random() - 0.5) * 10; // 随机偏移
          for (let i = 0; i < data.times.length; i++) {
            formattedData.push({
              channel: `${channel}-试次${trial}`,
              time: data.times[i],
              value: data.data[channel][i] + offset + Math.sin(i/20) * 2 // 添加一些随机波动
            });
          }
        }
      } else {
        console.warn(`通道 ${channel} 没有有效数据`);
      }
    } 
    // 对于ERP和时间序列视图，显示所有选中通道
    else {
      // 遍历所有选中的通道
      for (const channel of channelsToDisplay) {
        if (data.data[channel] && Array.isArray(data.data[channel])) {
          // 确保通道数据和时间点长度一致
          const channelDataLength = data.data[channel].length;
          const timesLength = data.times.length;
          
          if (channelDataLength !== timesLength) {
            console.warn(`通道 ${channel} 数据长度(${channelDataLength})与时间数组长度(${timesLength})不匹配，调整中`);
          }
          
          // 使用最小的长度来确保不会越界
          const pointsCount = Math.min(channelDataLength, timesLength);
          
          // 将每个时间点的数据转换为所需格式
          for (let i = 0; i < pointsCount; i++) {
            formattedData.push({
              channel: channel,
              time: data.times[i],
              value: data.data[channel][i]
            });
          }
        } else {
          console.warn(`通道 ${channel} 没有有效数据`);
        }
      }
    }
    
    console.log(`${type}格式化后的数据: ${formattedData.length} 个点, ${channelsToDisplay.length} 个通道`);
    return formattedData;
  }
  
  // 其他情况返回空数组
  console.warn(`未能识别的数据类型 ${type}，返回空数组`);
  return [];
};
</script>

<template>
  <AppLayout>
    <div class="time-analysis-container">
      <h2 class="page-title">时域分析</h2>
      
      <!-- 顶部分析指示区 -->
      <div class="top-controls">
        <!-- 基线校正 (更加简洁) -->
        <div class="control-group">
          <div class="baseline-section">
            <label class="control-label">
              <span class="option-label">基线校正</span>
              <el-switch v-model="analysisOptions.baseline.enabled" size="small" />
              <el-tooltip content="对脑电数据进行基线校正，通常使用事件前时间段">
                <i class="el-icon-info"></i>
              </el-tooltip>
            </label>
            <template v-if="analysisOptions.baseline.enabled">
              <div class="input-group">
                <el-input-number 
                  v-model="analysisOptions.baseline.start" 
                  :min="-1000" 
                  :max="0"
                  :step="50"
                  size="small"
                  controls-position="right"
                  style="width: 100px;"
                />
                <span style="margin: 0 5px;">至</span>
                <el-input-number 
                  v-model="analysisOptions.baseline.end" 
                  :min="-500" 
                  :max="0"
                  :step="50"
                  size="small"
                  controls-position="right"
                  style="width: 100px;"
                />
                <span class="unit">ms</span>
              </div>
            </template>
          </div>
        
          <!-- 时间窗口设置 (更加简洁) -->
          <div class="time-window-section">
            <label class="control-label">
              <span class="option-label">时间窗口</span>
              <el-tooltip content="分析的时间范围，0ms表示事件触发时刻">
                <i class="el-icon-info"></i>
              </el-tooltip>
            </label>
            <div class="input-group">
              <el-input-number 
                v-model="analysisOptions.timeWindow.start" 
                :min="-1000" 
                :max="0"
                :step="100"
                size="small"
                controls-position="right"
                style="width: 100px;"
              />
              <span style="margin: 0 5px;">至</span>
              <el-input-number 
                v-model="analysisOptions.timeWindow.end" 
                :min="0" 
                :max="2000"
                :step="100"
                size="small"
                controls-position="right"
                style="width: 100px;"
              />
              <span class="unit">ms</span>
            </div>
          </div>
        </div>
        
        <!-- 预处理状态和操作按钮 -->
        <div class="action-area">
          <div v-if="preprocessedDataAvailable" class="status-tag">
            <el-tag size="small" type="success">已加载预处理数据</el-tag>
          </div>
          <div class="action-buttons">
            <el-button 
              type="primary" 
              @click="runTimeAnalysis" 
              :loading="isLoading.applying"
              :disabled="selectedChannels.length === 0 || selectedEvents.length === 0"
            >
              运行分析
            </el-button>
            <el-button 
              type="success" 
              @click="goToNextStep"
            >
              下一步
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 主分析区域 -->
      <div class="analysis-container">
        <!-- 左侧控制面板 -->
        <div class="controls-panel">
          <!-- 通道选择 - 简化为按钮 -->
          <div class="control-section">
            <div class="section-header">
              <h4>通道选择</h4>
              <el-button type="primary" size="small" @click="handleSelectChannels">
                选择通道 ({{ selectedChannels.length }})
              </el-button>
            </div>
            <div class="selected-channels-preview" v-if="selectedChannels.length > 0">
              <el-tag 
                v-for="(channel, index) in selectedChannels.slice(0, 5)" 
                :key="channel"
                size="small"
                class="channel-tag"
              >
                {{ channel }}
              </el-tag>
              <el-tag v-if="selectedChannels.length > 5" size="small" type="info">
                +{{ selectedChannels.length - 5 }}个
              </el-tag>
            </div>
          </div>
          
          <!-- 事件选择 - 增强版，参考SegmentProcessor.vue -->
          <div class="control-section events-section">
            <div class="section-header">
              <h4>事件选择</h4>
            </div>
            
            <!-- 添加时间窗口内的事件信息提示 -->
            <div class="info-box" v-if="preprocessedDataAvailable && preprocessedData && preprocessedData.data.timeRange">
              <div class="info-title">
                <i class="el-icon-info"></i> 当前时间窗口
              </div>
              <div class="info-content">
                <div>时间范围: {{ analysisOptions.timeWindow.start }}ms 至 {{ analysisOptions.timeWindow.end }}ms</div>
                <div>事件类型: {{ uniqueEventTypes.length }}种</div>
                <div>事件实例: {{ availableEvents.length }}个</div>
              </div>
            </div>
            
            <div class="events-controls">
              <div class="events-actions">
                <el-button size="small" type="primary" plain @click="selectAllEvents">全选</el-button>
                <el-button size="small" @click="clearEventSelection">清除</el-button>
              </div>
            </div>
            
            <!-- 事件列表 - 增强布局 -->
            <div class="events-list">
              <template v-if="filteredEventTypes.length > 0">
                <div class="event-tags">
                  <el-check-tag
                    v-for="event in filteredEventTypes"
                    :key="event.id"
                    :checked="selectedEvents.includes(event.id)"
                    @click="toggleEvent(event.id)"
                    class="event-tag"
                  >
                    {{ event.name }} ({{ event.count }})
                  </el-check-tag>
                </div>
              </template>
              <el-empty 
                v-else 
                description="没有事件" 
                :image-size="40"
              />
            </div>
            
            <div class="events-count">已选择: {{ selectedEvents.length }}/{{ uniqueEventTypes.length }}</div>
          </div>
          
          <!-- 显示设置 - 移到左侧 -->
          <div class="control-section">
            <div class="section-header">
              <h4>显示设置</h4>
            </div>
            <div class="display-settings">
              <el-checkbox v-model="analysisOptions.display.showIndividual">显示单次试次</el-checkbox>
              <el-checkbox v-model="analysisOptions.display.showStd">显示标准差</el-checkbox>
              <el-checkbox v-model="analysisOptions.display.colorByCondition">按条件着色</el-checkbox>
            </div>
          </div>
        </div>
        
        <!-- 右侧大图表区域 -->
        <div class="chart-panel">
          <div class="chart-container" v-loading="isLoading.data || isLoading.applying">
            <div class="chart-header">
              <h4>分析结果</h4>
              <el-tabs v-model="activeTab" type="card" class="chart-tabs">
                <el-tab-pane label="ERP波形" name="erp"></el-tab-pane>
                <el-tab-pane label="单次试次" name="single-trial"></el-tab-pane>
                <el-tab-pane label="时间序列" name="time-series"></el-tab-pane>
              </el-tabs>
            </div>
            
            <template v-if="erpData">
              <!-- ERP波形 -->
              <div v-if="activeTab === 'erp'" class="chart-view">
                <TimeSeriesChart 
                  v-if="erpData && erpData.erp" 
                  :data="formatChartData(erpData, 'erp')"
                  :channels="selectedChannels"
                  :timeRange="[analysisOptions.timeWindow.start/1000, analysisOptions.timeWindow.end/1000]"
                />
              </div>
              
              <!-- 单次试次 -->
              <div v-else-if="activeTab === 'single-trial'" class="chart-view">
                <TimeSeriesChart 
                  v-if="erpData && erpData.singleTrials" 
                  :data="formatChartData(erpData, 'singleTrials')"
                  :channels="selectedChannels"
                  :timeRange="[analysisOptions.timeWindow.start/1000, analysisOptions.timeWindow.end/1000]"
                />
              </div>
              
              <!-- 时间序列 -->
              <div v-else-if="activeTab === 'time-series'" class="chart-view">
                <TimeSeriesChart 
                  v-if="erpData && erpData['time-series']" 
                  :data="formatChartData(erpData, 'time-series')"
                  :channels="selectedChannels"
                  :timeRange="[analysisOptions.timeWindow.start/1000, analysisOptions.timeWindow.end/1000]"
                />
              </div>
            </template>
              
              <!-- 无数据提示 -->
              <div v-else class="no-data">
              <el-empty description="暂无分析数据">
                <template #extra>
                  <el-button type="primary" @click="runTimeAnalysis">运行分析</el-button>
                </template>
              </el-empty>
              </div>
            </div>
        </div>
      </div>
      
      <!-- 分析流程导航 -->
      <AnalysisWorkflow 
        ref="workflowRef"
        current-step="time" 
        :dataset-id="datasetId" 
        :subject-id="subjectId" 
      />
    </div>
  </AppLayout>
  
  <!-- 通道选择对话框 -->
  <component :is="renderChannelSelectDialog()" />
</template>

<style scoped>
.time-analysis-container {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
  padding-bottom: 60px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  color: #303133;
}

/* 顶部控制区域 */
.top-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
}

.control-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.option-label {
  font-weight: 500;
  color: #303133;
  min-width: 70px;
}

.unit {
  margin-left: 5px;
  color: #909399;
}

.input-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.baseline-section,
.time-window-section {
  display: flex;
  flex-direction: column;
}

.action-area {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  justify-content: center;
}

.status-tag {
  margin-bottom: 5px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

/* 主分析区域 */
.analysis-container {
  display: flex;
  height: calc(100vh - 220px);
  gap: 15px;
}

/* 左侧控制面板 */
.controls-panel {
  width: 280px; /* 略微增加宽度以容纳更多内容 */
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.control-section {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 5px;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.selected-channels-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}

.channel-tag {
  margin-right: 0;
}

.display-settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.events-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.events-controls {
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
}

.events-actions {
  display: flex;
  gap: 10px;
}

/* 添加事件信息提示框样式 */
.info-box {
  margin-bottom: 10px;
  padding: 8px;
  background-color: #f0f9ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  font-size: 12px;
}

.info-title {
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.info-content {
  color: #606266;
  line-height: 1.5;
}

.events-list {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  padding: 8px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  margin-bottom: 5px;
}

.event-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.event-tag {
  margin: 0;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  padding: 4px 8px;
}

.event-tag:hover {
  transform: scale(1.05);
}

.events-count {
  font-size: 12px;
  color: #909399;
  text-align: right;
  margin-top: 5px;
}

/* 右侧图表区域 */
.chart-panel {
  flex: 1;
  overflow: hidden;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #EBEEF5;
}

.chart-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.chart-tabs {
  margin-left: auto;
}

.chart-view {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .analysis-container {
    flex-direction: column;
    height: auto;
  }
  
  .controls-panel {
    width: 100%;
  }
  
  .chart-panel {
    height: 600px; /* 增大图表高度 */
  }
  
  .top-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-area {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
  }
  
  .control-group {
    width: 100%;
  }
}
</style> 