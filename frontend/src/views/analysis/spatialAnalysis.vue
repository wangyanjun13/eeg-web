<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
import TopoMap from '@/components/analysis/TopoMap.vue';
import { useLoading } from '@/composables/useLoading';
import { useFormState } from '@/composables/useFormState';
import analysisService from '@/services/analysisService';
import datasetService from '@/services/dataset';
import { useChannelPositions } from '@/composables/useChannelPositions';
import AnalysisWorkflow from '@/components/analysis/AnalysisWorkflow.vue';

const route = useRoute();
const router = useRouter();
const datasetId = computed(() => route.params.datasetId);
const subjectId = computed(() => route.params.subjectId);

// 数据状态
const topoData = ref(null);
const availableTimePoints = ref([]);
const selectedTimePoint = ref(null);
const availableFrequencyBands = ref([
  { value: 'delta', label: 'Delta (1-4 Hz)' },
  { value: 'theta', label: 'Theta (4-8 Hz)' },
  { value: 'alpha', label: 'Alpha (8-13 Hz)' },
  { value: 'beta', label: 'Beta (13-30 Hz)' },
  { value: 'gamma', label: 'Gamma (30-45 Hz)' }
]);
const selectedFrequencyBand = ref('alpha');

// 加载状态
const { isLoading, withLoading } = useLoading({
  data: false,
  applying: false
});

// 分析表单
const { formState: analysisOptions, resetForm } = useFormState('spatial-analysis-options', {
  // 插值设置
  interpolation: {
    method: 'spline', // spline, linear, nearest
    resolution: 64 // 插值分辨率
  },
  // 显示设置
  display: {
    colorMap: 'jet', // jet, viridis, plasma, inferno
    showContour: true,
    showElectrodes: true,
    normalize: true
  }
});

// 当前活动标签页
const activeTab = ref('topo');

// 加载受试者信息
const loadSubjectInfo = async () => {
  try {
    const response = await datasetService.getSubjectInfo(datasetId.value, subjectId.value);
    if (response.data) {
      console.log('受试者信息:', response.data);
    }
  } catch (error) {
    ElMessage.error('加载受试者信息失败');
    console.error(error);
  }
};

// 运行空间分析
const runSpatialAnalysis = async () => {
  try {
    const params = {
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      frequencyBand: selectedFrequencyBand.value,
      timePoint: selectedTimePoint.value,
      ...analysisOptions
    };
    
    const response = await withLoading(
      analysisService.performSpatialAnalysis(params),
      'applying'
    );
    
    if (response.data) {
      topoData.value = response.data;
      availableTimePoints.value = response.data.timePoints || [];
      if (availableTimePoints.value.length > 0 && !selectedTimePoint.value) {
        selectedTimePoint.value = availableTimePoints.value[0];
      }
      ElMessage.success('空间分析完成');
    }
  } catch (error) {
    ElMessage.error('空间分析失败');
    console.error(error);
  }
};

// 加载示例数据
const loadExampleData = async () => {
  try {
    const response = await withLoading(
      analysisService.getExampleSpatialData(),
      'data'
    );
    
    if (response.data) {
      topoData.value = response.data;
      availableTimePoints.value = response.data.timePoints || [];
      if (availableTimePoints.value.length > 0) {
        selectedTimePoint.value = availableTimePoints.value[0];
      }
      ElMessage.success('示例数据加载成功');
    }
  } catch (error) {
    ElMessage.error('加载示例数据失败');
    console.error(error);
  }
};

// 生命周期钩子
onMounted(() => {
  loadSubjectInfo();
  // 如果是示例模式，加载示例数据
  if (route.query.example === 'true') {
    loadExampleData();
  }
});
</script>

<template>
  <AppLayout>
    <div class="spatial-analysis-container">
      <h2>空间分析</h2>
      
      <el-row :gutter="20">
        <!-- 左侧控制面板 -->
        <el-col :span="6">
          <el-card class="control-panel">
            <template #header>
              <div class="card-header">
                <h3>空间分析设置</h3>
              </div>
            </template>
            
            <el-form :model="analysisOptions" label-width="120px" label-position="left">
              <!-- 频带选择 -->
              <el-form-item label="频带选择">
                <el-select v-model="selectedFrequencyBand" placeholder="选择频带">
                  <el-option
                    v-for="band in availableFrequencyBands"
                    :key="band.value"
                    :label="band.label"
                    :value="band.value"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 时间点选择 -->
              <el-form-item label="时间点" v-if="availableTimePoints.length > 0">
                <el-select v-model="selectedTimePoint" placeholder="选择时间点">
                  <el-option
                    v-for="time in availableTimePoints"
                    :key="time"
                    :label="`${time} ms`"
                    :value="time"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 插值方法 -->
              <el-form-item label="插值方法">
                <el-select v-model="analysisOptions.interpolation.method">
                  <el-option label="样条插值" value="spline" />
                  <el-option label="线性插值" value="linear" />
                  <el-option label="最近邻插值" value="nearest" />
                </el-select>
              </el-form-item>
              
              <!-- 插值分辨率 -->
              <el-form-item label="插值分辨率">
                <el-slider
                  v-model="analysisOptions.interpolation.resolution"
                  :min="32"
                  :max="128"
                  :step="16"
                  show-input
                />
              </el-form-item>
              
              <!-- 显示设置 -->
              <el-form-item label="显示设置">
                <el-checkbox v-model="analysisOptions.display.showContour">显示等高线</el-checkbox>
                <el-checkbox v-model="analysisOptions.display.showElectrodes">显示电极位置</el-checkbox>
                <el-checkbox v-model="analysisOptions.display.normalize">归一化</el-checkbox>
              </el-form-item>
              
              <!-- 颜色映射 -->
              <el-form-item label="颜色映射">
                <el-select v-model="analysisOptions.display.colorMap">
                  <el-option label="Jet" value="jet" />
                  <el-option label="Viridis" value="viridis" />
                  <el-option label="Plasma" value="plasma" />
                  <el-option label="Inferno" value="inferno" />
                </el-select>
              </el-form-item>
            </el-form>
            
            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button @click="resetForm">重置</el-button>
              <el-button type="primary" @click="runSpatialAnalysis" :loading="isLoading.applying">
                运行分析
              </el-button>
              <el-button @click="loadExampleData" :loading="isLoading.data">
                加载示例数据
              </el-button>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧显示区域 -->
        <el-col :span="18">
          <el-card class="data-display">
            <template #header>
              <div class="card-header">
                <h3>空间分布</h3>
                <el-tabs v-model="activeTab" type="card">
                  <el-tab-pane label="头皮地形图" name="topo"></el-tab-pane>
                  <el-tab-pane label="3D视图" name="3d"></el-tab-pane>
                  <el-tab-pane label="源定位" name="source"></el-tab-pane>
                </el-tabs>
              </div>
            </template>
            
            <div v-loading="isLoading.data">
              <!-- 头皮地形图 -->
              <div v-if="activeTab === 'topo' && topoData">
                <TopoMap
                  :data="topoData"
                  :colorMap="analysisOptions.display.colorMap"
                  :title="`${selectedFrequencyBand} 频带 (${selectedTimePoint || 'N/A'} ms)`"
                />
              </div>
              
              <!-- 3D视图 -->
              <div v-else-if="activeTab === '3d' && topoData">
                <div class="placeholder">
                  <el-empty description="3D视图功能正在开发中" />
                </div>
              </div>
              
              <!-- 源定位 -->
              <div v-else-if="activeTab === 'source' && topoData">
                <div class="placeholder">
                  <el-empty description="源定位功能正在开发中" />
                </div>
              </div>
              
              <!-- 无数据提示 -->
              <div v-else class="no-data">
                <el-empty description="暂无数据，请运行分析或加载示例数据" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </AppLayout>
</template>

<style scoped>
.spatial-analysis-container {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.control-panel {
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

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 10px;
}

.data-display {
  height: calc(100vh - 180px);
  overflow: auto;
}

.no-data, .placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}
</style> 