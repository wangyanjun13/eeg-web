<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const datasets = ref([])
const dialogVisible = ref(false)
const currentDatasetInfo = ref(null)
const loading = ref(false)
const error = ref('')
const infoDialogVisible = ref(false)
const eegDialogVisible = ref(false)
const currentEEGData = ref(null)
const timeRange = ref([0, 10])
const selectedChannels = ref([])
const eegChart = ref(null)
let chartInstance = null

const fetchDatasets = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('http://localhost:8000/api/datasets/')
    datasets.value = response.data.data
    if (response.data.error) {
      error.value = response.data.error
    }
  } catch (err) {
    console.error('Error fetching datasets:', err)
    error.value = '获取数据集失败：' + (err.response?.data?.detail || err.message)
  } finally {
    loading.value = false
  }
}

const showInfo = async (dataset) => {
  try {
    const response = await axios.get(`http://localhost:8000/api/datasets/${dataset.id}/info/`)
    currentDatasetInfo.value = response.data.data
    infoDialogVisible.value = true
  } catch (err) {
    console.error('Error fetching dataset info:', err)
    ElMessage.error('获取数据集信息失败')
  }
}

const showEEG = async (dataset) => {
  try {
    loading.value = true
    const response = await axios.get(
      `http://localhost:8000/api/datasets/${dataset.id}/raw/`,
      {
        params: {
          start_time: timeRange.value[0],
          duration: timeRange.value[1] - timeRange.value[0]
        }
      }
    )
    currentEEGData.value = response.data.data
    selectedChannels.value = response.data.data.channels.slice(0, 5)
    eegDialogVisible.value = true
    await nextTick()
    initEEGChart()
    updateEEGDisplay()
  } catch (error) {
    ElMessage.error('获取EEG数据失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const initEEGChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(eegChart.value)
}

const updateEEGDisplay = () => {
  if (!chartInstance || !currentEEGData.value) return

  const option = {
    title: {
      text: 'EEG数据可视化'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: selectedChannels.value
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '时间 (s)'
    },
    yAxis: {
      type: 'value',
      name: '振幅'
    },
    series: selectedChannels.value.map(channel => ({
      name: channel,
      type: 'line',
      data: currentEEGData.value.data[channel]
    }))
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  fetchDatasets()
})
</script>

<template>
  <div class="container">
    <el-container>
      <el-header class="header">
        <h1>EEG数据分析展示交互平台</h1>
      </el-header>
      
      <el-main>
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          style="margin-bottom: 20px;"
        />
        
        <el-card class="data-table">
          <el-table 
            v-loading="loading"
            :data="datasets" 
            style="width: 100%"
            :default-sort="{ prop: 'id', order: 'ascending' }"
            border
          >
            <el-table-column prop="id" label="受试者ID" width="120" sortable />
            <el-table-column prop="subject" label="受试者编号" width="120" />
            <el-table-column prop="name" label="数据文件" min-width="200" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button-group>
                  <el-button 
                    @click="showInfo(scope.row)" 
                    size="small"
                    type="info"
                  >
                    查看信息
                  </el-button>
                  <el-button 
                    @click="showEEG(scope.row)" 
                    size="small" 
                    type="primary"
                  >
                    查看EEG
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 数据集信息对话框 -->
        <el-dialog 
          v-model="infoDialogVisible" 
          title="数据集信息" 
          width="50%"
          destroy-on-close
        >
          <div v-if="currentDatasetInfo" class="dataset-info">
            <el-descriptions border>
              <el-descriptions-item label="受试者ID">
                {{ currentDatasetInfo.subject_id }}
              </el-descriptions-item>
              <el-descriptions-item label="采样率">
                {{ currentDatasetInfo.sampling_rate }} Hz
              </el-descriptions-item>
              <el-descriptions-item label="持续时间">
                {{ currentDatasetInfo.duration.toFixed(2) }} 秒
              </el-descriptions-item>
              <el-descriptions-item label="通道数">
                {{ currentDatasetInfo.n_channels }}
              </el-descriptions-item>
            </el-descriptions>
            <div class="channel-list">
              <h3>通道列表：</h3>
              <div class="channel-tags">
                <el-tag 
                  v-for="channel in currentDatasetInfo.channels" 
                  :key="channel"
                  class="channel-tag"
                  size="small"
                >
                  {{ channel }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-dialog>

        <!-- EEG数据可视化对话框 -->
        <el-dialog 
          v-model="eegDialogVisible" 
          title="EEG数据可视化" 
          fullscreen
          destroy-on-close
        >
          <div v-if="currentEEGData" class="eeg-container">
            <div class="eeg-controls">
              <el-form :inline="true" class="control-form">
                <el-form-item label="时间范围">
                  <el-slider
                    v-model="timeRange"
                    :min="0"
                    :max="currentEEGData.duration"
                    :step="1"
                    range
                    @change="updateEEGDisplay"
                    style="width: 300px"
                  />
                </el-form-item>
                <el-form-item label="显示通道">
                  <el-select
                    v-model="selectedChannels"
                    multiple
                    placeholder="选择要显示的通道"
                    @change="updateEEGDisplay"
                    style="width: 400px"
                  >
                    <el-option
                      v-for="channel in currentEEGData.channels"
                      :key="channel"
                      :label="channel"
                      :value="channel"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>
            <div ref="eegChart" class="eeg-chart"></div>
          </div>
        </el-dialog>
      </el-main>
    </el-container>
  </div>
</template>

<style scoped>
.container {
  width: 100%;
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
  box-sizing: border-box;
}

.header {
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  border-radius: 4px;
}

.header h1 {
  margin: 0;
  line-height: 60px;
  font-size: 24px;
  color: #303133;
}

.data-table {
  margin-bottom: 20px;
}

.dataset-info {
  padding: 20px;
}

.channel-list {
  margin-top: 20px;
}

.channel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.channel-tag {
  margin: 0;
}

.eeg-container {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: white;
}

.eeg-controls {
  background-color: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.control-form {
  display: flex;
  align-items: center;
  gap: 20px;
}

.eeg-chart {
  flex: 1;
  min-height: 500px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

:deep(.el-dialog__body) {
  padding: 0;
}
</style>
