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
  async applyFilter(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/filter`, 
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      // 将缓存信息添加到返回的数据中
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('滤波处理请求失败:', error);
      throw error;
    }
  },

  /**
   * 应用重采样
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 重采样参数
   * @returns {Promise<Object>} - 处理结果
   */
  async applyResample(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/resample`, 
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('重采样请求失败:', error);
      throw error;
    }
  },

  /**
   * 应用参考设置
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 参考参数
   * @returns {Promise<Object>} - 处理结果
   */
  async applyReference(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/reference`, 
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('参考设置请求失败:', error);
      throw error;
    }
  },

  /**
   * 检测坏通道
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 坏通道检测参数
   * @returns {Promise<Object>} - 处理结果
   */
  async detectBadChannels(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/bad_channels`, 
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('坏通道检测请求失败:', error);
      throw error;
    }
  },

  /**
   * 数据分段
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分段参数
   * @returns {Promise<Object>} - 处理结果
   */
  async segmentData(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/segment`, 
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('数据分段请求失败:', error);
      throw error;
    }
  },

  /**
   * 检测并剔除坏段
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 坏段处理参数
   * @returns {Promise<Object>} - 处理结果
   */
  async detectBadSegments(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/bad_segments`, 
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('坏段处理请求失败:', error);
      throw error;
    }
  },

  /**
   * 运行ICA分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - ICA参数
   * @returns {Promise<Object>} - 处理结果
   */
  async runICA(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/ica`,
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('ICA分析请求失败:', error);
      throw error;
    }
  },

  /**
   * 去除伪迹
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 伪迹参数
   * @returns {Promise<Object>} - 处理结果
   */
  async removeArtifacts(datasetId, subjectId, params) {
    try {
      const response = await axios.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/artifacts`,
        params
      );
      
      // 从响应中提取缓存状态信息
      const data = response.data?.data || {};
      const fromCache = response.headers['x-from-cache'] === 'true';
      const processTime = parseFloat(response.headers['x-process-time'] || '0');
      
      return {
        ...response.data,
        data: {
          ...data,
          from_cache: fromCache,
          process_time: processTime
        }
      };
    } catch (error) {
      console.error('伪迹去除请求失败:', error);
      throw error;
    }
  },

  /**
   * 获取事件信息
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @returns {Promise<Object>} - 事件信息
   */
  getEvents(datasetId, subjectId) {
    return api.get(`/api/preprocess/${datasetId}/subjects/${subjectId}/events`);
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