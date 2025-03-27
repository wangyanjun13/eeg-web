<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
import TopoMap from '@/components/analysis/TopoMap.vue';
import { useLoading } from '@/composables/useLoading';
import { useFormState } from '@/composables/useFormState';
import analysisService from '@/services/analysisService';

const route = useRoute();
const router = useRouter();

// 数据状态
const topoData = ref(null);
const availableTimePoints = ref([]);
const selectedTimePoint = ref(null);
const availableFrequencyBands = ref([]);
const selectedFrequencyBand = ref(null);

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
    contourLines: true,
    electrodeLabels: true
  }
});

// 当前活动标签页
const activeTab = ref('topo');

// 重置选项
function resetOptions() {
  resetForm();
  ElMessage.success('已重置分析选项');
}

// 应用分析
async function applyAnalysis() {
  try {
    await withLoading(async () => {
      // 模拟API调用
      const result = await analysisService.performSpatialAnalysis({
        timePoint: selectedTimePoint.value,
        frequencyBand: selectedFrequencyBand.value,
        options: analysisOptions
      });
      
      topoData.value = result.topoData;
      ElMessage.success('空间分析完成');
    }, 'applying');
  } catch (error) {
    console.error('空间分析失败:', error);
    ElMessage.error('空间分析失败');
  }
}

// 加载示例数据
async function loadExampleData() {
  try {
    await withLoading(async () => {
      // 模拟API调用
      const result = await analysisService.getExampleSpatialData();
      
      // 设置可用时间点和频带
      availableTimePoints.value = result.timePoints;
      availableFrequencyBands.value = result.frequencyBands;
      
      // 默认选择
      selectedTimePoint.value = availableTimePoints.value[0]?.id;
      selectedFrequencyBand.value = availableFrequencyBands.value[0]?.id;
      
      // 设置地形图数据
      topoData.value = result.topoData;
      
      ElMessage.success('示例数据加载完成');
    }, 'data');
  } catch (error) {
    console.error('加载示例数据失败:', error);
    ElMessage.error('加载示例数据失败');
  }
}

// 生命周期钩子
onMounted(() => {
  loadExampleData();
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
                <h3>分析选项</h3>
              </div>
            </template>
            
            <el-form label-position="top">
              <!-- 时间点选择 -->
              <el-form-item label="选择时间点">
                <el-select
                  v-model="selectedTimePoint"
                  placeholder="选择时间点"
                  style="width: 100%"
                >
                  <el-option
                    v-for="point in availableTimePoints"
                    :key="point.id"
                    :label="`${point.name} (${point.time}ms)`"
                    :value="point.id"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 频带选择 -->
              <el-form-item label="选择频带">
                <el-select
                  v-model="selectedFrequencyBand"
                  placeholder="选择频带"
                  style="width: 100%"
                >
                  <el-option
                    v-for="band in availableFrequencyBands"
                    :key="band.id"
                    :label="`${band.name} (${band.range[0]}-${band.range[1]}Hz)`"
                    :value="band.id"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 插值方法 -->
              <el-form-item label="插值方法">
                <el-select v-model="analysisOptions.interpolation.method" style="width: 100%">
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
                  show-stops
                />
              </el-form-item>
              
              <!-- 颜色映射 -->
              <el-form-item label="颜色映射">
                <el-select v-model="analysisOptions.display.colorMap" style="width: 100%">
                  <el-option label="Jet" value="jet" />
                  <el-option label="Viridis" value="viridis" />
                  <el-option label="Plasma" value="plasma" />
                  <el-option label="Inferno" value="inferno" />
                </el-select>
              </el-form-item>
              
              <!-- 显示选项 -->
              <el-form-item label="显示选项">
                <el-checkbox v-model="analysisOptions.display.contourLines">显示等高线</el-checkbox>
                <el-checkbox v-model="analysisOptions.display.electrodeLabels">显示电极标签</el-checkbox>
              </el-form-item>
              
              <!-- 操作按钮 -->
              <div class="action-buttons">
                <el-button @click="resetOptions">重置</el-button>
                <el-button type="primary" @click="applyAnalysis" :loading="isLoading.applying">应用</el-button>
              </div>
            </el-form>
          </el-card>
        </el-col>
        
        <!-- 右侧显示区域 -->
        <el-col :span="18">
          <el-card class="data-display">
            <template #header>
              <div class="card-header">
                <h3>空间分布</h3>
                <el-tabs v-model="activeTab" type="card">
                  <el-tab-pane label="地形图" name="topo"></el-tab-pane>
                  <el-tab-pane label="3D视图" name="3d"></el-tab-pane>
                  <el-tab-pane label="源定位" name="source"></el-tab-pane>
                </el-tabs>
              </div>
            </template>
            
            <div v-loading="isLoading.data">
              <!-- 地形图 -->
              <div v-if="activeTab === 'topo' && topoData">
                <TopoMap 
                  :data="topoData" 
                  :colorMap="analysisOptions.display.colorMap"
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
                <el-empty description="暂无数据" />
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