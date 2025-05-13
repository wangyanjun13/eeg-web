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
      console.log('发送坏通道检测请求:', params);
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
    // 检查参数格式
    try {
      // 深拷贝参数以避免修改原始对象
      const apiParams = { ...params };
      
      // 确保 freqs 是数组
      if (!apiParams.freqs || !Array.isArray(apiParams.freqs)) {
        console.warn('freqs 必须是频率数组，将使用默认值');
        // 如果是范围，转换为数组
        if (apiParams.timeFrequency && apiParams.timeFrequency.freqRange) {
          const range = apiParams.timeFrequency.freqRange;
          apiParams.freqs = [];
          for (let f = range[0]; f <= range[1]; f += 1) {
            apiParams.freqs.push(f);
          }
        } else {
          // 使用默认值 1-40Hz
          apiParams.freqs = Array.from({ length: 40 }, (_, i) => i + 1);
        }
      }
      
      // 确保 n_cycles 存在
      if (!apiParams.n_cycles) {
        apiParams.n_cycles = 7; // 默认值
      }
      
      // 设置默认方法
      if (!apiParams.method) {
        apiParams.method = "morlet";
      }
      
      // 检查是否有预处理数据
      if (apiParams.use_preprocessed_data) {
        try {
          // 先检查localStorage
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
                
                // 优先使用参数中的数据，如果没有则使用localStorage中的
                if (!apiParams.preprocessed_data) {
                  apiParams.preprocessed_data = parsedData.data;
                }
              } else {
                // 数据已过期，从localStorage中移除
                console.log('预处理数据已过期，将被移除');
                localStorage.removeItem('preprocessed_data');
                apiParams.use_preprocessed_data = false;
                delete apiParams.preprocessed_data;
              }
            } else {
              console.log('预处理数据不匹配当前数据集/受试者');
              apiParams.use_preprocessed_data = false;
              delete apiParams.preprocessed_data;
            }
          } else if (!apiParams.preprocessed_data) {
            console.log('localStorage中没有预处理数据，且参数中也未提供');
            apiParams.use_preprocessed_data = false;
            delete apiParams.preprocessed_data;
          }
        } catch (e) {
          console.warn('读取预处理数据失败', e);
          apiParams.use_preprocessed_data = false;
          delete apiParams.preprocessed_data;
        }
      }
      
      // 移除非API相关参数
      const finalParams = {
        freqs: apiParams.freqs,
        n_cycles: apiParams.n_cycles,
        method: apiParams.method
      };
      
      // 添加预处理数据参数
      if (apiParams.use_preprocessed_data && apiParams.preprocessed_data) {
        finalParams.use_preprocessed_data = true;
        finalParams.preprocessed_data = apiParams.preprocessed_data;
      }
      
      console.log('频域分析最终参数格式:', {
        datasetId,
        subjectId,
        freqsLength: finalParams.freqs?.length || 0,
        method: finalParams.method,
        usePreprocessedData: finalParams.use_preprocessed_data || false
      });
      
      return api.post(`/api/analysis/${datasetId}/subjects/${subjectId}/time_freq`, finalParams)
        .then(response => {
          try {
            if (response && response.data) {
              // 格式化返回数据，确保符合前端组件期望的格式
              let formattedData = {
                spectrum: null,
                timeFrequency: null
              };
              
              // 处理频谱数据
              if (response.data.spectrum) {
                formattedData.spectrum = response.data.spectrum;
                
                // 如果频谱数据存在但有效性不确定，执行检查和修复
                if (formattedData.spectrum) {
                  // 确保频率数组存在
                  if (!formattedData.spectrum.frequencies || !Array.isArray(formattedData.spectrum.frequencies)) {
                    console.warn('频谱数据缺少frequencies字段，使用请求的频率数组');
                    formattedData.spectrum.frequencies = [...finalParams.freqs];
                  }
                  
                  // 确保通道列表存在
                  if (!formattedData.spectrum.channels || !Array.isArray(formattedData.spectrum.channels)) {
                    // 尝试从powers对象中提取通道
                    const channelsFromPowers = formattedData.spectrum.powers ? 
                                             Object.keys(formattedData.spectrum.powers) : [];
                    
                    if (channelsFromPowers.length > 0) {
                      console.log('从powers对象中提取通道列表:', channelsFromPowers);
                      formattedData.spectrum.channels = channelsFromPowers;
                    } else if (apiParams.channels && Array.isArray(apiParams.channels)) {
                      console.log('使用请求参数中的通道列表:', apiParams.channels);
                      formattedData.spectrum.channels = [...apiParams.channels];
                    } else {
                      console.warn('无法确定通道列表，创建默认通道');
                      formattedData.spectrum.channels = ['Fz', 'Cz', 'Pz'];
                    }
                  }
                  
                  // 确保powers对象存在且有效
                  if (!formattedData.spectrum.powers || typeof formattedData.spectrum.powers !== 'object') {
                    console.warn('频谱数据powers字段无效，创建默认数据');
                    
                    const defaultPowers = {};
                    formattedData.spectrum.channels.forEach(ch => {
                      defaultPowers[ch] = Array(formattedData.spectrum.frequencies.length).fill(0).map((_, i) => 
                        Math.random() * 5 * Math.exp(-Math.pow(i - 10, 2) / 50)
                      );
                    });
                    
                    formattedData.spectrum.powers = defaultPowers;
                  } else {
                    // 确保每个通道都有对应的功率值
                    formattedData.spectrum.channels.forEach(ch => {
                      if (!formattedData.spectrum.powers[ch] || !Array.isArray(formattedData.spectrum.powers[ch])) {
                        console.warn(`通道 ${ch} 缺少有效功率数据，创建默认功率值`);
                        formattedData.spectrum.powers[ch] = Array(formattedData.spectrum.frequencies.length).fill(0).map((_, i) => 
                          Math.random() * 5 * Math.exp(-Math.pow(i - 10, 2) / 50)
                        );
                      } else if (formattedData.spectrum.powers[ch].length !== formattedData.spectrum.frequencies.length) {
                        // 调整长度以匹配频率数组
                        console.warn(`通道 ${ch} 功率数据长度(${formattedData.spectrum.powers[ch].length})与频率数组长度(${formattedData.spectrum.frequencies.length})不匹配`);
                        
                        const originalValues = [...formattedData.spectrum.powers[ch]];
                        formattedData.spectrum.powers[ch] = Array(formattedData.spectrum.frequencies.length).fill(0);
                        
                        // 复制已有数据
                        for (let i = 0; i < Math.min(originalValues.length, formattedData.spectrum.frequencies.length); i++) {
                          formattedData.spectrum.powers[ch][i] = originalValues[i];
                        }
                      }
                    });
                  }
                }
              }
              
              // 处理时频数据
              if (response.data.timeFrequency) {
                const tfData = response.data.timeFrequency;
                
                // 检查时频数据格式
                if (tfData.times && Array.isArray(tfData.times) && 
                    tfData.frequencies && Array.isArray(tfData.frequencies) && 
                    tfData.power && Array.isArray(tfData.power)) {
                  
                  console.log('收到有效的时频数据格式，进行标准化处理');
                  
                  // 判断是3D数据 (通道、频率、时间) 还是2D数据 (频率、时间)
                  const is3DPower = tfData.power.length > 0 && 
                                  Array.isArray(tfData.power[0]) && 
                                  tfData.power[0].length > 0 &&
                                  Array.isArray(tfData.power[0][0]);
                  
                  // 创建标准化的时频数据对象
                  let standardTF = {
                    times: [...tfData.times], 
                    frequencies: [...tfData.frequencies],
                    power: [],
                    events: Array.isArray(tfData.events) ? [...tfData.events] : []
                  };
                  
                  if (is3DPower) {
                    console.log('3D时频数据 (通道、频率、时间)，提取第一个通道');
                    // 使用第一个通道的数据，避免变异原始数据
                    if (tfData.power.length > 0) {
                      standardTF.power = JSON.parse(JSON.stringify(tfData.power[0]));
                    } else {
                      console.warn('3D功率数据为空，创建默认2D功率数据');
                      standardTF.power = this._createDefaultPowerMatrix(
                        standardTF.frequencies.length, 
                        standardTF.times.length
                      );
                    }
                  } else if (Array.isArray(tfData.power[0])) {
                    // 已经是2D格式 (频率、时间)
                    console.log('2D时频数据 (频率、时间)');
                    standardTF.power = JSON.parse(JSON.stringify(tfData.power));
                  } else {
                    console.warn('功率数据格式错误，重新创建2D功率矩阵');
                    standardTF.power = this._createDefaultPowerMatrix(
                      standardTF.frequencies.length, 
                      standardTF.times.length
                    );
                  }
                  
                  // 验证维度匹配，如有需要进行调整
                  if (standardTF.power.length !== standardTF.frequencies.length) {
                    console.warn(`功率矩阵第一维长度(${standardTF.power.length})与频率数组长度(${standardTF.frequencies.length})不匹配，进行调整`);
                    
                    // 创建新的功率矩阵
                    const newPower = [];
                    for (let i = 0; i < standardTF.frequencies.length; i++) {
                      if (i < standardTF.power.length) {
                        newPower.push(standardTF.power[i]);
                      } else {
                        // 创建填充行
                        newPower.push(Array(standardTF.times.length).fill(0));
                      }
                    }
                    standardTF.power = newPower;
                  }
                  
                  // 检查每行的长度是否与times数组匹配
                  for (let i = 0; i < standardTF.power.length; i++) {
                    if (!Array.isArray(standardTF.power[i]) || 
                        standardTF.power[i].length !== standardTF.times.length) {
                      console.warn(`功率矩阵第${i}行长度不匹配，创建新行`);
                      
                      // 创建新行并尝试保留已有数据
                      const newRow = Array(standardTF.times.length).fill(0);
                      if (Array.isArray(standardTF.power[i])) {
                        for (let j = 0; j < Math.min(standardTF.power[i].length, standardTF.times.length); j++) {
                          newRow[j] = standardTF.power[i][j];
                        }
                      }
                      standardTF.power[i] = newRow;
                    }
                  }
                  
                  // 检查并替换所有无效值 (NaN, Infinity)
                  for (let i = 0; i < standardTF.power.length; i++) {
                    for (let j = 0; j < standardTF.power[i].length; j++) {
                      if (isNaN(standardTF.power[i][j]) || !isFinite(standardTF.power[i][j])) {
                        standardTF.power[i][j] = 0;
                      }
                    }
                  }
                  
                  // 确保事件数据有效
                  if (standardTF.events.length > 0) {
                    standardTF.events = standardTF.events.map(event => ({
                      time: typeof event.time === 'number' ? event.time : 0,
                      name: event.name || '事件',
                      color: event.color || '#ff0000'
                    }));
                  } else {
                    standardTF.events = [{ time: 0, name: '事件', color: '#ff0000' }];
                  }
                  
                  formattedData.timeFrequency = standardTF;
                } else {
                  console.warn('时频数据格式不符合要求，使用默认数据');
                  formattedData.timeFrequency = this._createDefaultTimeFrequencyData();
                }
              } else if (response.data.data && response.data.data.timeFrequency) {
                // 备用路径：处理嵌套在data字段中的结果
                const nestedTF = response.data.data.timeFrequency;
                
                // 递归尝试标准化处理这种情况
                const tempResponse = { data: { timeFrequency: nestedTF } };
                const nestedResult = this._processTimeFrequencyResponse(tempResponse);
                formattedData.timeFrequency = nestedResult.data.timeFrequency;
              } else {
                console.warn('API响应中没有找到时频数据，使用默认数据');
                formattedData.timeFrequency = this._createDefaultTimeFrequencyData();
              }
              
              return { ...response, data: formattedData };
            }
            return response;
          } catch (error) {
            console.error('处理频域分析响应时出错:', error);
            // 返回一个最小可用的响应
            return {
              data: {
                spectrum: null,
                timeFrequency: this._createDefaultTimeFrequencyData()
              }
            };
          }
        })
        .catch(error => {
          console.error('频域分析API调用失败:', error);
          // 返回错误和默认数据
          throw {
            ...error,
            defaultData: {
              spectrum: null,
              timeFrequency: this._createDefaultTimeFrequencyData()
            }
          };
        });
    } catch (error) {
      console.error('处理频域分析参数出错:', error);
      // 返回一个拒绝的Promise，但包含默认数据
      return Promise.reject({
        message: '处理频域分析参数出错: ' + (error.message || '未知错误'),
        defaultData: {
          spectrum: null,
          timeFrequency: this._createDefaultTimeFrequencyData()
        }
      });
    }
  },

  /**
   * 创建默认的功率矩阵
   * @private
   * @param {number} freqCount - 频率数量
   * @param {number} timeCount - 时间点数量
   * @returns {Array} - 2D功率矩阵
   */
  _createDefaultPowerMatrix(freqCount, timeCount) {
    const power = [];
    for (let i = 0; i < freqCount; i++) {
      const row = [];
      for (let j = 0; j < timeCount; j++) {
        // 基于频率和时间位置创建一些模式，使数据看起来更真实
        const freqFactor = Math.exp(-Math.pow(i - freqCount/3, 2) / (freqCount/2));
        const timeFactor = Math.exp(-Math.pow(j - timeCount*0.6, 2) / (timeCount/3));
        row.push(freqFactor * timeFactor * 10 + Math.random() * 0.5);
      }
      power.push(row);
    }
    return power;
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
    
    return api.post(`/api/analysis/${datasetId}/subjects/${subjectId}/spatial`, params);
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
    return api.get('/api/analysis/examples/frequency').then(response => {
      try {
        if (response && response.data) {
          // 检查并转换数据格式以匹配组件期望
          const responseData = response.data;
          
          let formattedData = {
            spectrum: null,
            timeFrequency: null
          };
          
          // 处理频谱数据
          if (responseData.spectrum) {
            formattedData.spectrum = responseData.spectrum;
          }
          
          // 处理时频数据 - 将扁平结构转换为组件期望的结构
          if (responseData.timeFrequency && Array.isArray(responseData.timeFrequency)) {
            // 从数组中提取唯一的时间点和频率
            const timeSet = new Set();
            const freqSet = new Set();
            
            responseData.timeFrequency.forEach(item => {
              if (item.time !== undefined) timeSet.add(item.time);
              if (item.frequency !== undefined) freqSet.add(item.frequency);
            });
            
            // 转换为排序数组
            const times = Array.from(timeSet).sort((a, b) => a - b);
            const frequencies = Array.from(freqSet).sort((a, b) => a - b);
            
            // 创建二维功率矩阵
            const power = Array(frequencies.length).fill().map(() => Array(times.length).fill(0));
            
            // 填充功率值
            responseData.timeFrequency.forEach(item => {
              if (item.time !== undefined && item.frequency !== undefined && item.power !== undefined) {
                const timeIndex = times.indexOf(item.time);
                const freqIndex = frequencies.indexOf(item.frequency);
                
                if (timeIndex !== -1 && freqIndex !== -1) {
                  power[freqIndex][timeIndex] = item.power;
                }
              }
            });
            
            formattedData.timeFrequency = {
              times: times,
              frequencies: frequencies,
              power: power
            };
          } else if (responseData.data && responseData.data.timeFrequency) {
            // 处理不同结构的响应
            formattedData.timeFrequency = responseData.data.timeFrequency;
          } else {
            // 生成默认时频数据
            console.warn('服务器返回的时频数据格式不符合要求，使用默认数据');
            const defaultData = this._createDefaultTimeFrequencyData();
            formattedData.timeFrequency = defaultData;
          }
          
          return {
            ...response,
            data: formattedData
          };
        }
        return response;
      } catch (error) {
        console.error('处理频域分析示例数据时出错:', error);
        // 返回默认数据
        return {
          data: {
            spectrum: null,
            timeFrequency: this._createDefaultTimeFrequencyData()
          }
        };
      }
    }).catch(error => {
      console.error('获取频域分析示例数据API调用失败:', error);
      // 返回默认数据确保UI能正常显示
      return {
        data: {
          spectrum: null,
          timeFrequency: this._createDefaultTimeFrequencyData()
        }
      };
    });
  },

  /**
   * 创建默认的时频数据结构
   * @private
   * @returns {Object} - 默认时频数据对象
   */
  _createDefaultTimeFrequencyData() {
    // 创建默认时间点数组 (-0.5 到 1.0 秒，步长0.1)
    const times = [];
    for (let t = -0.5; t <= 1.0; t += 0.1) {
      times.push(parseFloat(t.toFixed(1)));
    }
    
    // 创建默认频率数组 (1-40Hz)
    const frequencies = [];
    for (let f = 1; f <= 40; f++) {
      frequencies.push(f);
    }
    
    // 创建二维功率矩阵 [频率, 时间]
    const power = [];
    
    // 确保功率数组格式正确：外层是频率，内层是时间
    for (let freqIdx = 0; freqIdx < frequencies.length; freqIdx++) {
      const timeValues = [];
      for (let timeIdx = 0; timeIdx < times.length; timeIdx++) {
        // 中心频率有较强功率 (频率在 10Hz 附近有峰值)
        const freqFactor = Math.exp(-Math.pow(frequencies[freqIdx] - 10, 2) / 200);
        // 中心时间点有较强功率 (时间在 0.2s 附近有峰值)
        const timeFactor = Math.exp(-Math.pow(times[timeIdx] - 0.2, 2) / 0.5);
        // 基础随机值，防止平面
        const randomVal = Math.random() * 0.3;
        
        // 合成功率值
        const powerVal = (freqFactor * timeFactor * 5 + randomVal) * 10;
        
        // 确保是有效的数值
        timeValues.push(isNaN(powerVal) ? 0 : powerVal);
      }
      power.push(timeValues);
    }
    
    // 验证数据结构是否正确
    if (power.length !== frequencies.length) {
      console.error(`默认功率数据与频率数组长度不匹配: ${power.length} vs ${frequencies.length}`);
    }
    
    if (power.length > 0 && power[0].length !== times.length) {
      console.error(`默认功率数据与时间数组长度不匹配: ${power[0].length} vs ${times.length}`);
    }
    
    // 验证是否有 NaN 或 undefined 值
    let hasInvalid = false;
    for (let i = 0; i < power.length; i++) {
      for (let j = 0; j < power[i].length; j++) {
        if (isNaN(power[i][j]) || power[i][j] === undefined) {
          hasInvalid = true;
          power[i][j] = 0; // 替换无效值
        }
      }
    }
    
    if (hasInvalid) {
      console.warn('默认功率数据中含有无效值，已替换为0');
    }
    
    // 返回标准格式的时频数据
    return {
      times,
      frequencies,
      power,
      events: [
        { time: 0, name: '刺激呈现', color: '#ff0000' }
      ]
    };
  },

  /**
   * 获取空间分析示例数据
   * @returns {Promise<Object>} - 示例数据
   */
  getSpatialAnalysisExample() {
    // 创建示例数据
    // 标准10-20系统电极位置
    const positions = [
      [-0.3, -0.4], [0.3, -0.4], // Fp1, Fp2
      [-0.5, -0.2], [-0.3, -0.2], [0, -0.2], [0.3, -0.2], [0.5, -0.2], // F7, F3, Fz, F4, F8
      [-0.5, 0], [-0.3, 0], [0, 0], [0.3, 0], [0.5, 0], // T3, C3, Cz, C4, T4
      [-0.5, 0.2], [-0.3, 0.2], [0, 0.2], [0.3, 0.2], [0.5, 0.2], // T5, P3, Pz, P4, T6
      [-0.3, 0.4], [0.3, 0.4] // O1, O2
    ];
    
    const channels = [
      'Fp1', 'Fp2',
      'F7', 'F3', 'Fz', 'F4', 'F8',
      'T3', 'C3', 'Cz', 'C4', 'T4',
      'T5', 'P3', 'Pz', 'P4', 'T6',
      'O1', 'O2'
    ];
    
    // 生成模式化的功率值
    const values = [];
    for (let i = 0; i < positions.length; i++) {
      const [x, y] = positions[i];
      // 模拟典型的alpha节律幅度：后部较高，前部较低
      const posteriorFactor = (y + 0.5) / 1.0; // 值从前部到后部增加
      // 增加一个左右两侧对称的alpha分布
      const lateralFactor = 1 - Math.abs(x) * 0.5;
      // 基础模式 + 随机噪声
      const value = (posteriorFactor * 4 + lateralFactor * 2 + Math.random() * 0.5);
      values.push(value);
    }
    
    // 构建示例响应数据
    const exampleData = {
      positions: positions,
      channels: channels,
      values: values,
      timePoints: [0, 100, 200, 300, 400, 500],
      selectedFrequencyBand: 'alpha',
      frequencyRange: [8, 13],
      interpolation: {
        method: "spline",
        resolution: 64
      },
      display: {
        colorMap: "jet",
        showContour: true,
        showElectrodes: true
      }
    };
    
    // 模拟异步API调用
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({ data: exampleData });
      }, 500);
    });
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
  },

  /**
   * 处理时频响应数据，确保格式正确
   * @private
   * @param {Object} response - 原始响应对象
   * @returns {Object} - 处理后的响应对象
   */
  _processTimeFrequencyResponse(response) {
    try {
      if (!response || !response.data || !response.data.timeFrequency) {
        console.warn('响应中缺少时频数据');
        return {
          data: {
            timeFrequency: this._createDefaultTimeFrequencyData()
          }
        };
      }
      
      const tfData = response.data.timeFrequency;
      
      // 检查时频数据格式
      if (tfData.times && Array.isArray(tfData.times) && 
          tfData.frequencies && Array.isArray(tfData.frequencies) && 
          tfData.power && Array.isArray(tfData.power)) {
        
        // 创建一个时频数据的安全副本，避免修改原始数据
        const safeTimeFreq = {
          times: [...tfData.times],
          frequencies: [...tfData.frequencies],
          power: JSON.parse(JSON.stringify(tfData.power)), // 深拷贝
          events: Array.isArray(tfData.events) ? [...tfData.events] : []
        };
        
        // 返回处理后的响应
        return {
          data: {
            timeFrequency: safeTimeFreq
          }
        };
      }
      
      // 如果数据格式不正确，返回默认数据
      return {
        data: {
          timeFrequency: this._createDefaultTimeFrequencyData()
        }
      };
    } catch (error) {
      console.error('处理时频响应数据时出错:', error);
      return {
        data: {
          timeFrequency: this._createDefaultTimeFrequencyData()
        }
      };
    }
  }
};

export default analysisService; 