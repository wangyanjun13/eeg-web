<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/AppLayout.vue';
import EEGViewer from '@/components/EEGViewer.vue';

const route = useRoute();
const router = useRouter();
const datasetId = route.params.datasetId;
const subjectId = route.params.subjectId;

const subjectInfo = ref(null);
const eegData = ref(null);
const loading = ref({
  info: false,
  data: false
});

// 时间范围和选中的通道
const timeRange = ref([0, 10]);
const selectedChannels = ref([]);

// 获取受试者信息
const fetchSubjectInfo = async () => {
  loading.value.info = true;
  try {
    const response = await datasetService.getSubjectInfo(datasetId, subjectId);
    subjectInfo.value = response.data;
  } catch (error) {
    console.error('获取受试者信息失败:', error);
    ElMessage.error('获取受试者信息失败');
  } finally {
    loading.value.info = false;
  }
};

// 获取EEG数据
const fetchEEGData = async () => {
  loading.value.data = true;
  try {
    const response = await datasetService.getSubjectData(datasetId, subjectId, {
      start_time: timeRange.value[0],
      duration: timeRange.value[1] - timeRange.value[0]
    });
    eegData.value = response.data;
    
    // 初始化选中的通道（默认选择前5个）
    if (eegData.value && eegData.value.channels) {
      selectedChannels.value = eegData.value.channels.slice(0, 5);
    }
  } catch (error) {
    console.error('获取EEG数据失败:', error);
    ElMessage.error('获取EEG数据失败');
  } finally {
    loading.value.data = false;
  }
};

// 更新时间范围
const updateTimeRange = (newRange) => {
  timeRange.value = newRange;
  fetchEEGData();
};

// 更新选中的通道
const updateSelectedChannels = (channels) => {
  selectedChannels.value = channels;
};

// 计算通道选择器的选项
const channelOptions = computed(() => {
  if (!eegData.value || !eegData.value.channels) return [];
  return eegData.value.channels.map(channel => ({
    label: channel,
    value: channel
  }));
});

onMounted(() => {
  fetchSubjectInfo();
  fetchEEGData();
});
</script>

<template>
  <AppLayout>
    <div class="subject-detail-container">
      <!-- 返回按钮 -->
      <div class="back-button">
        <el-button @click="router.push(`/datasets/${datasetId}`)" icon="ArrowLeft">
          返回数据集
        </el-button>
      </div>

      <!-- 受试者基本信息 -->
      <el-card v-loading="loading.info" class="subject-info-card">
        <template #header>
          <div class="card-header">
            <h2 v-if="subjectInfo">受试者: {{ subjectInfo.subject }}</h2>
            <el-skeleton v-else :rows="1" animated />
          </div>
        </template>

        <div v-if="subjectInfo" class="subject-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="ID">{{ subjectInfo.id }}</el-descriptions-item>
            <el-descriptions-item label="文件名">{{ subjectInfo.name }}</el-descriptions-item>
            <el-descriptions-item label="格式">{{ subjectInfo.format }}</el-descriptions-item>
            <el-descriptions-item label="数据集">{{ subjectInfo.dataset_id }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <el-skeleton v-else :rows="4" animated />
      </el-card>

      <!-- EEG数据可视化 -->
      <el-card class="eeg-data-card">
        <template #header>
          <div class="card-header">
            <h3>EEG数据可视化</h3>
            <div class="data-controls">
              <el-select
                v-model="selectedChannels"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="选择通道"
                style="width: 240px"
                :loading="loading.data"
              >
                <el-option
                  v-for="option in channelOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
              
              <el-slider
                v-model="timeRange"
                range
                :min="0"
                :max="eegData ? eegData.duration : 10"
                :step="0.1"
                style="width: 300px; margin-left: 16px"
                @change="updateTimeRange"
              />
            </div>
          </div>
        </template>

        <div v-loading="loading.data">
          <EEGViewer
            v-if="eegData"
            :data="eegData"
            :time-range="timeRange"
            :selected-channels="selectedChannels"
            @update:time-range="updateTimeRange"
            @update:selected-channels="updateSelectedChannels"
          />
          <el-empty v-else-if="!loading.data" description="暂无EEG数据" />
        </div>
      </el-card>

      <!-- 分析按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="router.push(`/datasets/${datasetId}/subjects/${subjectId}/analyze`)">
          分析数据
        </el-button>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.subject-detail-container {
  padding: 20px;
}

.back-button {
  margin-bottom: 20px;
}

.subject-info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2, .card-header h3 {
  margin: 0;
}

.data-controls {
  display: flex;
  align-items: center;
}

.eeg-data-card {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style> 