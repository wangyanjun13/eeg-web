<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useAnalysis } from '@/composables/useAnalysis';
import { useFormState } from '@/composables/useFormState';

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

// 使用表单状态管理
const { formState, resetForm } = useFormState('eeg-preprocess-params', {
  filter: {
    highpass_filter: true,
    highpass: 1.0,
    lowpass_filter: true,
    lowpass: 40.0,
    notch_filter: true,
    line_freqs: [50.0, 60.0]
  },
  resample: {
    resample: true,
    resample_freq: 250.0
  },
  reference: {
    reference: "average",
    custom_ref_channels: []
  },
  ica: {
    run_ica: true,
    ica_method: "fastica",
    n_components: null,
    auto_detect_artifacts: true
  },
  bad_channels: {
    detect_bad_channels: true,
    bad_channel_method: "correlation"
  }
});

// 加载模板参数
const loadTemplate = async (templateName) => {
  try {
    const template = await loadPreprocessTemplate(templateName);
    if (template) {
      resetForm(template);
    }
  } catch (error) {
    console.error('加载模板错误:', error);
  }
};

// 执行预处理
const processResult = ref(null);

const runPreprocessing = async () => {
  try {
    const result = await runAnalysis('preprocess', {
      datasetId: datasetId.value,
      subjectId: subjectId.value,
      options: formState
    });
    processResult.value = result;
    ElMessage.success('预处理完成');
  } catch (error) {
    console.error('预处理错误:', error);
  }
};

// 初始化
onMounted(() => {
  // 加载默认模板
  loadTemplate(selectedTemplate.value);
});
</script>

<template>
  <div class="preprocessing-container">
    <h2>EEG数据预处理</h2>
    
    <!-- 模板选择 -->
    <div class="template-selection">
      <el-form-item label="预处理模板">
        <el-select v-model="selectedTemplate" @change="loadTemplate(selectedTemplate)">
          <el-option 
            v-for="option in templateOptions" 
            :key="option.value"
            :label="option.label" 
            :value="option.value">
            <div>{{ option.label }}</div>
            <small>{{ option.description }}</small>
          </el-option>
        </el-select>
      </el-form-item>
    </div>
    
    <el-form :model="formState" label-width="120px">
      <el-collapse>
        <!-- 重采样参数 -->
        <el-collapse-item title="重采样参数" name="resample">
          <el-form-item label="启用重采样">
            <el-switch v-model="formState.resample.resample" />
          </el-form-item>
          <el-form-item v-if="formState.resample.resample" label="采样频率">
            <el-input-number 
              v-model="formState.resample.resample_freq" 
              :min="100" 
              :max="1000"
              :step="1"
            />
            <span>Hz</span>
          </el-form-item>
        </el-collapse-item>
        
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
              :min="20" 
              :max="100"
              :step="1"
            />
            <span>Hz</span>
          </el-form-item>
          
          <el-form-item label="陷波滤波">
            <el-switch v-model="formState.filter.notch_filter" />
          </el-form-item>
          <el-form-item v-if="formState.filter.notch_filter" label="陷波频率">
            <el-tag 
              v-for="(freq, index) in formState.filter.line_freqs" 
              :key="index"
              closable
              @close="formState.filter.line_freqs.splice(index, 1)"
            >
              {{ freq }}Hz
            </el-tag>
            <el-button size="small" @click="formState.filter.line_freqs.push(50)">
              + 添加频率
            </el-button>
          </el-form-item>
        </el-collapse-item>
        
        <!-- 重参考参数 -->
        <el-collapse-item title="重参考参数" name="reference">
          <el-form-item label="参考方式">
            <el-radio-group v-model="formState.reference.reference">
              <el-radio label="average">平均参考</el-radio>
              <el-radio label="mastoids">双侧乳突</el-radio>
              <el-radio label="custom">自定义</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-collapse-item>
        
        <!-- ICA参数 -->
        <el-collapse-item title="ICA参数" name="ica">
          <el-form-item label="运行ICA">
            <el-switch v-model="formState.ica.run_ica" />
          </el-form-item>
          <el-form-item v-if="formState.ica.run_ica" label="ICA方法">
            <el-select v-model="formState.ica.ica_method">
              <el-option label="FastICA" value="fastica" />
              <el-option label="Extended Infomax" value="infomax" />
              <el-option label="Picard" value="picard" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="formState.ica.run_ica" label="自动检测伪迹">
            <el-switch v-model="formState.ica.auto_detect_artifacts" />
          </el-form-item>
        </el-collapse-item>
        
        <!-- 坏通道检测 -->
        <el-collapse-item title="坏通道检测" name="bad_channels">
          <el-form-item label="检测坏通道">
            <el-switch v-model="formState.bad_channels.detect_bad_channels" />
          </el-form-item>
          <el-form-item v-if="formState.bad_channels.detect_bad_channels" label="检测方法">
            <el-select v-model="formState.bad_channels.bad_channel_method">
              <el-option label="相关性" value="correlation" />
              <el-option label="方差" value="variance" />
              <el-option label="频谱" value="spectrum" />
            </el-select>
          </el-form-item>
        </el-collapse-item>
      </el-collapse>
      
      <!-- 执行按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="runPreprocessing" :loading="isLoading">
          执行预处理
        </el-button>
      </div>
    </el-form>
    
    <!-- 处理结果展示 -->
    <div v-if="processResult" class="process-result">
      <h3>预处理结果</h3>
      <el-card>
        <div v-for="(method, index) in processResult.applied_methods" :key="index">
          {{ method }}
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.preprocessing-container {
  padding: 20px;
}

.template-selection {
  margin-bottom: 20px;
}

.action-buttons {
  margin-top: 20px;
  text-align: center;
}

.process-result {
  margin-top: 30px;
}
</style> 