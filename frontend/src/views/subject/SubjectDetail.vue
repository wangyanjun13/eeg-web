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
    console.log('受试者信息:', subjectInfo.value);
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

// 格式化时长
const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}分${remainingSeconds}秒`;
};

// 格式化标签名称
const formatLabel = (key) => {
  // 将snake_case转换为更友好的显示格式
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// 计算额外的人口统计学信息（排除已显示的基本字段）
const additionalInfo = computed(() => {
  if (!subjectInfo.value) return {};
  
  const basicFields = ['subject_id', 'dataset_id', 'n_channels', 'sampling_rate', 
                       'duration', 'channels', 'age', 'sex'];
  
  return Object.fromEntries(
    Object.entries(subjectInfo.value)
      .filter(([key]) => !basicFields.includes(key))
  );
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
            <h2 v-if="subjectInfo">受试者: {{ subjectInfo.subject_id }}</h2>
            <el-skeleton v-else :rows="1" animated />
          </div>
        </template>

        <div v-if="subjectInfo" class="subject-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="数据集">{{ subjectInfo.dataset_id }}</el-descriptions-item>
            <el-descriptions-item label="通道数">{{ subjectInfo.n_channels }}</el-descriptions-item>
            <el-descriptions-item label="采样率">{{ subjectInfo.sampling_rate }} Hz</el-descriptions-item>
            <el-descriptions-item label="时长">{{ formatDuration(subjectInfo.duration) }}</el-descriptions-item>
            
            <!-- 添加人口统计学信息（如果有） -->
            <el-descriptions-item v-if="subjectInfo.age" label="年龄">{{ subjectInfo.age }}</el-descriptions-item>
            <el-descriptions-item v-if="subjectInfo.sex" label="性别">
              {{ subjectInfo.sex === 'M' ? '男' : subjectInfo.sex === 'F' ? '女' : subjectInfo.sex }}
            </el-descriptions-item>
            
            <!-- 显示其他可能的人口统计学信息 -->
            <template v-for="(value, key) in additionalInfo" :key="key">
              <el-descriptions-item :label="formatLabel(key)">{{ value }}</el-descriptions-item>
            </template>
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