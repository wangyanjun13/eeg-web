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
    }
  });
  
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
   * 保存分析结果到localStorage
   */
  const saveResults = (step, data) => {
    try {
      // 更新结果状态
      results.value[step] = data;
      
      // 记录应用的方法
      if (!appliedMethods.value.includes(step)) {
        appliedMethods.value.push(step);
      }
      
      // 保存到 localStorage
      const savedKey = `analysis_${datasetId}_${subjectId}`;
      const dataToSave = {
        results: results.value,
        appliedMethods: appliedMethods.value
      };
      localStorage.setItem(savedKey, JSON.stringify(dataToSave));
      
      return true;
    } catch (e) {
      console.error('保存处理结果失败:', e);
      return false;
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
      
      // 调用相应的API获取原始数据
      const response = await analysisService.getRawData(datasetId, subjectId);
      originalData.value = response.data;
      
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