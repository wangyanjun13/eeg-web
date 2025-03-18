import { ref } from 'vue'
import datasetService from '@/services/dataset'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function useEEGData() {
  const datasets = ref([])
  const currentDataset = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // 获取数据集列表
  const fetchDatasets = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const data = await datasetService.getDatasets(params)
      datasets.value = data.items || []
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取单个数据集详情
  const fetchDatasetById = async (id) => {
    loading.value = true
    error.value = null
    try {
      const data = await datasetService.getDatasetById(id)
      currentDataset.value = data
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取EEG数据
  const fetchEEGData = async (datasetId, params = {}) => {
    loading.value = true
    error.value = null
    try {
      const data = await datasetService.getEEGData(datasetId, params)
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 预处理EEG数据
  const preprocessEEGData = async (datasetId, params) => {
    loading.value = true
    error.value = null
    try {
      const data = await datasetService.preprocessEEGData(datasetId, params)
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 分析EEG数据
  const analyzeEEGData = async (datasetId, params) => {
    loading.value = true
    error.value = null
    try {
      const data = await datasetService.analyzeEEGData(datasetId, params)
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    datasets,
    currentDataset,
    loading,
    error,
    fetchDatasets,
    fetchDatasetById,
    fetchEEGData,
    preprocessEEGData,
    analyzeEEGData
  }
} 