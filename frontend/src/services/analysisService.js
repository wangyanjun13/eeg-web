import api from './api';

export default {
  /**
   * 获取预处理数据
   * @param {string} datasetId 数据集ID
   * @param {string} subjectId 受试者ID
   * @param {Object} options 预处理选项
   * @returns {Promise} 请求结果
   */
  preprocessData(datasetId, subjectId, options) {
    return api.post(`/api/datasets/${datasetId}/subjects/${subjectId}/preprocess`, options);
  },

  /**
   * 执行时域分析
   * @param {Object} params 分析参数
   * @returns {Promise} 请求结果
   */
  performTimeAnalysis(params) {
    return api.post('/api/analysis/time', params);
  },

  /**
   * 执行频域分析
   * @param {Object} params 分析参数
   * @returns {Promise} 请求结果
   */
  performFrequencyAnalysis(params) {
    return api.post('/api/analysis/frequency', params);
  },

  /**
   * 执行空间分析
   * @param {Object} params 分析参数
   * @returns {Promise} 请求结果
   */
  performSpatialAnalysis(params) {
    return api.post('/api/analysis/spatial', params);
  },

  /**
   * 执行高级分析
   * @param {Object} params 分析参数
   * @returns {Promise} 请求结果
   */
  performAdvancedAnalysis(params) {
    return api.post('/api/analysis/advanced', params);
  },

  /**
   * 获取示例时域数据
   * @returns {Promise} 请求结果
   */
  getExampleTimeData() {
    return api.get('/api/examples/time-data');
  },

  /**
   * 获取示例频域数据
   * @returns {Promise} 请求结果
   */
  getExampleFrequencyData() {
    return api.get('/api/examples/frequency-data');
  },

  /**
   * 获取示例空间数据
   * @returns {Promise} 请求结果
   */
  getExampleSpatialData() {
    return api.get('/api/examples/spatial-data');
  },

  /**
   * 获取示例高级分析数据
   * @returns {Promise} 请求结果
   */
  getExampleAdvancedData() {
    return api.get('/api/examples/advanced-data');
  },

  // 应用滤波器
  applyFilter(datasetId, subjectId, params) {
    return api.post(`/api/preprocess/${datasetId}/subjects/${subjectId}/filter`, params);
  },

  // 运行ICA分析
  runICA(datasetId, subjectId, params) {
    return api.post(`/api/preprocess/${datasetId}/subjects/${subjectId}/ica`, params);
  },

  // 去除伪迹
  removeArtifacts(datasetId, subjectId, params) {
    return api.post(`/api/preprocess/${datasetId}/subjects/${subjectId}/artifacts`, params);
  },

  // 获取预处理状态
  getPreprocessStatus(datasetId, subjectId) {
    return api.get(`/api/preprocess/${datasetId}/subjects/${subjectId}/status`);
  },

  /**
   * 获取原始数据
   * @param {string} datasetId 数据集ID
   * @param {string} subjectId 受试者ID
   * @returns {Promise} 请求结果
   */
  getRawData(datasetId, subjectId) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/data`);
  }
}; 