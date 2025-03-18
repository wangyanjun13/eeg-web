import api from './api';

export const datasetService = {
  // 获取数据集列表
  getDatasets(params) {
    return api.get('/api/datasets', { params });
  },

  // 获取单个数据集详情
  getDatasetById(id) {
    return api.get(`/api/datasets/${id}`);
  },

  // 获取数据集中的所有受试者
  getDatasetSubjects(datasetId) {
    return api.get(`/api/datasets/${datasetId}/subjects`);
  },

  // 获取受试者详细信息
  getSubjectInfo(datasetId, subjectId) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/info`);
  },

  // 获取受试者原始EEG数据
  getSubjectData(datasetId, subjectId, params) {
    return api.get(`/api/datasets/${datasetId}/subjects/${subjectId}/raw`, { params });
  },

  // 获取数据集参与者信息
  getParticipantsInfo(datasetId) {
    return api.get(`/api/datasets/${datasetId}/participants`);
  },

  // 获取EEG数据
  getEEGData(datasetId, params) {
    return api.get(`/api/datasets/${datasetId}/data`, { params });
  },

  // 预处理EEG数据
  preprocessEEGData(datasetId, subjectId, params) {
    return api.post(`/api/preprocess/${datasetId}/subjects/${subjectId}`, params);
  },

  // 分析EEG数据
  analyzeEEGData(datasetId, subjectId, params) {
    return api.post(`/api/analysis/${datasetId}/subjects/${subjectId}`, params);
  },

  // 上传数据集
  uploadDataset(formData) {
    return api.post('/api/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 更新数据集信息
  updateDataset(id, data) {
    return api.put(`/api/datasets/${id}`, data);
  },

  // 删除数据集
  deleteDataset(id) {
    return api.delete(`/api/datasets/${id}`);
  }
};

export default datasetService; 