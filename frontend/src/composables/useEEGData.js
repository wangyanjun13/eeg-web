import { ref } from 'vue'
import axios from 'axios'

export function useEEGData() {
  const datasets = ref([])
  const currentData = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchDatasets() {
    loading.value = true
    try {
      const response = await axios.get('http://localhost:8000/api/datasets')
      datasets.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchEEGData(datasetId) {
    loading.value = true
    try {
      const response = await axios.get(`http://localhost:8000/api/datasets/${datasetId}/eeg`)
      currentData.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    datasets,
    currentData,
    loading,
    error,
    fetchDatasets,
    fetchEEGData
  }
} 