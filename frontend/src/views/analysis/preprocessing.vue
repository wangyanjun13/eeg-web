<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import TimeSeriesChart from '@/components/analysis/TimeSeriesChart.vue';
import datasetService from '@/services/dataset';
import analysisService from '@/services/analysisService';
import { useLoading } from '@/composables/useLoading';
import { useAnalysis } from '@/composables/useAnalysis';

const route = useRoute();
const router = useRouter();
const datasetId = route.params.datasetId || ''; 
const subjectId = route.params.subjectId || '';

// 页面状态
const activeTab = ref('filter');
const originalData = ref(null);
const processedData = ref(null);
const { isLoading, withLoading } = useLoading();
const compareMode = ref(false);
const selectedChannels = ref([]);
const timeRange = ref([0, 10]);
const workflowRef = ref(null);
const subjectInfo = ref(null);
const showParams = ref(true); // 控制参数面板的显示/隐藏

// 使用封装好的分析方法
const { preprocessParams, runAnalysis, loadPreprocessTemplate } = useAnalysis(datasetId, subjectId);

// 获取受试者信息
const fetchSubjectInfo = async () => {
  try {
    const response = await withLoading(
      datasetService.getSubjectInfo(datasetId, subjectId),
      'info'
    );
    subjectInfo.value = response.data;
    
    // 加载初始通道
    if (subjectInfo.value?.channels) {
      selectedChannels.value = subjectInfo.value.channels.slice(0, 5);
    }
  } catch (error) {
    console.error('获取被试信息失败:', error);
    ElMessage.error('获取被试信息失败');
  }
};

// 获取原始数据
const fetchOriginalData = async () => {
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
    originalData.value = response.data;
  } catch (error) {
    console.error('获取EEG数据失败:', error);
    ElMessage.error('获取EEG数据失败');
  }
};

// 应用过滤器
const applyFilter = async () => {
  try {
    // 参数验证
    if (preprocessParams.filter.highpass_filter && preprocessParams.filter.highpass <= 0) {
      ElMessage.warning('高通滤波频率必须大于0');
      return;
    }
    if (preprocessParams.filter.lowpass_filter && preprocessParams.filter.lowpass <= 0) {
      ElMessage.warning('低通滤波频率必须大于0');
      return;
    }
    if (preprocessParams.filter.notch_filter && (!preprocessParams.filter.line_freqs || preprocessParams.filter.line_freqs.length === 0)) {
      ElMessage.warning('启用陷波滤波时必须指定频率');
      return;
    }

    // 确保数据集ID和受试者ID有效
    if (!datasetId || !subjectId) {
      ElMessage.error('数据集ID或受试者ID无效');
      return;
    }

    console.log('应用滤波器，参数:', {
      highpass_filter: preprocessParams.filter.highpass_filter,
      highpass: preprocessParams.filter.highpass,
      lowpass_filter: preprocessParams.filter.lowpass_filter,
      lowpass: preprocessParams.filter.lowpass,
      notch_filter: preprocessParams.filter.notch_filter,
      line_freqs: preprocessParams.filter.line_freqs
    });

    const response = await withLoading(
      analysisService.applyFilter(datasetId, subjectId, {
        highpass_filter: preprocessParams.filter.highpass_filter,
        highpass: preprocessParams.filter.highpass,
        lowpass_filter: preprocessParams.filter.lowpass_filter,
        lowpass: preprocessParams.filter.lowpass,
        notch_filter: preprocessParams.filter.notch_filter,
        line_freqs: preprocessParams.filter.line_freqs
      }),
      'processing'
    );

    if (!response || !response.data) {
      throw new Error('服务器返回数据无效');
    }

    processedData.value = response.data;
    compareMode.value = true;
    ElMessage.success('滤波器应用成功');
  } catch (error) {
    console.error('应用滤波器失败:', error);
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`应用滤波器失败: ${errorMessage}`);
  }
};

// 运行ICA
const runICAProcess = async () => {
  try {
    const response = await withLoading(
      analysisService.runICA(datasetId, subjectId, preprocessParams.ica),
      'processing'
    );
    processedData.value = response.data;
    compareMode.value = true;
    ElMessage.success('ICA分析完成');
  } catch (error) {
    console.error('ICA分析失败:', error);
    ElMessage.error('ICA分析失败');
  }
};

// 去除伪迹
const removeArtifacts = async () => {
  try {
    const response = await withLoading(
      analysisService.removeArtifacts(datasetId, subjectId, preprocessParams.artifacts),
      'processing'
    );
    processedData.value = response.data;
    compareMode.value = true;
    ElMessage.success('伪迹去除完成');
  } catch (error) {
    console.error('伪迹去除失败:', error);
    ElMessage.error('伪迹去除失败');
  }
};

// 应用所有预处理
const applyAllProcessing = async () => {
  try {
    ElMessageBox.confirm(
      '确定要应用所有预处理步骤吗？这可能需要一些时间。',
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(async () => {
      const allParams = {
        filter: preprocessParams.filter,
        resample: preprocessParams.resample,
        reference: preprocessParams.reference,
        ica: preprocessParams.ica,
        bad_channels: preprocessParams.bad_channels,
        artifacts: preprocessParams.artifacts
      };
      
      const response = await withLoading(
        analysisService.preprocessData(datasetId, subjectId, allParams),
        'processing'
      );
      
      processedData.value = response.data;
      compareMode.value = true;
      ElMessage.success('所有预处理步骤应用成功');
    }).catch(() => {
      // 用户取消操作
    });
  } catch (error) {
    console.error('预处理失败:', error);
    ElMessage.error('预处理失败');
  }
};

// 预处理模板选项
const templateOptions = [
  { value: 'default', label: '默认预处理模板' },
  { value: 'minimal', label: '最小预处理模板' },
  { value: 'ds002218', label: 'DS002218 数据集专用模板' }
];
const selectedTemplate = ref('default');

// 加载预处理模板
const loadTemplate = async () => {
  try {
    await withLoading(
      loadPreprocessTemplate(selectedTemplate.value),
      'template'
    );
    ElMessage.success(`已加载${selectedTemplate.value}模板`);
  } catch (error) {
    console.error('加载模板失败:', error);
    ElMessage.error('加载模板失败');
  }
};

// 前往下一步
const goToNextStep = () => {
  if (workflowRef.value) {
    workflowRef.value.goToNextStep();
  }
};

// 更新时间范围
const updateTimeRange = (newRange) => {
  timeRange.value = newRange;
  fetchOriginalData();
  if (processedData.value) {
    // 如果有处理过的数据，也需要重新应用预处理
    // 这里可能需要重新应用预处理
  }
};

// 切换到对比模式
const toggleCompareMode = () => {
  compareMode.value = !compareMode.value;
  if (!compareMode.value) {
    processedData.value = null; // 清除处理后的数据
  }
};

// 切换参数面板显示/隐藏
const toggleParamsPanel = () => {
  showParams.value = !showParams.value;
};

// 在页面加载时获取数据
onMounted(() => {
  fetchSubjectInfo();
  fetchOriginalData();
});

// 监听模板变化
watch(selectedTemplate, () => {
  loadTemplate();
});
</script>

<template>
  <AppLayout>
    <div class="preprocessing-container">
      <!-- 工作流组件（悬浮在侧边） -->
      <AnalysisWorkflow 
        ref="workflowRef"
        current-step="preprocessing" 
        :dataset-id="datasetId" 
        :subject-id="subjectId" 
      />
      
      <!-- 顶部工具栏 -->
      <div class="top-toolbar">
        <div class="left-controls">
          <el-button type="primary" @click="toggleParamsPanel" size="small">
            {{ showParams ? '隐藏参数' : '显示参数' }}
          </el-button>
          <el-select 
            v-model="selectedTemplate" 
            placeholder="选择预处理模板" 
            size="small"
            style="width: 180px; margin-left: 10px;"
          >
            <el-option
              v-for="item in templateOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button type="success" @click="applyAllProcessing" :loading="isLoading.processing" size="small" style="margin-left: 10px;">
            应用所有处理
          </el-button>
        </div>
        
        <div class="right-controls">
          <div class="time-range-controls">
            <el-input-number 
              v-model="timeRange[0]" 
              :min="0" 
              :max="subjectInfo?.duration - 1 || 10" 
              :step="1"
              @change="updateTimeRange(timeRange)"
              size="small"
              style="width: 80px;"
            />
            <span style="margin: 0 5px;">至</span>
            <el-input-number 
              v-model="timeRange[1]" 
              :min="timeRange[0] + 1" 
              :max="subjectInfo?.duration || 20" 
              :step="1"
              @change="updateTimeRange(timeRange)"
              size="small"
              style="width: 80px;"
            />
            <span style="margin-left: 5px;">秒</span>
          </div>
          <el-button @click="toggleCompareMode" size="small" style="margin-left: 10px;">
            {{ compareMode ? '取消对比' : '启用对比' }}
          </el-button>
        </div>
      </div>
      
      <!-- 参数面板（可折叠，位于顶部） -->
      <transition name="fade">
        <div v-if="showParams" class="params-panel-container">
          <el-tabs v-model="activeTab" class="params-tabs" tab-position="top" type="card">
            <!-- 滤波参数 -->
            <el-tab-pane label="滤波" name="filter">
              <div class="tab-content">
                <el-form label-position="top" size="small">
                  <div class="params-grid">
                    <el-form-item label="高通滤波器">
                      <div class="control-group">
                        <el-switch v-model="preprocessParams.filter.highpass_filter" />
                        <el-input-number 
                          v-model="preprocessParams.filter.highpass" 
                          :min="0.1" 
                          :max="30" 
                          :step="0.1" 
                          :disabled="!preprocessParams.filter.highpass_filter"
                          style="margin-left: 10px;"
                          size="small"
                        />
                        <span style="margin-left: 5px;">Hz</span>
                      </div>
                    </el-form-item>
                    
                    <el-form-item label="低通滤波器">
                      <div class="control-group">
                        <el-switch v-model="preprocessParams.filter.lowpass_filter" />
                        <el-input-number 
                          v-model="preprocessParams.filter.lowpass" 
                          :min="1" 
                          :max="200" 
                          :step="1" 
                          :disabled="!preprocessParams.filter.lowpass_filter"
                          style="margin-left: 10px;"
                          size="small"
                        />
                        <span style="margin-left: 5px;">Hz</span>
                      </div>
                    </el-form-item>
                    
                    <el-form-item label="陷波滤波器">
                      <div class="control-group">
                        <el-switch v-model="preprocessParams.filter.notch_filter" />
                        <el-select 
                          v-model="preprocessParams.filter.line_freqs" 
                          multiple 
                          :disabled="!preprocessParams.filter.notch_filter"
                          style="margin-left: 10px; width: 150px;"
                          size="small"
                        >
                          <el-option label="50 Hz" :value="50.0" />
                          <el-option label="60 Hz" :value="60.0" />
                        </el-select>
                      </div>
                    </el-form-item>
                  </div>
                  
                  <div class="action-buttons">
                    <el-button type="primary" @click="applyFilter" :loading="isLoading.processing" size="small">
                      应用滤波器
                    </el-button>
                  </div>
                </el-form>
              </div>
            </el-tab-pane>
            
            <!-- 重采样参数 -->
            <el-tab-pane label="重采样" name="resample">
              <div class="tab-content">
                <el-form label-position="top" size="small">
                  <div class="params-grid">
                    <el-form-item label="启用重采样">
                      <el-switch v-model="preprocessParams.resample.resample" />
                    </el-form-item>
                    
                    <el-form-item label="重采样频率">
                      <div class="control-group">
                        <el-input-number 
                          v-model="preprocessParams.resample.resample_freq" 
                          :min="100" 
                          :max="1000" 
                          :step="50" 
                          :disabled="!preprocessParams.resample.resample"
                          size="small"
                        />
                        <span style="margin-left: 5px;">Hz</span>
                      </div>
                    </el-form-item>
                  </div>
                </el-form>
              </div>
            </el-tab-pane>
            
            <!-- 重参考参数 -->
            <el-tab-pane label="重参考" name="reference">
              <div class="tab-content">
                <el-form label-position="top" size="small">
                  <div class="params-grid">
                    <el-form-item label="参考类型">
                      <el-radio-group v-model="preprocessParams.reference.reference" size="small">
                        <el-radio label="average">平均参考</el-radio>
                        <el-radio label="mastoids">乳突参考</el-radio>
                        <el-radio label="custom">自定义</el-radio>
                      </el-radio-group>
                    </el-form-item>
                    
                    <el-form-item label="自定义参考通道" v-if="preprocessParams.reference.reference === 'custom'">
                      <el-select 
                        v-model="preprocessParams.reference.custom_ref_channels" 
                        multiple 
                        placeholder="选择参考通道"
                        style="width: 100%;"
                        size="small"
                      >
                        <el-option 
                          v-for="channel in subjectInfo?.channels" 
                          :key="channel" 
                          :label="channel" 
                          :value="channel"
                        />
                      </el-select>
                    </el-form-item>
                  </div>
                </el-form>
              </div>
            </el-tab-pane>
            
            <!-- ICA参数 -->
            <el-tab-pane label="ICA" name="ica">
              <div class="tab-content">
                <el-form label-position="top" size="small">
                  <div class="params-grid">
                    <el-form-item label="运行ICA">
                      <el-switch v-model="preprocessParams.ica.run_ica" />
                    </el-form-item>
                    
                    <el-form-item label="ICA方法">
                      <el-select 
                        v-model="preprocessParams.ica.ica_method" 
                        placeholder="选择ICA方法"
                        :disabled="!preprocessParams.ica.run_ica"
                        style="width: 100%;"
                        size="small"
                      >
                        <el-option label="FastICA" value="fastica" />
                        <el-option label="InfoMax" value="infomax" />
                        <el-option label="Extended-InfoMax" value="extended-infomax" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="组件数量">
                      <el-input-number 
                        v-model="preprocessParams.ica.n_components" 
                        :min="5" 
                        :max="100" 
                        :step="1" 
                        :disabled="!preprocessParams.ica.run_ica"
                        size="small"
                      />
                    </el-form-item>
                    
                    <el-form-item label="自动检测伪迹">
                      <el-switch 
                        v-model="preprocessParams.ica.auto_detect_artifacts"
                        :disabled="!preprocessParams.ica.run_ica"
                      />
                    </el-form-item>
                  </div>
                  
                  <div class="action-buttons">
                    <el-button type="primary" @click="runICAProcess" :loading="isLoading.processing" :disabled="!preprocessParams.ica.run_ica" size="small">
                      运行ICA
                    </el-button>
                  </div>
                </el-form>
              </div>
            </el-tab-pane>
            
            <!-- 坏通道检测 -->
            <el-tab-pane label="坏通道" name="bad_channels">
              <div class="tab-content">
                <el-form label-position="top" size="small">
                  <div class="params-grid">
                    <el-form-item label="检测坏通道">
                      <el-switch v-model="preprocessParams.bad_channels.detect_bad_channels" />
                    </el-form-item>
                    
                    <el-form-item label="检测方法">
                      <el-select 
                        v-model="preprocessParams.bad_channels.bad_channel_method" 
                        placeholder="选择检测方法"
                        :disabled="!preprocessParams.bad_channels.detect_bad_channels"
                        style="width: 100%;"
                        size="small"
                      >
                        <el-option label="相关性" value="correlation" />
                        <el-option label="方差" value="variance" />
                        <el-option label="频谱" value="spectrum" />
                      </el-select>
                    </el-form-item>
                  </div>
                </el-form>
              </div>
            </el-tab-pane>
            
            <!-- 伪迹处理 -->
            <el-tab-pane label="伪迹处理" name="artifacts">
              <div class="tab-content">
                <el-form label-position="top" size="small">
                  <div class="params-grid">
                    <el-form-item label="去除伪迹">
                      <el-switch v-model="preprocessParams.artifacts.remove_artifacts" />
                    </el-form-item>
                    
                    <el-form-item label="检测方法">
                      <el-select 
                        v-model="preprocessParams.artifacts.artifact_detection_method" 
                        placeholder="选择检测方法"
                        :disabled="!preprocessParams.artifacts.remove_artifacts"
                        style="width: 100%;"
                        size="small"
                      >
                        <el-option label="自动检测" value="auto" />
                        <el-option label="阈值法" value="threshold" />
                        <el-option label="手动标记" value="manual" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item 
                      label="幅度阈值 (μV)" 
                      v-if="preprocessParams.artifacts.artifact_detection_method === 'threshold'"
                    >
                      <el-input-number 
                        v-model="preprocessParams.artifacts.amplitude_threshold" 
                        :min="50" 
                        :max="300" 
                        :step="10" 
                        :disabled="!preprocessParams.artifacts.remove_artifacts"
                        size="small"
                      />
                    </el-form-item>
                    
                    <el-form-item label="使用标记拒绝">
                      <el-switch 
                        v-model="preprocessParams.artifacts.reject_by_annotation"
                        :disabled="!preprocessParams.artifacts.remove_artifacts"
                      />
                    </el-form-item>
                  </div>
                  
                  <div class="action-buttons">
                    <el-button type="primary" @click="removeArtifacts" :loading="isLoading.processing" :disabled="!preprocessParams.artifacts.remove_artifacts" size="small">
                      去除伪迹
                    </el-button>
                  </div>
                </el-form>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </transition>
      
      <!-- 数据展示区域 -->
      <div 
        class="data-display" 
        v-loading="isLoading.data || isLoading.processing"
      >
        <!-- 数据对比展示 -->
        <div v-if="compareMode && originalData && processedData" class="data-comparison">
          <div class="comparison-header">
            <h4>原始数据</h4>
            <h4>处理后数据</h4>
          </div>
          
          <div class="comparison-charts">
            <div class="chart-container">
              <EEGViewer 
                :data="originalData" 
                v-model:timeRange="timeRange"
                v-model:selectedChannels="selectedChannels"
                @update:timeRange="updateTimeRange"
              />
            </div>
            <div class="chart-container">
              <EEGViewer 
                :data="processedData" 
                v-model:timeRange="timeRange"
                v-model:selectedChannels="selectedChannels"
                @update:timeRange="updateTimeRange"
              />
            </div>
          </div>
        </div>
        
        <!-- 单一数据展示 -->
        <div v-else-if="originalData" class="single-view">
          <EEGViewer 
            :data="originalData" 
            v-model:timeRange="timeRange"
            v-model:selectedChannels="selectedChannels"
            @update:timeRange="updateTimeRange"
          />
        </div>
        
        <el-empty v-else description="暂无数据" />
      </div>
      
      <!-- 页面底部 -->
      <div class="page-footer">
        <el-button type="success" @click="goToNextStep">
          <el-icon><ArrowRight /></el-icon> 下一步：时域分析
        </el-button>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.preprocessing-container {
  padding: 8px 16px;
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 100px);
}

.top-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 10px 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-left: 70px; /* 为侧边栏留出空间 */
  z-index: 10;
}

.left-controls, .right-controls {
  display: flex;
  align-items: center;
}

.time-range-controls {
  display: flex;
  align-items: center;
}

/* 参数面板（现在位于顶部） */
.params-panel-container {
  margin-left: 70px; /* 为侧边栏留出空间 */
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 16px;
  transition: all 0.3s ease;
  z-index: 5;
}

.params-tabs {
  width: 100%;
}

.tab-content {
  padding: 16px;
  background-color: #fff;
  border-radius: 0 0 8px 8px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.control-group {
  display: flex;
  align-items: center;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

/* 数据显示区域 */
.data-display {
  flex: 1;
  padding: 16px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  margin-left: 70px; /* 为侧边栏留出空间 */
  min-height: 450px;
  transition: height 0.3s;
}

.data-comparison {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.comparison-header {
  display: flex;
  justify-content: space-around;
}

.comparison-header h4 {
  margin: 10px 0;
  color: #303133;
}

.comparison-charts {
  display: flex;
  flex-direction: row;
  gap: 20px;
  flex: 1;
}

.chart-container {
  flex: 1;
  min-height: 400px;
}

.single-view {
  height: 100%;
  min-height: 450px;
}

.page-footer {
  display: flex;
  justify-content: flex-end;
  padding: 10px 0;
  margin-left: 70px; /* 为侧边栏留出空间 */
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .comparison-charts {
    flex-direction: column;
  }
  
  .chart-container {
    min-height: 350px;
  }
  
  .params-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

@media (max-width: 768px) {
  .preprocessing-container {
    padding: 8px;
  }
  
  .params-grid {
    grid-template-columns: 1fr;
  }
  
  .top-toolbar {
    flex-direction: column;
    align-items: flex-start;
    margin-left: 0;
  }
  
  .right-controls {
    margin-top: 10px;
    width: 100%;
  }
  
  .time-range-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .params-panel-container,
  .data-display,
  .page-footer {
    margin-left: 0;
  }
}
</style> 