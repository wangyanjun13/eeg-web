<script setup>
import { ref, onMounted, computed, provide } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/layout/AppLayout.vue';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import { useLoading } from '@/composables/useLoading';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';

const route = useRoute();
const router = useRouter();
const datasetId = route.params.datasetId;
const subjectId = route.params.subjectId;

// 数据状态
const subjectInfo = ref(null);
const eegData = ref(null);
const { isLoading: loading, withLoading } = useLoading({
  info: false,
  data: false
});

// 时间范围和选中的通道
const timeRange = ref([0, 10]);
const selectedChannels = ref([]);

// 获取受试者信息
const fetchSubjectInfo = async () => {
  try {
    const response = await withLoading(
      datasetService.getSubjectInfo(datasetId, subjectId),
      'info'
    );
    subjectInfo.value = response.data;
    console.log('被试信息:', subjectInfo.value);
    
    // 如果有通道信息，默认选择前5个通道
    if (subjectInfo.value && subjectInfo.value.channels) {
      selectedChannels.value = subjectInfo.value.channels.slice(0, 5);
    }
  } catch (error) {
    console.error('获取被试信息失败:', error);
    ElMessage.error('获取被试信息失败');
  }
};

// 获取EEG数据
const fetchEEGData = async () => {
  try {
    const response = await withLoading(
      datasetService.getSubjectData(
        datasetId, 
        subjectId,
        timeRange.value[0],
        timeRange.value[1] - timeRange.value[0]
      ),
      'data'
    );
    eegData.value = response.data;
    console.log('EEG数据:', eegData.value);
  } catch (error) {
    console.error('获取EEG数据失败:', error);
    ElMessage.error('获取EEG数据失败');
  }
};

// 更新时间范围
const updateTimeRange = (newRange) => {
  timeRange.value = newRange;
  fetchEEGData(); // 获取新时间范围的数据
};

// 更新选中的通道
const updateSelectedChannels = (channels) => {
  selectedChannels.value = channels;
  fetchEEGData(); // 当通道选择变化时重新获取数据
};

// 页面加载时获取数据
onMounted(() => {
  fetchSubjectInfo();
  fetchEEGData();
});

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}
</script>

<template>
  <AppLayout>
    <div class="subject-detail-container">
      <!-- 添加分析工作流导航 -->
      <AnalysisWorkflow 
        ref="workflowRef"
        current-step="raw" 
        :dataset-id="datasetId" 
        :subject-id="subjectId" 
      />
      
      <!-- 被试信息卡片 -->
      <el-card v-loading="loading.info" class="subject-info-card">
        <template #header>
          <div class="card-header">
            <h2>被试信息</h2>
          </div>
        </template>

        <div v-if="subjectInfo">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="被试ID">{{ subjectInfo.subject_id }}</el-descriptions-item>
            <el-descriptions-item label="数据集">{{ subjectInfo.dataset_id }}</el-descriptions-item>
            <el-descriptions-item label="采样率">{{ subjectInfo.sampling_rate }} Hz</el-descriptions-item>
            <el-descriptions-item label="通道数">{{ subjectInfo.n_channels }}</el-descriptions-item>
            <el-descriptions-item label="时长">{{ subjectInfo.duration.toFixed(2) }} 秒</el-descriptions-item>
            <el-descriptions-item label="性别">{{ subjectInfo.Gender }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ subjectInfo.Age }}</el-descriptions-item>
            <el-descriptions-item label="惯用手">{{ subjectInfo.Handedness }}</el-descriptions-item>
            <el-descriptions-item label="教育水平">{{ subjectInfo.EDU_level }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>

      <!-- EEG数据卡片 -->
      <el-card v-loading="loading.data" class="eeg-data-card">
        <template #header>
          <div class="card-header">
            <h3>EEG原始时间序列可视化</h3>
            <div class="data-controls">
              <el-input-number 
                v-model="timeRange[0]" 
                :min="0" 
                :max="subjectInfo?.duration - 1" 
                :step="1"
                @change="updateTimeRange(timeRange)"
                style="width: 120px; margin-right: 10px;"
              />
              <span>至</span>
              <el-input-number 
                v-model="timeRange[1]" 
                :min="timeRange[0] + 1" 
                :max="subjectInfo?.duration" 
                :step="1"
                @change="updateTimeRange(timeRange)"
                style="width: 120px; margin-left: 10px;"
              />
              <span style="margin-left: 5px;">秒</span>
            </div>
          </div>
        </template>

        <div v-if="eegData" class="eeg-viewer-container">
          <EEGViewer 
            :data="eegData" 
            v-model:timeRange="timeRange"
            v-model:selectedChannels="selectedChannels"
            @update:timeRange="updateTimeRange"
            @update:selectedChannels="updateSelectedChannels"
          />
          <!-- 下一步按钮放到图表右下角 -->
          <div class="next-step-button">
            <el-button type="success" size="default" plain @click="goToNextStep">
              <el-icon><ArrowRight /></el-icon> 开始预处理流程
            </el-button>
          </div>
        </div>
        <el-empty v-else-if="!loading.data" description="暂无EEG数据" />
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.subject-detail-container {
  padding: 8px 16px;
  max-width: 1600px;
  margin: 0 auto;
}

.subject-info-card {
  margin-bottom: 16px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2, .card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.data-controls {
  display: flex;
  align-items: center;
}

.eeg-data-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.eeg-viewer-container {
  position: relative;
  min-height: 400px;
  margin-bottom: 50px;
}

.next-step-button {
  position: absolute;
  bottom: -40px;
  right: 20px;
  z-index: 10;
  opacity: 0.9;
}

.next-step-button .el-button {
  font-size: 14px;
  padding: 8px 15px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .subject-detail-container {
    padding: 8px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .data-controls {
    margin-top: 10px;
    width: 100%;
    justify-content: space-between;
  }
}
</style> 