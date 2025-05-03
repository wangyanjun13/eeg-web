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
          sanitizedParams[key] = 0;
        }
      }
      
      // 保存分段参数，用于后续处理
      const segmentStartTime = sanitizedParams.start_time || 0;
      const segmentEndTime = sanitizedParams.end_time || 10;
      
      // 发起请求
      console.log(`发起分段请求: /api/preprocess/${datasetId}/subjects/${subjectId}/segment`);
      const response = await api.post(
        `/api/preprocess/${datasetId}/subjects/${subjectId}/segment`, 
        sanitizedParams
      );
      
      // 添加详细日志查看响应结构
      console.log("分段响应结构:", JSON.stringify(response.data));
      
      if (!response || !response.data) {
        throw new Error('服务器返回空数据');
      }
      
      // 提取和处理分段结果
      const responseData = response.data;
      
      // 创建标准化的结果对象
      const segmentResult = {
        data: {},  // 通道数据
        times: [], // 时间点
        channels: [],  // 通道列表
        sampling_rate: 0,  // 采样率
        duration: 0,   // 持续时间
        dataset_id: datasetId,
        subject_id: subjectId
      };
      
      // 1. 处理data字段
      if (responseData.data) {
        if (typeof responseData.data === 'object') {
          // 检查是否有通道数据
          const possibleChannels = Object.keys(responseData.data).filter(
            key => Array.isArray(responseData.data[key])
          );
          
          if (possibleChannels.length > 0) {
            // 直接使用responseData.data作为通道数据
            segmentResult.data = responseData.data;
            segmentResult.channels = possibleChannels;
          } else if (responseData.data.data && typeof responseData.data.data === 'object') {
            // 嵌套的data.data结构
            segmentResult.data = responseData.data.data;
            
            // 从嵌套结构中提取其他字段
            if (Array.isArray(responseData.data.channels)) {
              segmentResult.channels = responseData.data.channels;
            }
            
            if (Array.isArray(responseData.data.times)) {
              segmentResult.times = responseData.data.times;
            }
            
            if (responseData.data.sampling_rate) {
              segmentResult.sampling_rate = responseData.data.sampling_rate;
            }
            
            if (responseData.data.duration) {
              segmentResult.duration = responseData.data.duration;
            }
          }
        }
      }
      
      // 2. 确保times字段存在并正确映射到分段时间窗口
      if (!segmentResult.times || segmentResult.times.length === 0) {
        // 找到任何一个通道数据来确定长度
        const anyChannel = Object.keys(segmentResult.data)[0];
        const timeLength = anyChannel && segmentResult.data[anyChannel] ? 
                           segmentResult.data[anyChannel].length : 100;
        
        // 创建映射到选定时间窗口的新时间数组
        const segmentDuration = segmentEndTime - segmentStartTime;
        segmentResult.times = Array.from(
          {length: timeLength}, 
          (_, i) => segmentStartTime + (i * segmentDuration / (timeLength - 1))
        );
        
        console.log(`创建了新的时间数组，范围从 ${segmentResult.times[0]} 到 ${segmentResult.times[segmentResult.times.length-1]}`);
      } else {
        // 检查时间数组是否与预期的分段时间窗口匹配
        const firstTime = segmentResult.times[0];
        const lastTime = segmentResult.times[segmentResult.times.length - 1];
        
        // 如果时间范围与预期不符，应进行调整
        if (Math.abs(firstTime - segmentStartTime) > 0.1 || Math.abs(lastTime - (segmentEndTime - segmentStartTime)) > 0.1) {
          console.warn(`时间数组范围不匹配: ${firstTime}-${lastTime}, 预期: ${segmentStartTime}-${segmentEndTime}`);
          
          // 调整时间数组，保持相对间隔比例不变
          const timeLength = segmentResult.times.length;
          const segmentDuration = segmentEndTime - segmentStartTime;
          
          segmentResult.times = Array.from(
            {length: timeLength}, 
            (_, i) => segmentStartTime + (i * segmentDuration / (timeLength - 1))
          );
          
          console.log(`已调整时间数组，新范围从 ${segmentResult.times[0]} 到 ${segmentResult.times[segmentResult.times.length-1]}`);
        }
      }
      
      // 3. 确保所有通道都有数据
      segmentResult.channels.forEach(channel => {
        if (!segmentResult.data[channel] || !Array.isArray(segmentResult.data[channel])) {
          console.warn(`通道 ${channel} 缺少数据，创建默认数据`);
          segmentResult.data[channel] = new Array(segmentResult.times.length).fill(0);
        } else if (segmentResult.data[channel].length !== segmentResult.times.length) {
          // 调整数据长度以匹配时间数组
          console.warn(`通道 ${channel} 数据长度(${segmentResult.data[channel].length})与时间数组长度(${segmentResult.times.length})不匹配，调整中`);
          
          const newData = new Array(segmentResult.times.length).fill(0);
          const copyLength = Math.min(segmentResult.times.length, segmentResult.data[channel].length);
          
          for (let i = 0; i < copyLength; i++) {
            newData[i] = segmentResult.data[channel][i];
          }
          
          segmentResult.data[channel] = newData;
        }
      });
      
      // 4. 设置元数据字段
      segmentResult.sampling_rate = segmentResult.sampling_rate || responseData.data.sampling_rate || 100;
      segmentResult.duration = segmentEndTime - segmentStartTime;
      
      // 5. 设置正确的timeRange字段
      segmentResult.timeRange = [segmentStartTime, segmentEndTime];
      
      console.log(`最终分段结果: 时间范围=${segmentResult.timeRange}, 数据长度=${segmentResult.times.length}`);
      
      return { data: segmentResult };
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