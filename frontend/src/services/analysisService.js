import axios from 'axios';
import api from './api';

// 创建一个新的axios实例，使用完整URL用于外网访问
const axiosInstance = axios.create({
  baseURL: 'https://api.eeg-visualization-platform.site',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器，添加认证信息
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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
      const response = await axiosInstance.post(
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
      const response = await axiosInstance.post(
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
      const response = await axiosInstance.post(
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
      console.log('发送坏通道检测请求:', params);
      const response = await axiosInstance.post(
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
      // console.log("分段响应结构:", JSON.stringify(response.data));
      
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
          (_, i) => segmentStartTime + (i * segmentDuration / (timeLength - 1 || 1))
        );
      } else {
        // 检查时间数组是否与预期的分段时间窗口匹配
        const firstTime = segmentResult.times[0];
        const lastTime = segmentResult.times[segmentResult.times.length - 1];
        
        // 如果时间范围与预期差距较大，则重新生成时间数组
        if (Math.abs(firstTime - segmentStartTime) > 0.1 || Math.abs(lastTime - segmentEndTime) > 0.1) {
          // 调整时间数组以完全覆盖选定的时间窗口
          const timeLength = segmentResult.times.length;
          const segmentDuration = segmentEndTime - segmentStartTime;
          
          segmentResult.times = Array.from(
            {length: timeLength}, 
            (_, i) => segmentStartTime + (i * segmentDuration / (timeLength - 1 || 1))
          );
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
      if (sanitizedParams.segment_mode === 'event') {
        // 对于事件相关，时间窗口应该是 [-time_before, time_after]
        const totalDuration = sanitizedParams.time_before + sanitizedParams.time_after;
        segmentResult.timeRange = [-sanitizedParams.time_before, sanitizedParams.time_after];
        segmentResult.duration = totalDuration;
        
        // 设置段信息以便于用户了解
        segmentResult.segment_info = {
          type: "event_related",
          event_id: sanitizedParams.event_id,
          time_before: sanitizedParams.time_before,
          time_after: sanitizedParams.time_after,
          events_processed: responseData.data.segment_info?.event_count || 0,
          original_time_range: sanitizedParams.use_original_full_data ? 
            [0, responseData.data.duration || 0] : 
            [sanitizedParams.start_time || 0, sanitizedParams.end_time || 10]
        };
        
        // 调整时间数组以反映事件为中心的时间窗口
        if (segmentResult.times && segmentResult.times.length > 0) {
          const timeLength = segmentResult.times.length;
          segmentResult.times = Array.from(
            {length: timeLength}, 
            (_, i) => -sanitizedParams.time_before + (i * totalDuration / (timeLength - 1))
          );
        }
      } else {
        // 时间窗口模式 - 确保明确设置timeRange
        segmentResult.timeRange = [segmentStartTime, segmentEndTime];
        
        // 明确告知前端这是时间窗口分段
        segmentResult.segment_info = {
          type: "time_window",
          start_time: segmentStartTime,
          end_time: segmentEndTime,
          duration: segmentEndTime - segmentStartTime
        };
      }
      
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
      const response = await axiosInstance.post(
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
      const response = await axiosInstance.post(
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
      const response = await axiosInstance.post(
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
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/events`);
  },

  /**
   * 进行时域分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分析参数
   * @returns {Promise<Object>} - 分析结果
   */
  performTimeAnalysis(datasetId, subjectId, params) {
    // 检查是否有预处理数据
    try {
      console.log('performTimeAnalysis开始，检查是否有预处理数据');
      const preprocessedData = localStorage.getItem('preprocessed_data');
      if (preprocessedData) {
        console.log('在localStorage中找到了preprocessed_data');
        const parsedData = JSON.parse(preprocessedData);
        console.log('预处理数据基本信息:', {
          datasetId: parsedData.datasetId,
          subjectId: parsedData.subjectId,
          timestamp: parsedData.timestamp,
          hasData: !!parsedData.data,
          metadata: parsedData.metadata
        });
        
        // 检查数据是否匹配当前的数据集和受试者
        if (parsedData.datasetId === datasetId && 
            parsedData.subjectId === subjectId) {
          console.log('预处理数据匹配当前数据集和受试者');
          
          // 检查数据是否过期（24小时）
          const dataAge = Date.now() - parsedData.timestamp;
          const oneDayMs = 24 * 60 * 60 * 1000;
          
          if (dataAge < oneDayMs) {
            console.log('使用预处理后的数据进行时域分析，数据有效期内', {
              dataAge,
              oneDayMs,
              dataChannels: parsedData.data?.channels?.length || 0
            });
            
            // 将完整的预处理数据添加到参数中
            params.use_preprocessed_data = true;
            params.preprocessed_data = parsedData.data;
            console.log('已将预处理数据添加到请求参数中');
            
            // 如果预处理数据中有时间范围，使用它来自动设置时间窗口和基线
            if (parsedData.data.timeRange && Array.isArray(parsedData.data.timeRange) && parsedData.data.timeRange.length === 2) {
              const [startTime, endTime] = parsedData.data.timeRange;
              console.log('预处理数据包含时间范围:', [startTime, endTime]);
              
              // 如果没有明确设置时间窗口，就使用预处理数据的时间范围
              if (!params.timeWindow) {
                params.timeWindow = [...parsedData.data.timeRange];
                console.log('使用预处理数据中的时间范围作为时间窗口:', params.timeWindow);
              }
              
              // 如果没有明确设置基线，且起始时间是负值，自动设置基线区间
              if (!params.baseline && startTime < 0) {
                params.baseline = [startTime, 0]; // 基线区间从起始时间到事件发生时刻
                console.log('自动设置基线校正区间:', params.baseline);
              }
            }
          } else {
            // 数据已过期，从localStorage中移除
            console.log('预处理数据已过期，将被移除', { dataAge, oneDayMs });
            localStorage.removeItem('preprocessed_data');
            
            // 提示用户数据已过期
            const expiredTime = new Date(parsedData.timestamp);
            throw new Error(`预处理数据已过期（超过24小时）。创建时间: ${expiredTime.toLocaleString()}`);
          }
        } else {
          console.log('预处理数据不匹配当前数据集/受试者', {
            expected: { datasetId, subjectId },
            actual: { datasetId: parsedData.datasetId, subjectId: parsedData.subjectId }
          });
        }
      } else {
        console.log('localStorage中没有找到preprocessed_data');
      }
    } catch (e) {
      console.warn('读取预处理数据失败', e);
    }
    
    // 确保baseline参数格式正确
    if (params.baseline && !Array.isArray(params.baseline)) {
      console.warn('baseline参数不是数组格式，进行转换');
      if (params.baseline.enabled) {
        params.baseline = [params.baseline.start / 1000, params.baseline.end / 1000];
      } else {
        params.baseline = null;
      }
    }
    
    // 确保timeWindow参数格式正确
    if (params.timeWindow && !Array.isArray(params.timeWindow)) {
      console.warn('timeWindow参数不是数组格式，进行转换');
      params.timeWindow = [params.timeWindow.start / 1000, params.timeWindow.end / 1000];
    }
    
    console.log('发送时域分析请求到后端', {
      url: `/api/analysis/${datasetId}/subjects/${subjectId}/erp`,
      usePreprocessedData: params.use_preprocessed_data,
      hasPreprocessedData: !!params.preprocessed_data,
      baseline: params.baseline,
      timeWindow: params.timeWindow,
      events: params.events
    });
    
    return api.post(`/api/analysis/${datasetId}/subjects/${subjectId}/erp`, params);
  },

  /**
   * 进行频域分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分析参数
   * @returns {Promise<Object>} - 分析结果
   */
  performFrequencyAnalysis(datasetId, subjectId, params) {
    // 检查是否有预处理数据
    try {
      const preprocessedData = localStorage.getItem('preprocessed_data');
      if (preprocessedData) {
        const parsedData = JSON.parse(preprocessedData);
        
        // 检查数据是否匹配当前的数据集和受试者
        if (parsedData.datasetId === datasetId && 
            parsedData.subjectId === subjectId) {
          
          // 检查数据是否过期（24小时）
          const dataAge = Date.now() - parsedData.timestamp;
          const oneDayMs = 24 * 60 * 60 * 1000;
          
          if (dataAge < oneDayMs) {
            console.log('使用预处理后的数据进行频域分析');
            
            // 将完整的预处理数据添加到参数中
            params.use_preprocessed_data = true;
            params.preprocessed_data = parsedData.data;
          } else {
            // 数据已过期，从localStorage中移除
            console.log('预处理数据已过期，将被移除');
            localStorage.removeItem('preprocessed_data');
          }
        }
      }
    } catch (e) {
      console.warn('读取预处理数据失败', e);
    }
    
    return api.post(`/api/analysis/${datasetId}/subjects/${subjectId}/time_freq`, params);
  },

  /**
   * 进行空间分析
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   * @param {Object} params - 分析参数
   * @returns {Promise<Object>} - 分析结果
   */
  performSpatialAnalysis(datasetId, subjectId, params) {
    // 检查是否有预处理数据
    try {
      const preprocessedData = localStorage.getItem('preprocessed_data');
      if (preprocessedData) {
        const parsedData = JSON.parse(preprocessedData);
        
        // 检查数据是否匹配当前的数据集和受试者
        if (parsedData.datasetId === datasetId && 
            parsedData.subjectId === subjectId) {
          
          // 检查数据是否过期（24小时）
          const dataAge = Date.now() - parsedData.timestamp;
          const oneDayMs = 24 * 60 * 60 * 1000;
          
          if (dataAge < oneDayMs) {
            console.log('使用预处理后的数据进行空间分析');
            
            // 将完整的预处理数据添加到参数中
            params.use_preprocessed_data = true;
            params.preprocessed_data = parsedData.data;
          } else {
            // 数据已过期，从localStorage中移除
            console.log('预处理数据已过期，将被移除');
            localStorage.removeItem('preprocessed_data');
          }
        }
      }
    } catch (e) {
      console.warn('读取预处理数据失败', e);
    }
    
    return api.post(`/api/analysis/${datasetId}/subjects/${subjectId}/connectivity`, params);
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
   * 获取时域分析示例数据
   * @returns {Promise<Object>} - 示例数据
   */
  getTimeAnalysisExample() {
    return api.get('/api/analysis/examples/time');
  },

  /**
   * 获取频域分析示例数据
   * @returns {Promise<Object>} - 示例数据
   */
  getFrequencyAnalysisExample() {
    return api.get('/api/analysis/examples/frequency');
  },

  /**
   * 获取空间分析示例数据
   * @returns {Promise<Object>} - 示例数据
   */
  getSpatialAnalysisExample() {
    return api.get('/api/analysis/examples/spatial');
  },

  /**
   * 运行时域分析
   * @param {Object} params - 分析参数，包含datasetId, subjectId, baseline, timeWindow, events等
   * @returns {Promise<Object>} - 分析结果
   */
  async runTimeAnalysis(params) {
    try {
      console.log('发送时域分析请求，参数:', params);
      
      // 确保参数完整
      if (!params.datasetId || !params.subjectId) {
        throw new Error('缺少必要的数据集和受试者ID参数');
      }
      
      // 检查并转换参数
      if (params.baseline && !Array.isArray(params.baseline)) {
        console.log('baseline参数不是数组格式，正在转换...');
        if (typeof params.baseline === 'object' && params.baseline.hasOwnProperty('enabled')) {
          params.baseline = params.baseline.enabled 
            ? [params.baseline.start / 1000, params.baseline.end / 1000] 
            : null;
        } else {
          console.warn('baseline参数格式不规范，设置为默认值');
          params.baseline = [-0.2, 0];
        }
      }
      
      if (params.timeWindow && !Array.isArray(params.timeWindow)) {
        console.log('timeWindow参数不是数组格式，正在转换...');
        if (typeof params.timeWindow === 'object') {
          params.timeWindow = [params.timeWindow.start / 1000, params.timeWindow.end / 1000];
        } else {
          console.warn('timeWindow参数格式不规范，设置为默认值');
          params.timeWindow = [-0.2, 0.8];
        }
      }
      
      // 确保事件列表存在且是数组
      if (!params.events || !Array.isArray(params.events) || params.events.length === 0) {
        console.warn('events参数为空或不是数组，尝试获取预处理数据中的事件');
        
        // 尝试从预处理数据中获取事件
        const preprocessedData = localStorage.getItem('preprocessed_data');
        if (preprocessedData) {
          try {
            const parsedData = JSON.parse(preprocessedData);
            if (parsedData.data && parsedData.datasetId === params.datasetId && 
                parsedData.subjectId === params.subjectId) {
              
              // 检查是否有时间范围，用于过滤事件
              const timeRange = params.timeWindow || parsedData.data.timeRange;
              console.log('时间窗口范围:', timeRange);
              
              if (parsedData.data.events) {
                let eventList = [];
                
                // 处理不同格式的事件数据
                if (Array.isArray(parsedData.data.events)) {
                  // 数组格式的事件列表
                  console.log('预处理数据中的事件是数组格式, 总数:', parsedData.data.events.length);
                  
                  // 先检查事件结构
                  const sampleEvent = parsedData.data.events[0];
                  console.log('事件数据结构样例:', sampleEvent);
                  
                  // 如果事件有时间信息且有时间范围，进行过滤
                  if (timeRange && parsedData.data.events.some(e => e.time !== undefined || e.latency !== undefined || e.onset !== undefined)) {
                    console.log(`根据时间范围 [${timeRange[0]}, ${timeRange[1]}] 过滤事件`);
                    
                    // 过滤在时间范围内的事件
                    eventList = parsedData.data.events.filter(event => {
                      // 获取事件时间（秒）
                      const eventTime = 
                        event.time !== undefined ? event.time : 
                        event.latency !== undefined ? event.latency / 1000 : 
                        event.onset !== undefined ? event.onset : null;
                      
                      // 如果没有时间信息，保留该事件
                      if (eventTime === null) {
                        console.log(`事件 ${event.id || event} 没有时间信息，默认保留`);
                        return true;
                      }
                      
                      const isInRange = eventTime >= timeRange[0] && eventTime <= timeRange[1];
                      if (isInRange) {
                        console.log(`事件 ${event.id || event} 在时间范围内，时间点: ${eventTime}`);
                      }
                      return isInRange;
                    });
                    
                    console.log(`过滤后的事件数量: ${eventList.length}/${parsedData.data.events.length}`);
                  } else {
                    // 没有时间信息或没有时间范围，使用所有事件
                    console.log('没有找到时间信息或时间范围，使用全部事件');
                    eventList = [...parsedData.data.events];
                  }
                  
                  // 提取事件ID
                  params.events = eventList.map(event => {
                    const eventId = event.id !== undefined ? event.id : (typeof event === 'number' ? event : null);
                    if (eventId === null && typeof event === 'object') {
                      console.warn('事件对象没有ID属性:', event);
                      return 1; // 默认ID
                    }
                    return eventId;
                  }).filter(id => id !== null);
                } else if (typeof parsedData.data.events === 'object') {
                  // 对象格式的事件列表
                  console.log('预处理数据中的事件是对象格式');
                  
                  const eventMap = parsedData.data.events;
                  const eventIds = Object.keys(eventMap);
                  
                  console.log(`找到 ${eventIds.length} 个事件类型`);
                  
                  // 如果事件有时间信息且有时间范围，进行过滤
                  if (timeRange && Object.values(eventMap).some(e => e.time !== undefined || e.latency !== undefined || e.onset !== undefined)) {
                    console.log(`根据时间范围 [${timeRange[0]}, ${timeRange[1]}] 过滤事件`);
                    
                    // 过滤在时间范围内的事件
                    const filteredIds = eventIds.filter(id => {
                      const event = eventMap[id];
                      // 获取事件时间（秒）
                      const eventTime = 
                        event.time !== undefined ? event.time : 
                        event.latency !== undefined ? event.latency / 1000 : 
                        event.onset !== undefined ? event.onset : null;
                      
                      // 如果没有时间信息，保留该事件
                      if (eventTime === null) {
                        console.log(`事件类型 ${id} 没有时间信息，默认保留`);
                        return true;
                      }
                      
                      const isInRange = eventTime >= timeRange[0] && eventTime <= timeRange[1];
                      if (isInRange) {
                        console.log(`事件类型 ${id} 在时间范围内，时间点: ${eventTime}`);
                      }
                      return isInRange;
                    });
                    
                    console.log(`过滤后的事件类型数量: ${filteredIds.length}/${eventIds.length}`);
                    params.events = filteredIds.map(id => parseInt(id) || id);
                  } else {
                    // 没有时间信息或没有时间范围，使用所有事件ID
                    console.log('没有找到时间信息或时间范围，使用全部事件类型');
                    params.events = eventIds.map(id => parseInt(id) || id);
                  }
                }
                
                console.log('从预处理数据中读取事件列表:', params.events);
              } else {
                console.log('预处理数据中没有找到事件信息');
              }
            } else {
              console.log('预处理数据不匹配当前数据集/受试者');
            }
          } catch (error) {
            console.error('解析预处理数据时出错:', error);
          }
        } else {
          console.log('没有找到预处理数据');
        }
        
        // 如果仍然没有事件，添加默认事件
        if (!params.events || !Array.isArray(params.events) || params.events.length === 0) {
          params.events = [1]; // 添加默认事件ID
          console.log('未找到有效事件，使用默认事件ID:', params.events);
        }
      }
      
      console.log('格式化后的参数:', {
        baseline: params.baseline,
        timeWindow: params.timeWindow,
        events: params.events
      });
      
      // 使用现有的performTimeAnalysis方法，保持兼容性
      return this.performTimeAnalysis(params.datasetId, params.subjectId, {
        baseline: params.baseline,
        timeWindow: params.timeWindow,
        events: params.events
      });
    } catch (error) {
      console.error('时域分析请求失败:', error);
      throw error;
    }
  }
};

export default analysisService; 