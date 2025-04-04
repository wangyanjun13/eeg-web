<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useAnalysis } from '@/composables/useAnalysis';
import { useFormState } from '@/composables/useFormState';
import datasetService from '@/services/dataset';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';
import AppLayout from '@/components/layout/AppLayout.vue';

const route = useRoute();
const datasetId = computed(() => route.params.datasetId);
const subjectId = computed(() => route.params.subjectId);

// 使用分析钩子
const { isLoading, results, error, preprocessParams, loadPreprocessTemplate, runAnalysis } = useAnalysis();

// 预处理模板
const templateOptions = ref([
  { value: 'default', label: '默认设置', description: '适用于大多数EEG数据' },
  { value: 'minimal', label: '最小处理', description: '仅应用基本滤波和重参考' },
  { value: 'ds002218', label: 'DS002218设置', description: '适用于听觉/视觉节奏省略范式' }
]);

// 当前选择的模板
const selectedTemplate = ref('default');

// 表单状态
const { formState, resetForm } = useFormState('preprocess-form', {
  filter: {
    highpass_filter: true,
    highpass: 1.0,
    lowpass_filter: true,
    lowpass: 40.0,
    notch_filter: false,
    notch_freq: 50.0,
    notch_width: 5.0
  },
  resampling: {
    enabled: false,
    sfreq: 250
  },
  reference: {
    method: 'average',
    custom_ref: []
  },
  ica: {
    enabled: false,
    n_components: 20,
    method: 'fastica'
  },
  bad_channels: {
    detect: true,
    interpolate: true,
    threshold: 0.8
  }
});

// 原始数据和处理后数据
const rawData = ref(null);
const processedData = ref(null);
const selectedChannels = ref([]);
const timeRange = ref([0, 10]);

// 加载原始数据
const loadRawData = async () => {
  try {
    const response = await datasetService.getSubjectData(datasetId.value, subjectId.value, timeRange.value[0], timeRange.value[1] - timeRange.value[0]);
    rawData.value = response.data;
    
    // 默认选择前5个通道
    if (rawData.value && rawData.value.channels) {
      selectedChannels.value = rawData.value.channels.slice(0, 5);
    }
  } catch (error) {
    ElMessage.error('加载原始数据失败');
    console.error(error);
  }
};

// 加载预处理模板
const loadTemplate = async () => {
  try {
    const template = await loadPreprocessTemplate(selectedTemplate.value);
    Object.assign(formState, template);
  } catch (error) {
    ElMessage.error('加载预处理模板失败');
  }
};

// 应用预处理
const applyPreprocessing = async () => {
  try {
    await runAnalysis('preprocess', datasetId.value, subjectId.value, formState);
    processedData.value = results.value;
    ElMessage.success('预处理完成');
  } catch (error) {
    ElMessage.error('预处理失败');
  }
};

// 重置表单
const handleReset = () => {
  resetForm();
  processedData.value = null;
};

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}

// 组件挂载时加载数据和模板
onMounted(() => {
  loadRawData();
  loadTemplate();
});
</script>

<template>
  <AppLayout>
    <div class="preprocessing-container">
      <!-- 添加分析工作流导航 -->
      <AnalysisWorkflow 
        ref="workflowRef"
        current-step="preprocessing" 
        :dataset-id="datasetId" 
        :subject-id="subjectId" 
      />
      
      <!-- 被试信息卡片 -->
      <SubjectInfoCard :datasetId="datasetId" :subjectId="subjectId" />
      
      <!-- 预处理模板选择 -->
      <el-card class="template-card">
        <template #header>
          <div class="card-header">
            <h3>预处理设置</h3>
          </div>
        </template>
        
        <el-form-item label="预处理模板">
          <el-select v-model="selectedTemplate" @change="loadTemplate" style="width: 100%">
            <el-option
              v-for="item in templateOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
              <div class="template-option">
                <span>{{ item.label }}</span>
                <small>{{ item.description }}</small>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-card>
      
      <!-- 预处理参数表单 -->
      <el-form :model="formState" label-width="120px">
        <el-collapse>
          <!-- 滤波参数 -->
          <el-collapse-item title="滤波参数" name="filter">
            <el-form-item label="高通滤波">
              <el-switch v-model="formState.filter.highpass_filter" />
            </el-form-item>
            <el-form-item v-if="formState.filter.highpass_filter" label="高通频率">
              <el-input-number 
                v-model="formState.filter.highpass" 
                :min="0.1" 
                :max="10"
                :step="0.1"
              />
              <span>Hz</span>
            </el-form-item>
            
            <el-form-item label="低通滤波">
              <el-switch v-model="formState.filter.lowpass_filter" />
            </el-form-item>
            <el-form-item v-if="formState.filter.lowpass_filter" label="低通频率">
              <el-input-number 
                v-model="formState.filter.lowpass" 
                :min="1" 
                :max="100"
                :step="1"
              />
              <span>Hz</span>
            </el-form-item>
            
            <el-form-item label="陷波滤波">
              <el-switch v-model="formState.filter.notch_filter" />
            </el-form-item>
            <template v-if="formState.filter.notch_filter">
              <el-form-item label="陷波频率">
                <el-input-number 
                  v-model="formState.filter.notch_freq" 
                  :min="1" 
                  :max="100"
                  :step="1"
                />
                <span>Hz</span>
              </el-form-item>
              <el-form-item label="陷波宽度">
                <el-input-number 
                  v-model="formState.filter.notch_width" 
                  :min="0.1" 
                  :max="10"
                  :step="0.1"
                />
                <span>Hz</span>
              </el-form-item>
            </template>
          </el-collapse-item>
          
          <!-- 重采样参数 -->
          <el-collapse-item title="重采样参数" name="resampling">
            <el-form-item label="启用重采样">
              <el-switch v-model="formState.resampling.enabled" />
            </el-form-item>
            <el-form-item v-if="formState.resampling.enabled" label="目标采样率">
              <el-input-number 
                v-model="formState.resampling.sfreq" 
                :min="100" 
                :max="1000"
                :step="50"
              />
              <span>Hz</span>
            </el-form-item>
          </el-collapse-item>
          
          <!-- 重参考参数 -->
          <el-collapse-item title="重参考参数" name="reference">
            <el-form-item label="参考方法">
              <el-select v-model="formState.reference.method">
                <el-option label="平均参考" value="average" />
                <el-option label="双耳参考" value="mastoids" />
                <el-option label="自定义参考" value="custom" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="formState.reference.method === 'custom'" label="自定义参考通道">
              <el-select 
                v-model="formState.reference.custom_ref" 
                multiple 
                placeholder="选择参考通道"
              >
                <el-option 
                  v-for="channel in rawData?.channels" 
                  :key="channel" 
                  :label="channel" 
                  :value="channel" 
                />
              </el-select>
            </el-form-item>
          </el-collapse-item>
          
          <!-- ICA参数 -->
          <el-collapse-item title="ICA参数" name="ica">
            <el-form-item label="启用ICA">
              <el-switch v-model="formState.ica.enabled" />
            </el-form-item>
            <template v-if="formState.ica.enabled">
              <el-form-item label="组件数量">
                <el-input-number 
                  v-model="formState.ica.n_components" 
                  :min="5" 
                  :max="50"
                  :step="1"
                />
              </el-form-item>
              <el-form-item label="ICA方法">
                <el-select v-model="formState.ica.method">
                  <el-option label="FastICA" value="fastica" />
                  <el-option label="Extended Infomax" value="infomax" />
                  <el-option label="Picard" value="picard" />
                </el-select>
              </el-form-item>
            </template>
          </el-collapse-item>
          
          <!-- 坏通道处理 -->
          <el-collapse-item title="坏通道处理" name="bad_channels">
            <el-form-item label="检测坏通道">
              <el-switch v-model="formState.bad_channels.detect" />
            </el-form-item>
            <el-form-item label="插值坏通道">
              <el-switch v-model="formState.bad_channels.interpolate" />
            </el-form-item>
            <el-form-item label="检测阈值">
              <el-slider 
                v-model="formState.bad_channels.threshold" 
                :min="0.5" 
                :max="0.95" 
                :step="0.05"
                show-stops
              />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
        
        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button @click="handleReset">重置</el-button>
          <el-button type="primary" @click="applyPreprocessing" :loading="isLoading">应用预处理</el-button>
          <el-button type="success" @click="goToNextStep">下一步</el-button>
        </div>
      </el-form>
      
      <!-- 处理结果 -->
      <el-card v-if="processedData" class="process-result">
        <template #header>
          <div class="card-header">
            <h3>预处理结果</h3>
          </div>
        </template>
        
        <EEGViewer 
          :data="processedData" 
          :timeRange="timeRange"
          :selectedChannels="selectedChannels"
        />
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.preprocessing-container {
  padding: 20px;
  padding-bottom: 60px;
}

.subject-info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.template-card {
  margin-bottom: 20px;
}

.template-option {
  display: flex;
  flex-direction: column;
}

.template-option small {
  color: #909399;
  font-size: 12px;
}

.action-buttons {
  margin-top: 20px;
  text-align: center;
}

.process-result {
  margin-top: 30px;
}
</style> 