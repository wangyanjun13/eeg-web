import { ref, reactive, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import analysisService from '@/services/analysisService';

/**
 * 预处理和分析组合函数
 * @param {String} datasetId 数据集ID
 * @param {String} subjectId 受试者ID
 * @returns {Object} 分析相关的状态和方法
 */
export function useAnalysis(datasetId, subjectId) {
  const router = useRouter();
  
  // 状态变量
  const isLoading = ref(false);
  const currentTaskId = ref(null);
  const taskStatus = ref(null);
  const error = ref(null);
  const originalData = ref(null);
  const processedData = ref(null);
  const availableMethods = ref([]);
  const appliedMethods = ref([]);
  const results = ref({});
  
  // 预处理参数 - 与后端PreprocessParams结构匹配
  const preprocessParams = reactive({
    // 滤波参数
    filter: {
      highpass_filter: true,
      highpass: 1.0,
      lowpass_filter: true,
      lowpass: 40.0,
      notch_filter: true,
      line_freqs: [50.0, 60.0]
    },
    // 重采样参数
    resample: {
      resample: false,
      resample_freq: 250.0
    },
    // 参考设置
    reference: {
      reference: 'average',
      custom_ref_channels: []
    },
    // ICA设置
    ica: {
      run_ica: false,
      ica_method: 'fastica',
      n_components: 15,
      auto_detect_artifacts: true
    },
    // 坏通道检测
    bad_channels: {
      detect_bad_channels: false,
      bad_channel_method: 'correlation'
    },
    // 伪迹去除
    artifacts: {
      remove_artifacts: false,
      artifact_detection_method: 'threshold',
      amplitude_threshold: 100.0,
      reject_by_annotation: true
    },
    // 添加分段参数
    segment: {
      segment_mode: 'time',
      start_time: 0.0,
      end_time: 10.0,
      event_name: null,
      pre_event: 0.2,
      post_event: 0.8,
      apply_baseline: true,
      baseline_start: -0.2,
      baseline_end: 0.0
    },
    // 添加坏段参数
    bad_segments: {
      detect_bad_segments: true,
      detection_method: 'auto',
      amplitude_threshold: 100.0,
      gradient_threshold: 10.0,
      reject_method: 'zero'
    }
  });
  
  /**
   * 检查localStorage是否可用
   */
  const checkStorageSupport = () => {
    try {
      const testKey = `test_${Date.now()}`;
      localStorage.setItem(testKey, 'test');
      localStorage.removeItem(testKey);
      return true;
    } catch (e) {
      console.warn('当前环境不支持 localStorage，将使用内存存储', e);
      return false;
    }
  };
  
  // 修改 saveResults 函数，增加一个标志位
  const storageSupported = checkStorageSupport();
  const saveResults = (step, data) => {
    try {
      // 更新结果状态
      results.value[step] = data;
      
      // 记录应用的方法
      if (!appliedMethods.value.includes(step)) {
        appliedMethods.value.push(step);
      }
      
      // 确保全局对象存在
      if (typeof window !== 'undefined') {
        if (!window.savedResults) window.savedResults = {};
        // 使用深拷贝避免引用问题
        window.savedResults[step] = JSON.parse(JSON.stringify(data));
      }
      
      // 只有在支持的环境中尝试使用 localStorage
      if (storageSupported) {
        try {
          const savedKey = `analysis_${datasetId}_${subjectId}`;
          
          // 进一步优化存储数据结构
          const minimalData = {
            results: Object.fromEntries(
              Object.entries(results.value).map(([k, v]) => [
                k, 
                { 
                  timestamp: new Date().getTime(),
                  applied: true,
                  // 仅存储必要的元数据
                  summary: v ? {
                    channels: Array.isArray(v.channels) ? v.channels.length : 0,
                    sampling_rate: typeof v.sampling_rate === 'number' ? v.sampling_rate : null,
                    from_cache: !!v.from_cache
                  } : null
                }
              ])
            ),
            appliedMethods: appliedMethods.value,
            lastUpdated: new Date().toISOString()
          };
          
          // 尝试压缩数据
          const serializedData = JSON.stringify(minimalData);
          localStorage.setItem(savedKey, serializedData);
        } catch (storageError) {
          console.warn('无法保存到localStorage，但处理将继续', storageError);
        }
      }
      
      return true;
    } catch (e) {
      console.error('保存处理结果失败:', e);
      // 仍然返回true，避免中断主流程
      return true;
    }
  };
  
  /**
   * 从localStorage加载保存的分析结果
   */
  const loadSavedResults = () => {
    try {
      const savedKey = `analysis_${datasetId}_${subjectId}`;
      const savedData = localStorage.getItem(savedKey);
      if (savedData) {
        const parsedData = JSON.parse(savedData);
        if (parsedData.results) {
          results.value = parsedData.results;
        }
        if (parsedData.appliedMethods) {
          appliedMethods.value = parsedData.appliedMethods;
        }
      }
    } catch (e) {
      console.error('加载保存的分析结果失败:', e);
    }
  };
  
  /**
   * 加载预处理模板
   * @param {String} templateName 模板名称
   */
  const loadPreprocessTemplate = async (templateName) => {
    try {
      isLoading.value = true;
      error.value = null;
      
      const response = await analysisService.getPreprocessTemplate(templateName);
      
      if (response && response.data) {
        const template = response.data;
        
        // 更新预处理参数 - 直接替换整个对象以确保结构匹配
        if (template.filter) {
          preprocessParams.filter = { ...template.filter };
        }
        if (template.resample) {
          preprocessParams.resample = { ...template.resample };
        }
        if (template.reference) {
          preprocessParams.reference = { ...template.reference };
        }
        if (template.ica) {
          preprocessParams.ica = { ...template.ica };
        }
        if (template.bad_channels) {
          preprocessParams.bad_channels = { ...template.bad_channels };
        }
        if (template.artifacts) {
          preprocessParams.artifacts = { ...template.artifacts };
        }
        // 添加新参数的支持
        if (template.segment) {
          preprocessParams.segment = { ...template.segment };
        }
        if (template.bad_segments) {
          preprocessParams.bad_segments = { ...template.bad_segments };
        }
        
        ElMessage.success(`成功加载预处理模板`);
      } else {
        throw new Error('获取的模板数据结构不正确');
      }
    } catch (e) {
      error.value = `加载预处理模板失败: ${e.message || e}`;
      ElMessage.error(error.value);
    } finally {
      isLoading.value = false;
    }
  };
  
  /**
   * 获取预处理状态
   * @param {String} taskId 任务ID
   */
  const getPreprocessStatus = async (taskId) => {
    if (!taskId) {
      return { status: 'unknown', progress: 0, message: '未知任务' };
    }
    
    try {
      const status = await analysisService.getPreprocessStatus(taskId);
      taskStatus.value = status;
      return status;
    } catch (e) {
      error.value = `获取预处理状态失败: ${e.message || e}`;
      console.error(error.value);
      return { status: 'error', progress: 0, message: error.value };
    }
  };
  
  /**
   * 运行分析
   * @param {String} type 分析类型
   * @param {Object} params 分析参数
   */
  const runAnalysis = async (type, params = {}) => {
    try {
      isLoading.value = true;
      error.value = null;
      
      let result;
      
      switch (type) {
        case 'preprocess':
          // 使用完整的预处理参数
          const response = await analysisService.preprocessData(datasetId, subjectId, preprocessParams);
          currentTaskId.value = response.task_id;
          result = response;
          break;
          
        case 'filter':
          // 直接使用filter参数
          result = await analysisService.applyFilter(datasetId, subjectId, preprocessParams.filter);
          break;
          
        case 'resample':
          // 重采样
          result = await analysisService.applyResample(datasetId, subjectId, preprocessParams.resample);
          break;
          
        case 'segment':
          // 数据分段
          result = await analysisService.segmentData(datasetId, subjectId, preprocessParams.segment);
          break;
          
        case 'badChannels':
          // 坏通道检测
          result = await analysisService.detectBadChannels(datasetId, subjectId, preprocessParams.bad_channels);
          break;
          
        case 'badSegments':
          // 坏段检测
          result = await analysisService.detectBadSegments(datasetId, subjectId, preprocessParams.bad_segments);
          break;
          
        case 'reference':
          // 重参考
          result = await analysisService.applyReference(datasetId, subjectId, preprocessParams.reference);
          break;
          
        case 'ica':
          // 直接使用ica参数
          result = await analysisService.runICA(datasetId, subjectId, preprocessParams.ica);
          break;
          
        case 'artifacts':
          // 直接使用artifacts参数
          result = await analysisService.removeArtifacts(datasetId, subjectId, preprocessParams.artifacts);
          break;
          
        case 'time':
          result = await analysisService.performTimeAnalysis(datasetId, subjectId, params);
          break;
          
        case 'frequency':
          result = await analysisService.performFrequencyAnalysis(datasetId, subjectId, params);
          break;
          
        case 'spatial':
          result = await analysisService.performSpatialAnalysis(datasetId, subjectId, params);
          break;
          
        case 'advanced':
          result = await analysisService.performAdvancedAnalysis(datasetId, subjectId, params);
          break;
          
        default:
          throw new Error(`未知的分析类型: ${type}`);
      }
      
      // 保存结果
      results.value[type] = result;
      if (!appliedMethods.value.includes(type)) {
        appliedMethods.value.push(type);
      }
      saveResults(type, result);
      
      // 在返回结果前，确保处理后的数据保持相同的时间范围
      if (result && result.data) {
        const timeRange = originalData.value?.timeRange || [0, 10];
        result.data = {
          ...result.data,
          timeRange: timeRange,
          duration: timeRange[1] - timeRange[0]
        };
      }
      
      return result;
    } catch (e) {
      error.value = `运行${type}分析失败: ${e.message || e}`;
      ElMessage.error(error.value);
      throw e;
    } finally {
      isLoading.value = false;
    }
  };
  
  /**
   * 获取原始数据
   */
  const fetchOriginalData = async () => {
    try {
      isLoading.value = true;
      error.value = null;
      
      // 获取保存的时间范围
      let timeRange = [0, 10];
      try {
        const savedTimeRange = localStorage.getItem('selected_time_range');
        if (savedTimeRange) {
          timeRange = JSON.parse(savedTimeRange);
          console.log('useAnalysis: Using saved time range:', timeRange);
        }
      } catch (e) {
        console.error('useAnalysis: Error parsing saved time range:', e);
      }
      
      // 使用保存的时间范围获取数据
      const response = await analysisService.getRawData(
        datasetId, 
        subjectId,
        timeRange[0],
        timeRange[1] - timeRange[0]
      );
      
      // 修改返回的数据结构，确保包含正确的时间范围信息
      const data = {
        ...response.data,
        times: response.data.times.filter(t => t >= timeRange[0] && t <= timeRange[1]),
        duration: timeRange[1] - timeRange[0],
        timeRange: timeRange
      };

      // 对每个通道的数据进行裁剪
      if (data.data) {
        Object.keys(data.data).forEach(channel => {
          const startIndex = Math.floor(timeRange[0] * response.data.sampling_rate);
          const endIndex = Math.ceil(timeRange[1] * response.data.sampling_rate);
          data.data[channel] = data.data[channel].slice(startIndex, endIndex);
        });
      }
      
      originalData.value = data;
      console.log('useAnalysis: Original data fetched with time range:', timeRange);
      
      return originalData.value;
    } catch (e) {
      error.value = `获取原始数据失败: ${e.message || e}`;
      ElMessage.error(error.value);
      throw e;
    } finally {
      isLoading.value = false;
    }
  };
  
  /**
   * 获取处理后的数据
   */
  const fetchProcessedData = async () => {
    try {
      // 获取最近一次处理后的数据
      const latestResult = results.value[appliedMethods.value[appliedMethods.value.length - 1]];
      if (latestResult && latestResult.data) {
        processedData.value = latestResult.data;
      }
      return processedData.value;
    } catch (e) {
      error.value = `获取处理后数据失败: ${e.message || e}`;
      console.error(error.value);
      return null;
    }
  };

  // 初始化时加载保存的结果
  loadSavedResults();
  
  return {
    // 状态
    isLoading,
    error,
    originalData,
    processedData,
    preprocessParams,
    currentTaskId,
    taskStatus,
    availableMethods,
    appliedMethods,
    results,
    
    // 方法
    loadPreprocessTemplate,
    getPreprocessStatus,
    runAnalysis,
    fetchOriginalData,
    fetchProcessedData,
    saveResults
  };
}