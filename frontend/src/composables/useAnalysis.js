import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import analysisService from '@/services/analysisService';

/**
 * 分析功能钩子
 * @param {Object} options 配置选项
 * @returns {Object} 分析相关状态和方法
 */
export function useAnalysis(options = {}) {
  const isLoading = ref(false);
  const results = ref(null);
  const error = ref(null);
  const preprocessParams = ref(null);

  /**
   * 加载预处理模板
   * @param {string} templateName 模板名称
   */
  async function loadPreprocessTemplate(templateName) {
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await analysisService.getPreprocessTemplate(templateName);
      preprocessParams.value = response;
      return response;
    } catch (err) {
      error.value = err;
      ElMessage.error(`加载模板失败: ${err.message}`);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 执行分析
   * @param {string} type 分析类型
   * @param {Object} params 分析参数
   */
  async function runAnalysis(type, params) {
    isLoading.value = true;
    error.value = null;
    
    try {
      let response;
      
      switch (type) {
        case 'preprocess':
          response = await analysisService.preprocessData(
            params.datasetId,
            params.subjectId,
            params.options
          );
          break;
        case 'time':
          response = await analysisService.performTimeAnalysis(params);
          break;
        case 'frequency':
          response = await analysisService.performFrequencyAnalysis(params);
          break;
        case 'spatial':
          response = await analysisService.performSpatialAnalysis(params);
          break;
        case 'advanced':
          response = await analysisService.performAdvancedAnalysis(params);
          break;
        default:
          throw new Error(`未知的分析类型: ${type}`);
      }
      
      results.value = response;
      ElMessage.success('分析完成');
      return response;
    } catch (err) {
      error.value = err;
      ElMessage.error(`分析失败: ${err.message}`);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    isLoading,
    results,
    error,
    preprocessParams,
    loadPreprocessTemplate,
    runAnalysis
  };
} 