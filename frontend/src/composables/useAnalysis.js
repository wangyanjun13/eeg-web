import { ref, reactive, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useFormState } from './useFormState';
import analysisService from '@/services/analysisService';

/**
 * 分析功能钩子
 * @param {string} datasetId 数据集ID
 * @param {string} subjectId 被试ID
 * @returns {Object} 分析相关状态和方法
 */
export function useAnalysis(datasetId, subjectId) {
  // 使用 localStorage 存储分析结果，以便在不同页面间共享
  const storageKey = `analysis-${datasetId}-${subjectId}`;
  
  // 分析结果
  const results = ref(null);
  const isLoading = ref(false);
  const error = ref(null);
  
  // 预处理参数
  const { formState: preprocessParams } = useFormState(`preprocess-${datasetId}-${subjectId}`, {
    // 默认预处理参数
    filter: {
      highpass_filter: true,
      highpass: 1.0,
      lowpass_filter: true,
      lowpass: 40.0,
      notch_filter: true,
      notch_freq: 50.0
    },
    reference: {
      method: 'average',
      custom_ref: []
    },
    // ... 其他预处理参数
  });
  
  // 从 localStorage 恢复分析结果
  const loadSavedResults = () => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        results.value = JSON.parse(saved);
      }
    } catch (e) {
      console.error('Failed to load saved analysis results', e);
    }
  };
  
  // 保存分析结果到 localStorage
  const saveResults = () => {
    if (results.value) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(results.value));
      } catch (e) {
        console.error('Failed to save analysis results', e);
      }
    }
  };
  
  /**
   * 加载预处理模板
   * @param {string} templateName 模板名称
   */
  const loadPreprocessTemplate = async (templateName) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await analysisService.getPreprocessTemplate(templateName);
      Object.assign(preprocessParams, response.data);
    } catch (err) {
      error.value = err.message || '加载预处理模板失败';
    } finally {
      isLoading.value = false;
    }
  };
  
  /**
   * 执行分析
   * @param {string} type 分析类型
   * @param {Object} params 分析参数
   */
  const runAnalysis = async (type, params) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      let response;
      
      switch (type) {
        case 'preprocess':
          response = await analysisService.runPreprocessing(datasetId, subjectId, params);
          break;
        case 'time':
          response = await analysisService.runTimeAnalysis(datasetId, subjectId, params);
          break;
        case 'frequency':
          response = await analysisService.runFrequencyAnalysis(datasetId, subjectId, params);
          break;
        case 'spatial':
          response = await analysisService.runSpatialAnalysis(datasetId, subjectId, params);
          break;
        case 'advanced':
          response = await analysisService.runAdvancedAnalysis(datasetId, subjectId, params);
          break;
        default:
          throw new Error('未知的分析类型');
      }
      
      results.value = response.data;
      saveResults();
      return response.data;
    } catch (err) {
      error.value = err.message || '分析执行失败';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };
  
  // 初始化时加载保存的结果
  loadSavedResults();
  
  return {
    isLoading,
    results,
    error,
    preprocessParams,
    loadPreprocessTemplate,
    runAnalysis,
    loadSavedResults,
    saveResults
  };
} 