import api from './api';
import axios from 'axios';

// 创建一个取消令牌源
const CancelToken = axios.CancelToken;
let uploadCancelSource = null;

// 上传配置
const UPLOAD_CHUNK_SIZE = 2 * 1024 * 1024; // 2MB 默认块大小
const MAX_RETRY_COUNT = 3; // 最大重试次数
const RETRY_DELAY = 3000; // 重试延迟(ms)

// 封装与数据集相关的API请求

export const datasetService = {
  // 获取数据集列表
  getDatasets(params = {}) {
    const queryParams = new URLSearchParams();
    
    // 添加关键词搜索参数
    if (params.keyword) {
      queryParams.append('keyword', params.keyword);
    }
    
    // 添加其他筛选参数
    if (params.tags && params.tags.length > 0) {
      queryParams.append('tags', params.tags.join(','));
    }
    
    if (params.dateRange && params.dateRange.length === 2) {
      queryParams.append('start_date', params.dateRange[0]);
      queryParams.append('end_date', params.dateRange[1]);
    }
    
    if (params.sortBy) {
      queryParams.append('sort_by', params.sortBy);
      queryParams.append('sort_order', params.sortOrder || 'desc');
    }
    
    const queryString = queryParams.toString();
    return api.get(`/api/datasets${queryString ? '?' + queryString : ''}`);
  },

  // 获取单个数据集详情
  getDatasetById(id) {
    return api.get(`/api/datasets/${id}`);
  },
  
  // 获取数据集中的受试者列表
  getDatasetSubjects(datasetId) {
    return api.get(`/api/datasets/${datasetId}/subjects`);
  },
  
  // 获取受试者详细信息
  getSubjectInfo(datasetId, subjectId) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/info`);
  },
  
  // 获取受试者原始EEG数据
  getSubjectData(datasetId, subjectId, startTime = 0, duration = 10) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/raw`, {
      params: {
        start_time: startTime,
        duration: duration
      }
    });
  },
  
  // 获取事件信息
  getEvents(datasetId, subjectId) {
    console.log(`获取事件信息: datasetId=${datasetId}, subjectId=${subjectId}`);
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/events`);
  },
  
  // 获取参与者信息
  getParticipantsInfo(datasetId) {
    return api.get(`/api/datasets/${datasetId}/participants`);
  },

  // 获取电极位置信息
  getElectrodePositions(datasetId, subjectId) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/electrodes`);
  },

  // 导出受试者原始数据
  exportSubjectData(datasetId, subjectId) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/export`, {
      responseType: 'blob'
    });
  },

  // 记录网站访问
  recordVisit() {
    return api.post('/api/datasets/record-visit');
  },
  
  // 获取网站访问量
  getVisitCount() {
    return api.get('/api/datasets/visit-count');
  },

  // 上传数据集
  uploadDataset(formData) {
    return api.post('/api/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 获取所有上传文件
  getUploadedFiles(fileType) {
    let params = {};
    if (fileType) {
      params.file_type = fileType;
    }
    return api.get('/api/upload/files', { params });
  },

  // 获取特定上传文件详情
  getUploadedFile(fileId) {
    return api.get(`/api/upload/files/${fileId}`);
  },

  // 删除上传文件
  deleteUploadedFile(fileId) {
    return api.delete(`/api/upload/files/${fileId}`);
  },

  // 获取我的文件列表
  getMyFiles: async () => {
    try {
      // 添加随机参数，避免缓存问题
      const timestamp = new Date().getTime();
      // api.js的响应拦截器已经返回了response.data，所以这里直接使用
      const response = await api.get(`/api/upload/files?_t=${timestamp}`);
      console.log('获取我的文件列表API响应:', response);
      return response;
    } catch (error) {
      console.error('获取我的文件列表失败:', error);
      // 出错时返回统一格式，方便前端处理
      return { status: 'error', files: [], message: error.message };
    }
  },

  // 上传文件（数据文件或模型文件）
  uploadDataset: async (formData, onProgress) => {
    // 如果有之前的上传请求，取消它
    if (uploadCancelSource) {
      try {
        uploadCancelSource.cancel('新的上传请求开始，取消之前的请求');
      } catch (e) {
        console.error('取消上一个请求失败:', e);
      }
      uploadCancelSource = null;
    }
    
    // 获取文件对象
    const fileEntry = formData.get('file');
    if (!fileEntry) {
      throw new Error('未找到文件');
    }
    
    // 文件大小和分块计算
    const fileSize = fileEntry.size;
    const fileName = fileEntry.name;
    
    // 根据文件大小动态调整块大小
    let chunkSize = UPLOAD_CHUNK_SIZE;
    if (fileSize > 100 * 1024 * 1024) { // 大于100MB
      chunkSize = 1 * 1024 * 1024; // 1MB - 降低块大小，避免HTTP/2协议错误
    } else if (fileSize > 50 * 1024 * 1024) { // 大于50MB
      chunkSize = 1.5 * 1024 * 1024; // 1.5MB - 使用更小的块大小
    } else if (fileSize > 10 * 1024 * 1024) { // 大于10MB
      chunkSize = 2 * 1024 * 1024; // 2MB - 使用默认块大小
    } else {
      chunkSize = 4 * 1024 * 1024; // 4MB - 对于小文件使用更大的块大小
    }
    
    console.log(`文件大小: ${(fileSize / (1024 * 1024)).toFixed(2)} MB, 使用块大小: ${(chunkSize / (1024 * 1024)).toFixed(2)} MB`);
    
    // 创建新的取消令牌
    uploadCancelSource = CancelToken.source();
    
    // 设置超时时间 - 根据文件大小动态调整
    const baseTimeout = 15 * 60 * 1000; // 基础15分钟
    const timeoutPerMB = 2000; // 每MB增加2秒
    const timeout = baseTimeout + (fileSize / (1024 * 1024)) * timeoutPerMB;
    
    try {
      // 添加重试逻辑
      let retryCount = 0;
      let lastError = null;
      
      while (retryCount <= MAX_RETRY_COUNT) {
        try {
          if (retryCount > 0) {
            console.log(`尝试第 ${retryCount} 次重试上传...`);
            // 在重试之间添加延迟
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
          }
          
          // 使用标准的axios请求进行上传
          const response = await axios.post(
            `${api.defaults.baseURL}/api/upload/file`, 
            formData, 
            {
              headers: {
                'Content-Type': 'multipart/form-data',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                // 强制使用 HTTP/1.1
                'X-Prefer-Http-Version': 'HTTP/1.1',
                // 添加浏览器标识，帮助服务器识别连接类型
                'X-Client-Browser': navigator.userAgent
              },
              timeout: timeout,
              cancelToken: uploadCancelSource.token,
              onUploadProgress: (progressEvent) => {
                if (progressEvent.total) {
                  const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                  if (onProgress) {
                    onProgress(percentCompleted);
                  }
                }
              },
              // 尝试使用更小的块大小和更长的超时时间
              maxBodyLength: Infinity,
              maxContentLength: Infinity,
              // 强制使用 XMLHttpRequest 而不是 fetch API
              // 这有助于避免某些浏览器中的 HTTP/2 问题
              transport: {
                request: function createRequest(options) {
                  return new XMLHttpRequest();
                }
              }
            }
          );
          
          return response.data;
        } catch (error) {
          lastError = error;
          
          // 特别处理 HTTP/2 协议错误
          if (error.message && (
            error.message.includes('HTTP/2') || 
            error.message.includes('PROTOCOL_ERROR') ||
            error.message.includes('ERR_HTTP2_')
          )) {
            console.error('检测到 HTTP/2 协议错误，将在重试时尝试使用 HTTP/1.1');
            retryCount++;
            
            // 如果是最后一次重试，则抛出错误
            if (retryCount > MAX_RETRY_COUNT) {
              console.error(`上传失败，已达到最大重试次数 (${MAX_RETRY_COUNT})`, error);
              throw new Error('文件上传失败：HTTP/2 协议错误。请尝试减小文件大小或使用其他浏览器。');
            }
            
            continue;
          }
          
          // 处理网络错误
          if (error.message && (
            error.message.includes('network') || 
            error.message.includes('timeout') ||
            error.message.includes('Network Error')
          )) {
            console.warn(`遇到网络错误，准备重试: ${error.message}`);
            retryCount++;
            
            // 如果是最后一次重试，则抛出错误
            if (retryCount > MAX_RETRY_COUNT) {
              console.error(`上传失败，已达到最大重试次数 (${MAX_RETRY_COUNT})`, error);
              throw new Error(`文件上传失败：网络错误 (${error.message})。请检查网络连接并重试。`);
            }
            
            continue;
          } else {
            // 不可重试的错误直接抛出
            throw error;
          }
        }
      }
      
      // 如果所有重试都失败
      throw lastError || new Error('上传失败，已达到最大重试次数');
    } catch (error) {
      // 如果错误是由于取消请求导致的，不做特殊处理
      if (axios.isCancel(error)) {
        console.log('上传请求被取消:', error.message);
        throw new Error('上传请求被取消');
      }
      
      console.error('上传文件失败:', error);
      
      // 检查是否是"Cannot read properties of undefined (reading 'source')"错误
      if (error.message && error.message.includes("Cannot read properties of undefined")) {
        console.error('检测到source未定义错误，这可能是由于取消令牌问题导致的');
        // 重置取消令牌
        uploadCancelSource = null;
        throw new Error('上传过程中发生内部错误，请重试');
      }
      
      // 检查是否是 HTTP/2 协议错误
      if (error.message && (
        error.message.includes('HTTP/2') || 
        error.message.includes('PROTOCOL_ERROR') ||
        error.message.includes('ERR_HTTP2_')
      )) {
        throw new Error('文件上传失败：HTTP/2 协议错误。请尝试减小文件大小或使用其他浏览器。');
      }
      
      // 其他错误处理
      throw error;
    } finally {
      // 清理取消令牌
      uploadCancelSource = null;
    }
  },

  // 取消当前上传
  cancelUpload: () => {
    if (uploadCancelSource) {
      try {
        uploadCancelSource.cancel('用户取消上传');
        uploadCancelSource = null;
        return true;
      } catch (e) {
        console.error('取消上传失败:', e);
        uploadCancelSource = null;
        return false;
      }
    }
    return false;
  },

  // 下载文件
  downloadFile: async (fileId) => {
    try {
      console.log(`开始下载文件 ID: ${fileId}`);
      
      // 创建一个a标签，直接使用href跳转到下载链接
      // 这样可以避免CORS问题，因为浏览器处理跨域下载而不是JavaScript
      const downloadUrl = `${api.defaults.baseURL}/api/upload/files/${fileId}/download`;
      console.log('下载链接:', downloadUrl);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.target = '_blank'; // 新窗口打开
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      return true;
    } catch (error) {
      console.error('下载文件失败:', error);
      throw error;
    }
  },

  // 删除文件
  deleteFile: async (fileId) => {
    try {
      const response = await api.delete(`/api/upload/files/${fileId}`);
      return response.data;
    } catch (error) {
      console.error('删除文件失败:', error);
      throw error;
    }
  },

  // 评测模型与数据匹配情况
  evaluateModel: async (dataFileId, modelFileId) => {
    try {
      console.log(`开始评测模型: 数据文件ID=${dataFileId}, 模型文件ID=${modelFileId}`);
      
      const formData = new FormData();
      formData.append('data_file_id', dataFileId);
      formData.append('model_file_id', modelFileId);
      
      // 增加额外的调试信息
      console.log('准备发送评测请求...');
      
      const response = await api.post('/api/upload/evaluate_model', formData, {
        timeout: 180000, // 延长超时时间到3分钟
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('收到响应:', response);
      
      // 改进的响应处理逻辑：如果response存在，直接返回数据，不要抛出错误
      if (response) {
        // 即使响应中包含错误信息，也返回完整响应数据
        console.log('处理响应数据:', response);
        return response;
      } else {
        // 只有在响应完全不存在时才抛出错误
        console.error('响应对象不存在');
        throw new Error('服务器无响应');
      }
    } catch (error) {
      console.error('评测模型失败:', error);
      
      // 构建标准化的错误响应对象
      let errorResponse = {
        status: 'error', // 确保始终有status字段
        message: '评测模型失败',
        error_type: 'unknown_error',
        details: {}
      };
      
      if (error.response) {
        console.log('服务器返回错误:', error.response);
        // 服务器返回的错误
        if (error.response.data && typeof error.response.data === 'object') {
          // 如果服务器已经返回了标准错误格式，直接使用
          if (error.response.data.status === 'error') {
            console.log('直接返回服务器的错误响应:', error.response.data);
            return error.response.data;
          }
          // 否则提取错误信息
          errorResponse.message = error.response.data.detail || error.response.data.message || '服务器处理请求时出错';
          errorResponse.details = error.response.data || {};
        } else {
          errorResponse.message = '服务器返回了非JSON格式的错误';
        }
        errorResponse.error_type = 'server_error';
      } else if (error.request) {
        console.log('请求发送但无响应:', error.request);
        // 请求发送但没有收到响应
        if (error.code === 'ECONNABORTED') {
          errorResponse.message = '模型评测超时，请尝试使用较小的数据文件或更简单的模型';
          errorResponse.error_type = 'timeout_error';
        } else {
          errorResponse.message = '无法连接到服务器，请检查网络连接';
          errorResponse.error_type = 'connection_error';
        }
      } else {
        console.log('请求设置错误:', error.message);
        // 请求设置出错
        errorResponse.message = error.message || '请求设置出错';
        errorResponse.error_type = 'request_error';
      }
      
      // 添加文件信息到错误详情中
      errorResponse.details.data_file_id = dataFileId;
      errorResponse.details.model_file_id = modelFileId;
      
      console.log('返回标准化错误响应:', errorResponse);
      
      // 直接返回错误响应对象，而不是抛出错误
      return errorResponse;
    }
  }
};

export default datasetService;