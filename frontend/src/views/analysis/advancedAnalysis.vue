<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
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
  
  // 分类分析设置
  classification: {
    method: 'svm', // svm, lda, rf
    features: ['power', 'connectivity'], // power, connectivity, time
    crossValidation: true,
    kFold: 5
  },
  
  // 聚类分析设置
  clustering: {
    method: 'kmeans', // kmeans, hierarchical, dbscan
    features: ['power'], // power, connectivity, time
    nClusters: 3
  }
});

// 当前活动标签页
const activeTab = ref('connectivity');

// 通道选择
const { 
  openChannelSelect, 
  renderChannelSelectDialog 
} = useChannelPositions();

// 加载受试者信息和可用通道
const loadSubjectInfo = async () => {
  try {
    const response = await datasetService.getSubjectInfo(datasetId.value, subjectId.value);
    if (response.data && response.data.channels) {
      availableChannels.value = response.data.channels;
      // 默认选择前10个通道
      selectedChannels.value = availableChannels.value.slice(0, 10);
    }
  } catch (error) {
    ElMessage.error('加载受试者信息失败');
    console.error(error);
  }
};

// 运行高级分析
const runAdvancedAnalysis = async () => {
  if (selectedChannels.value.length === 0) {
    ElMessage.warning('请至少选择一个通道');
    return;
  }
  
  try {
    const params = {
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      channels: selectedChannels.value,
      ...analysisOptions
    };
    
    const response = await withLoading(
      analysisService.performAdvancedAnalysis(params),
      'applying'
    );
    
    if (response.data) {
      analysisResults.value = response.data;
      ElMessage.success('高级分析完成');
    }
  } catch (error) {
    ElMessage.error('高级分析失败');
    console.error(error);
  }
};

// 加载示例数据
const loadExampleData = async () => {
  try {
    const response = await withLoading(
      analysisService.getExampleAdvancedData(),
      'data'
    );
    
    if (response.data) {
      analysisResults.value = response.data;
      ElMessage.success('示例数据加载成功');
    }
  } catch (error) {
    ElMessage.error('加载示例数据失败');
    console.error(error);
  }
};

// 选择通道
const handleSelectChannels = () => {
  openChannelSelect(
    selectedChannels.value,
    availableChannels.value,
    (selected) => {
      selectedChannels.value = selected;
    }
  );
};

// 初始化
onMounted(() => {
  loadSubjectInfo();
  // 如果是示例模式，加载示例数据
  if (route.query.example === 'true') {
    loadExampleData();
  }
});

// 监听分析类型变化
watch(() => analysisOptions.analysisType, (newType) => {
  activeTab.value = newType;
});

const workflowRef = ref(null);

// 前往下一步
function goToNextStep() {
  workflowRef.value?.goToNextStep();
}
</script>

<template>
  <div class="advanced-analysis-container">
    <!-- 控制面板 -->
    <el-card class="control-panel">
      <template #header>
        <div class="card-header">
          <h3>高级分析设置</h3>
        </div>
      </template>
      
      <el-form :model="analysisOptions" label-width="120px" label-position="left">
        <!-- 分析类型 -->
        <el-form-item label="分析类型">
          <el-radio-group v-model="analysisOptions.analysisType">
            <el-radio-button label="connectivity">连通性分析</el-radio-button>
            <el-radio-button label="classification">分类分析</el-radio-button>
            <el-radio-button label="clustering">聚类分析</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <!-- 通道选择 -->
        <el-form-item label="通道选择">
          <div class="channel-selection">
            <el-button size="small" @click="handleSelectChannels">
              选择通道
            </el-button>
            <div class="selected-channels" v-if="selectedChannels.length > 0">
              已选择 {{ selectedChannels.length }} 个通道
            </div>
          </div>
        </el-form-item>
        
        <!-- 连通性分析设置 -->
        <template v-if="analysisOptions.analysisType === 'connectivity'">
          <el-form-item label="连通性方法">
            <el-select v-model="analysisOptions.connectivity.method">
              <el-option label="相干性" value="coherence" />
              <el-option label="相位锁定值" value="plv" />
              <el-option label="相位滞后指数" value="pli" />
              <el-option label="加权相位滞后指数" value="wpli" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="频率范围">
            <el-slider
              v-model="analysisOptions.connectivity.freqRange"
              range
              :min="1"
              :max="50"
              :step="1"
              show-input
            >
              <template #default="{ modelValue }">
                {{ modelValue[0] }} - {{ modelValue[1] }} Hz
              </template>
            </el-slider>
          </el-form-item>
          
          <el-form-item label="时间窗口">
            <el-slider
              v-model="analysisOptions.connectivity.timeWindow"
              range
              :min="0"
              :max="2000"
              :step="100"
              show-input
            >
              <template #default="{ modelValue }">
                {{ modelValue[0] }} - {{ modelValue[1] }} ms
              </template>
            </el-slider>
          </el-form-item>
          
          <el-form-item label="连接阈值">
            <el-slider
              v-model="analysisOptions.connectivity.threshold"
              :min="0"
              :max="1"
              :step="0.05"
              show-input
            />
          </el-form-item>
        </template>
        
        <!-- 分类分析设置 -->
        <template v-if="analysisOptions.analysisType === 'classification'">
          <el-form-item label="分类方法">
            <el-select v-model="analysisOptions.classification.method">
              <el-option label="支持向量机" value="svm" />
              <el-option label="线性判别分析" value="lda" />
              <el-option label="随机森林" value="rf" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="特征选择">
            <el-checkbox-group v-model="analysisOptions.classification.features">
              <el-checkbox label="power">功率谱</el-checkbox>
              <el-checkbox label="connectivity">连通性</el-checkbox>
              <el-checkbox label="time">时域特征</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="交叉验证">
            <el-switch v-model="analysisOptions.classification.crossValidation" />
          </el-form-item>
          
          <el-form-item label="K折交叉验证" v-if="analysisOptions.classification.crossValidation">
            <el-input-number
              v-model="analysisOptions.classification.kFold"
              :min="2"
              :max="10"
              :step="1"
            />
          </el-form-item>
        </template>
        
        <!-- 聚类分析设置 -->
        <template v-if="analysisOptions.analysisType === 'clustering'">
          <el-form-item label="聚类方法">
            <el-select v-model="analysisOptions.clustering.method">
              <el-option label="K均值聚类" value="kmeans" />
              <el-option label="层次聚类" value="hierarchical" />
              <el-option label="密度聚类" value="dbscan" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="特征选择">
            <el-checkbox-group v-model="analysisOptions.clustering.features">
              <el-checkbox label="power">功率谱</el-checkbox>
              <el-checkbox label="connectivity">连通性</el-checkbox>
              <el-checkbox label="time">时域特征</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="聚类数量" v-if="analysisOptions.clustering.method !== 'dbscan'">
            <el-input-number
              v-model="analysisOptions.clustering.nClusters"
              :min="2"
              :max="10"
              :step="1"
            />
          </el-form-item>
        </template>
      </el-form>
      
      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button @click="resetForm">重置</el-button>
        <el-button type="primary" @click="runAdvancedAnalysis" :loading="isLoading.applying">
          运行分析
        </el-button>
        <el-button @click="loadExampleData" :loading="isLoading.data">
          加载示例数据
        </el-button>
        <el-button type="success" @click="goToNextStep">下一步</el-button>
      </div>
    </el-card>
    
    <!-- 数据显示 -->
    <div class="data-display">
      <el-card v-if="analysisResults">
        <template #header>
          <div class="card-header">
            <h3>分析结果</h3>
          </div>
        </template>
        
        <!-- 根据分析类型显示不同的结果 -->
        <div v-if="analysisOptions.analysisType === 'connectivity'">
          <!-- 连通性分析结果 -->
          <div id="connectivity-chart" style="width: 100%; height: 500px;"></div>
        </div>
        
        <div v-else-if="analysisOptions.analysisType === 'classification'">
          <!-- 分类分析结果 -->
          <div class="classification-results">
            <h4>分类性能</h4>
            <el-table :data="analysisResults.performance" style="width: 100%">
              <el-table-column prop="metric" label="指标" />
              <el-table-column prop="value" label="值" />
            </el-table>
            
            <h4 class="mt-4">混淆矩阵</h4>
            <div id="confusion-matrix" style="width: 100%; height: 400px;"></div>
          </div>
        </div>
        
        <div v-else-if="analysisOptions.analysisType === 'clustering'">
          <!-- 聚类分析结果 -->
          <div class="clustering-results">
            <h4>聚类结果</h4>
            <div id="clustering-chart" style="width: 100%; height: 500px;"></div>
          </div>
        </div>
      </el-card>
      
      <div v-else class="no-data">
        <el-empty description="暂无数据，请运行分析或加载示例数据" />
      </div>
    </div>
    
    <!-- 通道选择对话框 -->
    <component :is="renderChannelSelectDialog()" />
    
    <!-- 分析流程导航 -->
    <AnalysisWorkflow 
      ref="workflowRef"
      current-step="spatial" 
      :dataset-id="datasetId" 
      :subject-id="subjectId" 
    />
  </div>
</template>

<style scoped>
.advanced-analysis-container {
  padding: 20px;
  padding-bottom: 60px;
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

.channel-selection, .selected-channels {
  margin-top: 8px;
}

.selected-channels {
  font-size: 12px;
  color: #606266;
  margin-top: 8px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 10px;
}

.data-display {
  margin-top: 20px;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  margin-top: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.classification-results h4, .clustering-results h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  font-size: 16px;
  font-weight: 600;
}
</style> 