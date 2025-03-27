<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/layout/AppLayout.vue';
import { useLoading } from '@/composables/useLoading';
import { useFormState } from '@/composables/useFormState';
import analysisService from '@/services/analysisService';

const route = useRoute();
const router = useRouter();

// 数据状态
const analysisResults = ref(null);
const availableChannels = ref([]);
const selectedChannels = ref([]);

// 加载状态
const { isLoading, withLoading } = useLoading({
  data: false,
  applying: false
});

// 分析表单
const { formState: analysisOptions, resetForm } = useFormState('advanced-analysis-options', {
  // 分析类型
  analysisType: 'connectivity', // connectivity, classification, clustering
  
  // 连通性分析设置
  connectivity: {
    method: 'coherence', // coherence, plv, pli, wpli
    freqRange: [8, 13], // Hz
    timeWindow: [0, 1000], // ms
    threshold: 0.7 // 连接阈值
  },
  
  // 分类设置
  classification: {
    method: 'svm', // svm, lda, randomforest
    features: ['power', 'connectivity'],
    crossValidation: 'kfold', // kfold, loocv
    kFolds: 5
  },
  
  // 聚类设置
  clustering: {
    method: 'kmeans', // kmeans, hierarchical, dbscan
    features: ['power', 'connectivity'],
    nClusters: 3
  }
});

// 当前活动标签页
const activeTab = ref('connectivity');

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
      const result = await analysisService.performAdvancedAnalysis({
        channels: selectedChannels.value,
        options: analysisOptions
      });
      
      analysisResults.value = result.data;
      ElMessage.success('高级分析完成');
    }, 'applying');
  } catch (error) {
    console.error('高级分析失败:', error);
    ElMessage.error('高级分析失败');
  }
}

// 加载示例数据
async function loadExampleData() {
  try {
    await withLoading(async () => {
      // 模拟API调用
      const result = await analysisService.getExampleAdvancedData();
      
      // 设置可用通道
      availableChannels.value = result.channels;
      
      // 默认选择所有通道
      selectedChannels.value = availableChannels.value.map(ch => ch.id);
      
      // 设置分析结果
      analysisResults.value = result.data;
      
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

// 根据分析类型更新活动标签页
watch(() => analysisOptions.analysisType, (newType) => {
  activeTab.value = newType;
});
</script>

<template>
  <AppLayout>
    <div class="advanced-analysis-container">
      <h2>高级分析</h2>
      
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
              <!-- 分析类型 -->
              <el-form-item label="分析类型">
                <el-radio-group v-model="analysisOptions.analysisType">
                  <el-radio-button label="connectivity">连通性分析</el-radio-button>
                  <el-radio-button label="classification">分类分析</el-radio-button>
                  <el-radio-button label="clustering">聚类分析</el-radio-button>
                </el-radio-group>
              </el-form-item>
              
              <!-- 通道选择 -->
              <el-form-item label="选择通道">
                <el-select
                  v-model="selectedChannels"
                  multiple
                  collapse-tags
                  placeholder="选择通道"
                  style="width: 100%"
                >
                  <el-option
                    v-for="channel in availableChannels"
                    :key="channel.id"
                    :label="channel.name"
                    :value="channel.id"
                  />
                </el-select>
              </el-form-item>
              
              <!-- 连通性分析选项 -->
              <template v-if="analysisOptions.analysisType === 'connectivity'">
                <el-form-item label="连通性方法">
                  <el-select v-model="analysisOptions.connectivity.method" style="width: 100%">
                    <el-option label="相干性" value="coherence" />
                    <el-option label="相位锁定值" value="plv" />
                    <el-option label="相位滞后指数" value="pli" />
                    <el-option label="加权相位滞后指数" value="wpli" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="频率范围 (Hz)">
                  <el-slider
                    v-model="analysisOptions.connectivity.freqRange"
                    range
                    :min="1"
                    :max="50"
                  />
                </el-form-item>
                
                <el-form-item label="时间窗口 (ms)">
                  <el-slider
                    v-model="analysisOptions.connectivity.timeWindow"
                    range
                    :min="0"
                    :max="2000"
                    :step="100"
                  />
                </el-form-item>
                
                <el-form-item label="连接阈值">
                  <el-slider
                    v-model="analysisOptions.connectivity.threshold"
                    :min="0"
                    :max="1"
                    :step="0.05"
                  />
                </el-form-item>
              </template>
              
              <!-- 分类分析选项 -->
              <template v-if="analysisOptions.analysisType === 'classification'">
                <el-form-item label="分类方法">
                  <el-select v-model="analysisOptions.classification.method" style="width: 100%">
                    <el-option label="支持向量机" value="svm" />
                    <el-option label="线性判别分析" value="lda" />
                    <el-option label="随机森林" value="randomforest" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="特征选择">
                  <el-checkbox-group v-model="analysisOptions.classification.features">
                    <el-checkbox label="power">频带功率</el-checkbox>
                    <el-checkbox label="connectivity">连通性</el-checkbox>
                    <el-checkbox label="erp">ERP特征</el-checkbox>
                    <el-checkbox label="timefreq">时频特征</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                
                <el-form-item label="交叉验证">
                  <el-select v-model="analysisOptions.classification.crossValidation" style="width: 100%">
                    <el-option label="K折交叉验证" value="kfold" />
                    <el-option label="留一交叉验证" value="loocv" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="K折数" v-if="analysisOptions.classification.crossValidation === 'kfold'">
                  <el-input-number v-model="analysisOptions.classification.kFolds" :min="2" :max="10" />
                </el-form-item>
              </template>
              
              <!-- 聚类分析选项 -->
              <template v-if="analysisOptions.analysisType === 'clustering'">
                <el-form-item label="聚类方法">
                  <el-select v-model="analysisOptions.clustering.method" style="width: 100%">
                    <el-option label="K均值聚类" value="kmeans" />
                    <el-option label="层次聚类" value="hierarchical" />
                    <el-option label="密度聚类" value="dbscan" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="特征选择">
                  <el-checkbox-group v-model="analysisOptions.clustering.features">
                    <el-checkbox label="power">频带功率</el-checkbox>
                    <el-checkbox label="connectivity">连通性</el-checkbox>
                    <el-checkbox label="erp">ERP特征</el-checkbox>
                    <el-checkbox label="timefreq">时频特征</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                
                <el-form-item label="聚类数" v-if="analysisOptions.clustering.method === 'kmeans'">
                  <el-input-number v-model="analysisOptions.clustering.nClusters" :min="2" :max="10" />
                </el-form-item>
              </template>
              
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
                <h3>分析结果</h3>
                <el-tabs v-model="activeTab" type="card">
                  <el-tab-pane label="连通性分析" name="connectivity"></el-tab-pane>
                  <el-tab-pane label="分类分析" name="classification"></el-tab-pane>
                  <el-tab-pane label="聚类分析" name="clustering"></el-tab-pane>
                </el-tabs>
              </div>
            </template>
            
            <div v-loading="isLoading.data">
              <!-- 连通性分析结果 -->
              <div v-if="activeTab === 'connectivity' && analysisResults">
                <div class="placeholder">
                  <el-empty description="连通性分析可视化正在开发中" />
                </div>
              </div>
              
              <!-- 分类分析结果 -->
              <div v-else-if="activeTab === 'classification' && analysisResults">
                <div class="placeholder">
                  <el-empty description="分类分析可视化正在开发中" />
                </div>
              </div>
              
              <!-- 聚类分析结果 -->
              <div v-else-if="activeTab === 'clustering' && analysisResults">
                <div class="placeholder">
                  <el-empty description="聚类分析可视化正在开发中" />
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
.advanced-analysis-container {
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