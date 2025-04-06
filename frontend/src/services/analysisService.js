import axios from 'axios';
import api from './api';

/**
 * 分析服务 - 提供对EEG数据进行各种分析的API接口
 */
const analysisService = {
  /**
   * 获取原始EEG数据
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {number} startTime - 开始时间(秒)
   * @param {number} duration - 持续时间(秒) 
   * @returns {Promise<Object>} - 原始EEG数据
   */
  getRawData(datasetId, subjectId, startTime = 0, duration = 10) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/raw`, {
      params: {
        start_time: startTime,
        duration: duration
      }
    });
  },

  /**
   * 获取预处理模板
   * @param {string} templateName - 模板名称
   * @returns {Promise<Object>} - 预处理模板
   */
  getPreprocessTemplate(templateName) {
    return api.get(`/api/preprocess/templates/${templateName}`);
  },

  /**
   * 获取所有预处理模板
   * @returns {Promise<Object>} - 所有预处理模板
   */
  getAllPreprocessTemplates() {
    return api.get(`/api/preprocess/templates`);
  },

  /**
   * 对数据进行预处理
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 预处理参数
   * @returns {Promise<Object>} - 处理结果
   */
  preprocessData(datasetId, subjectId, params) {
    return api.post(`/api/preprocess/${datasetId}/${subjectId}`, params);
  },

  /**
   * 获取预处理任务状态
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} - 任务状态
   */
  getPreprocessStatus(taskId) {
    return api.get(`/api/preprocess/status/${taskId}`);
  },

  /**
   * 应用滤波器
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 滤波参数
   * @returns {Promise<Object>} - 处理结果
   */
  applyFilter(datasetId, subjectId, params) {
    // 确保参数格式正确
    const filterParams = {
      highpass_filter: Boolean(params.highpass_filter),
      highpass: Number(params.highpass) || 1.0,
      lowpass_filter: Boolean(params.lowpass_filter),
      lowpass: Number(params.lowpass) || 40.0,
      notch_filter: Boolean(params.notch_filter),
      line_freqs: Array.isArray(params.line_freqs) ? params.line_freqs.map(Number) : [50.0, 60.0]
    };
    
    return api.post(`/api/preprocess/${datasetId}/subjects/${subjectId}/filter`, filterParams);
  },

  /**
   * 运行ICA分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - ICA参数
   * @returns {Promise<Object>} - 处理结果
   */
  runICA(datasetId, subjectId, params) {
    return api.post(`/api/preprocess/${datasetId}/subjects/${subjectId}/ica`, params);
  },

  /**
   * 去除伪迹
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 伪迹参数
   * @returns {Promise<Object>} - 处理结果
   */
  removeArtifacts(datasetId, subjectId, params) {
    return api.post(`/api/preprocess/${datasetId}/subjects/${subjectId}/artifacts`, params);
  },

  /**
   * 进行时域分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分析参数
   * @returns {Promise<Object>} - 分析结果
   */
  performTimeAnalysis(datasetId, subjectId, params) {
    return api.post(`/api/analysis/time/${datasetId}/${subjectId}`, params);
  },

  /**
   * 进行频域分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分析参数
   * @returns {Promise<Object>} - 分析结果
   */
  performFrequencyAnalysis(datasetId, subjectId, params) {
    return api.post(`/api/analysis/frequency/${datasetId}/${subjectId}`, params);
  },

  /**
   * 进行空间分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分析参数
   * @returns {Promise<Object>} - 分析结果
   */
  performSpatialAnalysis(datasetId, subjectId, params) {
    return api.post(`/api/analysis/spatial/${datasetId}/${subjectId}`, params);
  },

  /**
   * 进行高级分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分析参数
   * @returns {Promise<Object>} - 分析结果
   */
  performAdvancedAnalysis(datasetId, subjectId, params) {
    return api.post(`/api/analysis/advanced/${datasetId}/${subjectId}`, params);
  },

  /**
   * 获取时域分析示例数据（用于开发和测试）
   * @returns {Promise<Object>} - 示例数据
   */
  getTimeAnalysisExample() {
    return api.get(`/api/analysis/examples/time`);
  },

  /**
   * 获取频域分析示例数据（用于开发和测试）
   * @returns {Promise<Object>} - 示例数据
   */
  getFrequencyAnalysisExample() {
    return api.get(`/api/analysis/examples/frequency`);
  },

  /**
   * 获取空间分析示例数据（用于开发和测试）
   * @returns {Promise<Object>} - 示例数据
   */
  getSpatialAnalysisExample() {
    return api.get(`/api/analysis/examples/spatial`);
  },

  /**
   * 获取高级分析示例数据（用于开发和测试）
   * @returns {Promise<Object>} - 示例数据
   */
  getAdvancedAnalysisExample() {
    return api.get(`/api/analysis/examples/advanced`);
  }
};

export default analysisService; 