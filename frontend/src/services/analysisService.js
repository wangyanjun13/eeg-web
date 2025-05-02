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
      // 清理和验证参数
      const sanitizedParams = {};
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && (typeof value !== 'number' || !isNaN(value))) {
          sanitizedParams[key] = value;
        } else if (typeof value === 'number' && isNaN(value)) {
          sanitizedParams[key] = 0; // 将NaN替换为0
        }
      }
      
      console.log(`发起分段请求: /api/preprocess/${datasetId}/subjects/${subjectId}/segment`);
      console.log('请求参数:', JSON.stringify(sanitizedParams, null, 2));
      
      const response = await api.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/segment`, 
        sanitizedParams
      );
      
      // 验证响应数据
      if (!response || !response.data) {
        throw new Error('服务器返回空数据');
      }
      
      // 处理响应数据 - 确保data字段存在
      const result = response.data;
      
      // 确保有效的data字段
      if (!result.data || typeof result.data !== 'object') {
        console.warn('响应缺少有效的data字段，创建空对象');
        result.data = {};
      }
      
      // 获取分段数据
      const segmentData = result.data;
      
      // 确保数据结构中有data对象
      if (!segmentData.data || typeof segmentData.data !== 'object') {
        console.warn('分段结果缺少data字段，创建空对象');
        segmentData.data = {};
      }
      
      // 确保times数组存在且有效
      if (!segmentData.times || !Array.isArray(segmentData.times) || segmentData.times.length === 0) {
        console.warn('分段结果缺少有效的times字段，创建默认时间数组');
        // 创建100个时间点，从0到10秒
        segmentData.times = Array.from({length: 100}, (_, i) => i / 10);
      }
      
      // 确保channels数组存在且有效
      if (!segmentData.channels || !Array.isArray(segmentData.channels) || segmentData.channels.length === 0) {
        console.warn('分段结果缺少channels字段，尝试从data字段推断');
        // 从data对象中提取通道名称
        segmentData.channels = Object.keys(segmentData.data);
        
        if (segmentData.channels.length === 0) {
          console.warn('无法推断channels，创建默认通道');
          // 创建一些默认通道
          segmentData.channels = ['Ch1', 'Ch2', 'Ch3'];
          // 为默认通道创建零填充数据
          segmentData.channels.forEach(ch => {
            segmentData.data[ch] = new Array(segmentData.times.length).fill(0);
          });
        }
      }
      
      // 确保每个channel都有对应的数据数组
      segmentData.channels.forEach(channel => {
        if (!segmentData.data[channel] || !Array.isArray(segmentData.data[channel])) {
          console.warn(`通道 ${channel} 在分段结果中没有有效数据，创建零填充数组`);
          segmentData.data[channel] = new Array(segmentData.times.length).fill(0);
        } else if (segmentData.data[channel].length !== segmentData.times.length) {
          // 长度不匹配时调整数据长度
          const newArray = new Array(segmentData.times.length).fill(0);
          const copyLength = Math.min(segmentData.data[channel].length, segmentData.times.length);
          for(let i = 0; i < copyLength; i++) {
            newArray[i] = segmentData.data[channel][i];
          }
          segmentData.data[channel] = newArray;
        }
      });
      
      // 确保包含必要的ID字段
      segmentData.dataset_id = segmentData.dataset_id || datasetId;
      segmentData.subject_id = segmentData.subject_id || subjectId;
      
      // 添加时间范围字段，便于前端渲染
      if (segmentData.times && segmentData.times.length > 0) {
        segmentData.timeRange = [
          segmentData.times[0],
          segmentData.times[segmentData.times.length - 1]
        ];
      } else {
        segmentData.timeRange = [0, 10]; // 默认时间范围
      }
      
      // 确保采样率存在
      if (!segmentData.sampling_rate) {
        console.warn('分段结果缺少sampling_rate字段，使用默认值');
        segmentData.sampling_rate = 100;
      }
      
      // 确保持续时间存在
      if (!segmentData.duration) {
        console.warn('分段结果缺少duration字段，使用默认值');
        segmentData.duration = segmentData.times[segmentData.times.length - 1] - segmentData.times[0];
      }
      
      // 确保segment_info字段存在
      if (!segmentData.segment_info) {
        segmentData.segment_info = {
          type: params.segment_mode || "time",
          start: params.start_time || 0,
          end: params.end_time || 10
        };
      }
      
      return result;
    } catch (error) {
      console.error('数据分段请求失败:', error);
      throw error;
    }
  },

  /**
   * 验证响应数据的有效性
   * @private
   */
  _validateResponseData(data) {
    // 检查数据的基本结构
    if (!data) {
      throw new Error('响应数据为空');
    }
    
    // 递归替换特殊浮点值
    this._sanitizeFloatValues(data);
    
    return data;
  },

  /**
   * 递归清理对象中的特殊浮点值
   * @private
   */
  _sanitizeFloatValues(obj) {
    if (!obj || typeof obj !== 'object') return obj;
    
    const newObj = Array.isArray(obj) ? [...obj] : {...obj};
    
    Object.keys(newObj).forEach(key => {
      const value = newObj[key];
      if (typeof value === 'number') {
        // 检查并替换NaN和Infinity
        if (isNaN(value)) {
          newObj[key] = 0;
        } else if (!isFinite(value)) {
          newObj[key] = value > 0 ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER;
        }
      } else if (Array.isArray(value)) {
        // 处理数组
        newObj[key] = value.map(item => {
          if (typeof item === 'number') {
            if (isNaN(item)) return 0;
            if (!isFinite(item)) return item > 0 ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER;
          } else if (typeof item === 'object') {
            return this._sanitizeFloatValues(item);
          }
          return item;
        });
      } else if (typeof value === 'object') {
        // 递归处理嵌套对象
        newObj[key] = this._sanitizeFloatValues(value);
      }
    });
    
    return newObj;
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
    // 首先尝试从preprocess API获取事件
    return api.get(`/api/preprocess/${datasetId}/subjects/${subjectId}/events`)
      .catch(error => {
        console.warn('从预处理API获取事件失败，尝试从dataset API获取:', error);
        // 如果预处理API失败，尝试从dataset API获取
        return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/events`)
          .catch(secondError => {
            console.warn('从dataset API获取事件也失败:', secondError);
            // 如果两个API都失败，返回空的事件数据
            return {data: {events: []}};
          });
      });
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