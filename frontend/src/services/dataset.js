import api from './api';

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
  }
};

export default datasetService;