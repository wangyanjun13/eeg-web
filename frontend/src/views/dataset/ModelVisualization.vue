<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus';
import { ArrowLeft, Download, View, DataAnalysis } from '@element-plus/icons-vue';
import AppLayout from '@/components/layout/AppLayout.vue';
import EEGViewer from '@/components/analysis/EEGViewer.vue';
import datasetService from '@/services/dataset';
import { formatDate, formatFileSize } from '@/utils/formatters';

const route = useRoute();
const router = useRouter();

// 获取路由参数
const dataFileId = route.query.dataFileId;
const modelFileId = route.query.modelFileId;

// 文件信息
const dataFile = ref(null);
const modelFile = ref(null);

// EEG显示相关
const timeRange = ref([0, 10]);
const selectedChannels = ref([]);
const availableChannels = ref([]);
const viewMode = ref('time'); // 'time' 或 'frequency'

// 可视化数据
const originalData = ref(null);
const processedData = ref(null);
const isLoading = ref(false);

// 分析结果
const analysisResults = ref({
  accuracy: null,
  precision: null,
  recall: null,
  f1_score: null,
  mse: null,
  mae: null,
  snr: null,
  snr_improvement: null,
  pearson: null,
  waveform_fidelity: null,
  confusionMatrix: null,
  elapsedTime: null,
});

// 添加状态变量
const evaluationState = ref('loading'); // 'loading', 'success', 'error'
const errorInfo = ref(null);

// 格式化EEG数据
const formatEEGData = (rawData) => {
  if (!rawData) return null;
  
  console.log('开始格式化EEG数据:', rawData);
  
  // 确保数据至少包含基本结构
  if (!rawData.data || !Array.isArray(rawData.data) || rawData.data.length === 0) {
    console.error('原始数据缺少必要的数据点数组');
    return null;
  }
  
  // 解析通道名称
  const channels = rawData.channels || ['Channel 1'];
  
  // 解析采样率
  const samplingRate = rawData.sampling_rate || 250; // Hz
  
  // 创建时间序列 - 根据数据长度创建适当的时间点
  const dataLength = Array.isArray(rawData.data[0]) ? rawData.data[0].length : rawData.data.length;
  const times = rawData.times || Array.from({length: dataLength}, (_, i) => i / samplingRate);
  
  // 准备数据对象
  const formattedData = {
    channels: channels,
    times: times,
    data: {},
    sampling_rate: samplingRate,
    duration: times[times.length - 1],
    timeRange: [times[0], times[times.length - 1]]
  };
  
  // 处理不同的数据结构
  if (Array.isArray(rawData.data) && !rawData.data[0].hasOwnProperty('length')) {
    // 单通道数据
    console.log('检测到单通道数据');
    formattedData.data[channels[0]] = rawData.data.slice();
  } else if (Array.isArray(rawData.data) && Array.isArray(rawData.data[0])) {
    // 多通道数据 - channels是数组，data是二维数组
    console.log('检测到多通道数据');
    channels.forEach((channel, idx) => {
      if (idx < rawData.data.length) {
        formattedData.data[channel] = rawData.data[idx].slice();
      } else {
        console.warn(`没有为通道 ${channel} 找到数据`);
        formattedData.data[channel] = Array(dataLength).fill(0);
      }
    });
  } else if (typeof rawData.data === 'object') {
    // 数据已经是 {channel1: [...], channel2: [...]} 格式
    console.log('检测到对象格式的通道数据');
    Object.keys(rawData.data).forEach(channel => {
      if (channels.includes(channel)) {
        formattedData.data[channel] = rawData.data[channel].slice();
      }
    });
    
    // 如果没有匹配到任何通道，尝试直接使用所有数据
    if (Object.keys(formattedData.data).length === 0) {
      console.warn('未找到匹配的通道，使用所有可用数据');
      formattedData.data = { ...rawData.data };
      // 更新通道列表以反映实际数据
      formattedData.channels = Object.keys(rawData.data);
    }
  }
  
  // 检查是否成功格式化了数据
  const hasData = Object.values(formattedData.data).some(arr => arr && arr.length > 0);
  
  if (!hasData) {
    console.error('无法从原始数据中提取有效的EEG数据');
    // 移除随机示例数据生成
    // 不再创建模拟数据，直接返回null
    return null;
  } else {
    console.log('EEG数据格式化成功:', Object.keys(formattedData.data).length, '个通道');
  }
  
  return formattedData;
};

// 加载文件信息
const loadFileInfo = async () => {
  try {
    isLoading.value = true;
    
    if (dataFileId) {
      const response = await datasetService.getUploadedFile(dataFileId);
      if (response.status === 'success') {
        dataFile.value = response.file;
      } else {
        ElMessage.error('加载数据文件信息失败');
        return;
      }
    }
    
    if (modelFileId) {
      const response = await datasetService.getUploadedFile(modelFileId);
      if (response.status === 'success') {
        modelFile.value = response.file;
      } else {
        ElMessage.error('加载模型文件信息失败');
        return;
      }
    }
    
    if (!dataFile.value || !modelFile.value) {
      ElMessage.error('缺少必要的文件信息');
      return;
    }
    
    // 加载模型评测数据
    await loadVisualizationData();
    
  } catch (error) {
    console.error('加载文件信息失败:', error);
    ElMessage.error('加载文件信息失败: ' + error.message);
  } finally {
    isLoading.value = false;
  }
};

// 加载可视化数据（使用API）
const loadVisualizationData = async () => {
  try {
    console.log('开始加载模型可视化数据...');
    evaluationState.value = 'loading'; // 设置为加载状态
    
    const loadingInstance = ElLoading.service({
      text: '正在评测模型，这可能需要一些时间...',
      background: 'rgba(255, 255, 255, 0.7)',
    });
    
    // 调用API评估模型
    let response;
    try {
      console.log('调用模型评测接口...');
      response = await datasetService.evaluateModel(dataFileId, modelFileId);
      console.log('收到模型评测响应:', response);
    } catch(apiError) {
      console.error('API调用失败:', apiError);
      throw new Error(`无法连接到评测服务: ${apiError.message || '未知错误'}`);
    } finally {
    loadingInstance.close();
    }
    
    // 检查响应是否存在
    if (!response) {
      console.error('评测返回空响应');
      throw new Error('评测模型失败: 未获得响应');
    }
    
    // 处理响应数据，确保我们处理的是正确的格式
    // 从evaluateModel返回的是整个response对象，我们需要获取它的data属性
    const responseData = response.data || response;
    
    // 无论状态如何，都允许处理响应
    if (responseData.status === 'success') {
      // 正常处理成功响应
      console.log('成功处理模型评测结果');
      
      // 检查visualization_data是否存在
      if (!responseData.visualization_data) {
        console.error('缺少visualization_data字段');
        throw new Error('服务器响应中缺少可视化数据');
      }
      
      console.log('原始可视化数据结构:', responseData.visualization_data);
      
      // 格式化原始数据
      if (responseData.visualization_data.original) {
        console.log('处理原始数据:', responseData.visualization_data.original);
        originalData.value = formatEEGData(responseData.visualization_data.original);
        console.log('格式化后的原始数据:', originalData.value);
      } else {
        console.error('缺少原始数据');
        originalData.value = null;
      }
      
      // 格式化处理后的数据
      if (responseData.visualization_data.processed) {
        console.log('处理模型输出数据:', responseData.visualization_data.processed);
        processedData.value = formatEEGData(responseData.visualization_data.processed);
        console.log('格式化后的处理数据:', processedData.value);
      } else {
        console.error('缺少处理后的数据');
        processedData.value = null;
      }
      
      // 如果数据格式化失败，直接显示错误，不再尝试创建模拟数据
      if (!originalData.value || !processedData.value) {
        console.error('数据格式化失败，无法显示可视化');
        throw new Error('无法格式化EEG数据，请检查数据格式是否正确');
      }
      
      // 设置可用通道
      if (originalData.value && originalData.value.channels && originalData.value.channels.length > 0) {
        availableChannels.value = originalData.value.channels;
        // 默认选择所有通道或最多5个通道显示
        selectedChannels.value = originalData.value.channels.slice(0, Math.min(5, originalData.value.channels.length));
        console.log('设置可用通道:', availableChannels.value);
      } else {
        console.warn('找不到可用通道');
        availableChannels.value = [];
        selectedChannels.value = [];
      }
      
      // 设置分析结果
      analysisResults.value = {
        mse: responseData.results?.mse || 0,
        mae: responseData.results?.mae || 0,
        snr: responseData.results?.snr || 0,
        pearson: responseData.results?.pearson || 0,
        waveform_fidelity: responseData.results?.waveform_fidelity || 0,
        elapsedTime: responseData.results?.elapsed_time || 0
      };
      
      // 设置状态为成功
      evaluationState.value = 'success';
      
      console.log('模型评测完成:', responseData);
    } else if (responseData.status === 'error') {
      // 处理结构化错误响应
      console.error('模型评测出现错误:', responseData);
      
      // 设置错误状态和信息
      evaluationState.value = 'error';
      errorInfo.value = {
        type: responseData.error_type || 'unknown_error',
        message: responseData.message || '未知错误',
        details: responseData.details || {}
      };
      
      // 显示错误信息对话框
      showModelErrorDialog(responseData);
    } else {
      console.error('未知的响应状态:', responseData.status);
      evaluationState.value = 'error';
      errorInfo.value = {
        type: 'unknown_status',
        message: `未知的响应状态: ${responseData.status || 'undefined'}`,
        details: responseData
      };
      
      // 显示基本错误对话框
      showModelErrorDialog({
        status: 'error',
        error_type: 'unknown_status',
        message: `未知的响应状态: ${responseData.status || 'undefined'}`,
        details: responseData
      });
    }
  } catch (error) {
    console.error('评测模型失败:', error);
    
    // 设置错误状态
    evaluationState.value = 'error';
    errorInfo.value = {
      type: 'client_error',
      message: error.message || '未知错误',
      details: {}
    };
    
    // 显示更友好的错误信息
    ElMessageBox.confirm(
      `模型评测过程中出现错误: ${error.message || '未知错误'}\n\n这可能是因为以下原因之一:\n- 模型包含自定义层\n- 模型结构与数据不兼容\n- 服务器处理超时\n\n您可以尝试重试或者返回选择其他模型。`,
      '评测失败',
      {
        confirmButtonText: '重试',
        cancelButtonText: '返回',
        type: 'warning'
      }
    ).then(() => {
      // 用户选择重试
      loadVisualizationData();
    }).catch(() => {
      // 用户选择返回
      goBack();
    });
  }
};

// 显示模型错误对话框
const showModelErrorDialog = (response) => {
  let errorMessage = response.message || '未知错误';
  let detailHtml = '';
  
  console.log('处理错误对话框数据:', response);
  
  if (response.error_type === 'model_loading_error') {
    // 尝试从错误消息中提取更有用的信息
    let errorDetails = errorMessage;
    let technicalError = response.details?.technical_error || errorMessage;
    
    if (errorMessage.includes('mean_squared_error')) {
      errorDetails = '模型使用了自定义的mean_squared_error损失函数，当前环境无法识别。';
    } else if (errorMessage.includes('could not be transformed to Keras')) {
      errorDetails = '模型使用了非标准的TensorFlow层，当前环境无法加载。';
    } else if (errorMessage.includes('BasicBlockall')) {
      errorDetails = '模型使用了自定义的BasicBlockall层，需要特定的加载环境。';
    }
    
    detailHtml = `
      <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
        <p>错误原因: 无法加载模型</p>
        <p class="error-tech-details" style="word-break: break-word; font-family: monospace; background: #fff; padding: 8px; border-left: 3px solid #F56C6C;">${technicalError}</p>
        <p>简化说明: ${errorDetails}</p>
        <p>这通常是因为:</p>
        <ul>
          <li>模型包含自定义层，需要额外代码支持</li>
          <li>模型依赖特定的TensorFlow版本</li>
          <li>模型使用了不兼容的损失函数</li>
          <li>模型结构与当前支持的格式不兼容</li>
        </ul>
        <p>建议: 尝试使用标准层构建的模型，或者联系开发人员添加对应的自定义层支持。</p>
      </div>
    `;
  } else if (response.error_type === 'processing_error') {
    // 处理模型处理过程中的错误
    let errorDetails = errorMessage;
    let technicalError = response.details?.technical_error || errorMessage;
    
    // 提取具体的错误信息
    if (errorMessage.includes('expected axis -1 of input shape to have value') && 
        errorMessage.includes('but received input with shape')) {
      // 特定的形状不匹配错误处理
      // 尝试从错误信息中提取形状信息
      const expectedMatch = errorMessage.match(/expected axis -1 of input shape to have value (\d+)/);
      const receivedMatch = errorMessage.match(/received input with shape \(([^)]+)\)/);
      
      const expectedSize = expectedMatch ? expectedMatch[1] : '未知';
      const receivedShape = receivedMatch ? receivedMatch[1] : '未知';
      
      errorDetails = `模型期望的输入维度为 ${expectedSize}，但实际收到的输入维度为 ${receivedShape}。这是一个严重的形状不匹配问题。`;
      
      detailHtml = `
        <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
          <p>错误原因: 模型输入形状严重不匹配</p>
          <p class="error-tech-details" style="word-break: break-word; font-family: monospace; background: #fff; padding: 8px; border-left: 3px solid #F56C6C;">${errorMessage}</p>
          <p>简化说明: ${errorDetails}</p>
          
          <div style="background: #fff3e0; padding: 12px; margin: 15px 0; border-radius: 4px; border-left: 4px solid #ff9800;">
            <h4 style="margin-top: 0; color: #e65100;">形状不匹配详情</h4>
            <p>预期输入维度: <strong>${expectedSize}</strong></p>
            <p>实际输入维度: <strong>${receivedShape}</strong></p>
            <p>这表明您的模型设计用于处理不同大小的EEG数据。</p>
          </div>
          
          <p>解决方案:</p>
          <ol>
            <li>确保您上传的模型是专门设计用于EEG数据处理的</li>
            <li>检查模型的第一层输入形状，应与您的数据格式匹配</li>
            <li>您可以尝试修改模型架构以适应当前数据的形状 (${receivedShape})</li>
            <li>或者准备与模型期望的形状 (${expectedSize}) 匹配的数据</li>
          </ol>
          
          <div style="background: #e8f4fd; padding: 12px; margin: 15px 0; border-radius: 4px; border-left: 4px solid #2196f3;">
            <h4 style="margin-top: 0; color: #0d47a1;">TensorFlow模型兼容性提示</h4>
            <p>推荐使用以下模型架构：</p>
            <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; font-family: monospace;">
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(通道数, 时间点数)),  # 匹配您的EEG数据形状
    tf.keras.layers.Conv1D(filters=16, kernel_size=3, activation='relu'),
    tf.keras.layers.MaxPooling1D(pool_size=2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(通道数 * 时间点数, activation='linear'),
    tf.keras.layers.Reshape((通道数, 时间点数))
])
            </pre>
            <p>确保第一层的输入形状与您的EEG数据匹配，最后的输出形状也应当与输入相同。</p>
          </div>
        </div>
      `;
    } else if (errorMessage.includes('Exception encountered when calling') || 
        errorMessage.includes('tensorflow') ||
        errorMessage.includes('model.predict')) {
      errorDetails = '模型预测过程中发生错误，通常是因为输入数据格式与模型期望的不匹配。';
      
      detailHtml = `
        <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
          <p>错误原因: 模型处理数据失败</p>
          <p class="error-tech-details" style="word-break: break-word; font-family: monospace; background: #fff; padding: 8px; border-left: 3px solid #F56C6C;">${errorMessage}</p>
          <p>简化说明: ${errorDetails}</p>
          <p>可能的原因:</p>
          <ul>
            <li>模型的输入形状与数据不匹配</li>
            <li>模型需要特定格式的数据预处理</li>
            <li>模型的预测函数可能存在问题</li>
            <li>服务器资源不足以处理请求</li>
          </ul>
          <p>建议解决方案:</p>
          <ol>
            <li>确认模型是为EEG数据设计的</li>
            <li>检查模型的输入形状和预期数据格式</li>
            <li>尝试使用较小的数据样本</li>
            <li>使用标准化的模型结构，避免复杂的自定义操作</li>
          </ol>
        </div>
      `;
    } else if (errorMessage.includes('shape')) {
      errorDetails = '数据形状不匹配，模型无法处理当前格式的EEG数据。';
      
      detailHtml = `
        <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
          <p>错误原因: 形状不匹配</p>
          <p class="error-tech-details" style="word-break: break-word; font-family: monospace; background: #fff; padding: 8px; border-left: 3px solid #F56C6C;">${errorMessage}</p>
          <p>简化说明: ${errorDetails}</p>
          <p>可能的原因:</p>
          <ul>
            <li>模型期望的输入形状与实际数据不符</li>
            <li>模型的输出形状可能与预期不同</li>
            <li>数据可能需要重塑(reshape)以匹配模型的期望</li>
          </ul>
          <p>建议解决方案:</p>
          <ol>
            <li>检查模型的输入层定义</li>
            <li>修改模型以适应您的数据形状</li>
            <li>或者调整数据预处理步骤以匹配模型期望</li>
          </ol>
        </div>
      `;
    } else {
      detailHtml = `
        <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
          <p>错误原因: 模型处理数据失败</p>
          <p class="error-tech-details" style="word-break: break-word; font-family: monospace; background: #fff; padding: 8px; border-left: 3px solid #F56C6C;">${errorMessage}</p>
          <p>简化说明: ${errorDetails}</p>
          <p>可能的原因:</p>
          <ul>
            <li>模型的输入形状与数据不匹配</li>
            <li>模型需要特定格式的数据预处理</li>
            <li>模型的预测函数可能存在问题</li>
            <li>服务器资源不足以处理请求</li>
          </ul>
          <p>建议解决方案:</p>
          <ol>
            <li>确认模型是为EEG数据设计的</li>
            <li>检查模型的输入形状和预期数据格式</li>
            <li>尝试使用较小的数据样本</li>
            <li>使用标准化的模型结构，避免复杂的自定义操作</li>
          </ol>
        </div>
      `;
    }
  } else if (response.error_type === 'shape_mismatch' && response.details) {
    detailHtml = `
      <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
        <p><span style="font-weight: bold;">输入数据形状:</span> ${response.details.input_shape || '未知'}</p>
        <p><span style="font-weight: bold;">模型输出形状:</span> ${response.details.output_shape || '未知'}</p>
        
        <div style="background-color: #fff3e0; padding: 12px; margin: 15px 0; border-radius: 4px; border-left: 4px solid #ff9800;">
          <h4 style="margin-top: 0; color: #e65100;">形状不匹配原因解析</h4>
          <p>可能的原因:</p>
          <ul>
            <li>模型可能期望<strong>单通道</strong>数据，但收到了<strong>多通道</strong>数据（或反之）</li>
            <li>数据是<strong>样本集</strong>(多个样本)，但被当作<strong>单个样本</strong>处理</li>
            <li>模型设计用于不同<strong>时间点数量</strong>的EEG数据</li>
          </ul>
          <p>建议解决方案:</p>
          <ul>
            <li>检查您的数据文件格式是否符合期望 (样本集或单个多通道样本)</li>
            <li>确认您的模型是否设计用于此类数据形状</li>
            <li>如果数据是样本集(EMG_epochs)，系统会选择第一个样本，确保这是您期望的行为</li>
          </ul>
        </div>
        
        <p>建议: 使用设计用于当前EEG数据格式的模型，确保输入输出形状匹配。</p>
      </div>
    `;
  } else if (response.error_type === 'request_error') {
    // 处理请求错误
    detailHtml = `
      <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
        <p>错误类型: 请求错误</p>
        <p>详细信息: ${errorMessage}</p>
        <p>可能的原因:</p>
        <ul>
          <li>服务器暂时无法访问</li>
          <li>网络连接问题</li>
          <li>请求格式错误</li>
        </ul>
        <p>建议: 确认网络连接正常，然后重试操作。如果问题持续存在，请刷新页面后再试。</p>
      </div>
    `;
  } else {
    // 处理其他类型的错误
    detailHtml = `
      <div style="background: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 4px;">
        <p>错误类型: ${response.error_type || '未知错误类型'}</p>
        <p>详细信息: ${JSON.stringify(response.details || {})}</p>
        <p>请尝试以下操作:</p>
        <ul>
          <li>使用更简单的模型结构</li>
          <li>确认数据文件格式正确</li>
          <li>尝试重新上传模型文件</li>
          <li>如果问题持续存在，请联系管理员</li>
        </ul>
      </div>
    `;
  }
  
  // 添加通用的有用提示部分
  detailHtml += `
    <div style="background: #e1f5fe; padding: 12px; margin: 15px 0; border-radius: 4px; border-left: 4px solid #03a9f4;">
      <h4 style="margin-top: 0; color: #01579b;">实用提示</h4>
      <p>为了获得更好的体验，请考虑以下建议：</p>
      <ul style="margin-bottom: 0;">
        <li>保持数据文件大小在10MB以下以提高处理速度</li>
        <li>使用标准Keras/TensorFlow模型，避免复杂的自定义层</li>
        <li>确保模型设计用于EEG数据处理，结构合理</li>
        <li>对模型进行简化，减少层数和参数</li>
        <li>检查您的EEG数据通道排列是否与模型期望一致</li>
        <li>如果继续遇到问题，可尝试重新上传更兼容的模型</li>
      </ul>
    </div>
  `;
  
  ElMessageBox.alert(
    `<div style="text-align: left;">
      <p style="font-weight: bold; color: #F56C6C;">模型评测失败</p>
      <p>${errorMessage}</p>
      ${detailHtml}
    </div>`,
    '评测失败',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '我明白了',
      type: 'error',
      callback: () => {
        // 用户可以在此界面查看原始数据
      }
    }
  );
};

// 处理回到文件列表
const goBack = () => {
  router.push('/my-files');
};

// 下载分析结果
const downloadResults = () => {
  const results = {
    dataFile: dataFile.value,
    modelFile: modelFile.value,
    analysisResults: analysisResults.value,
    timestamp: new Date().toISOString()
  };
  
  const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `预测结果_${dataFile.value.name}_${new Date().getTime()}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  
  ElMessage.success('预测结果已下载');
};

// 处理通道更新
const updateSelectedChannels = (channels) => {
  selectedChannels.value = channels;
};

// 更新时间范围和视图模式
const updateTimeRange = (range) => timeRange.value = range;
const updateViewMode = (mode) => viewMode.value = mode;

// 格式化百分比
const formatPercent = (value) => {
  if (value === null || value === undefined) return '-';
  return (value * 100).toFixed(2) + '%';
};

// 格式化数值
const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-';
  return parseFloat(value).toFixed(decimals);
};

// 添加用于解析形状的辅助函数
const getShapeDimension = (shapeStr, index) => {
  try {
    if (!shapeStr) return 10; // 默认值
    // 移除括号，并按逗号分割
    const shapeParts = shapeStr.replace(/[\(\)]/g, '').split(',');
    // 获取指定索引处的值（如果存在）
    return parseInt(shapeParts[index]) || 10;
  } catch (e) {
    return 10; // 默认值
  }
};

const formatShapeDimensions = (shapeStr) => {
  try {
    if (!shapeStr) return '';
    // 移除括号，并按逗号分割
    return shapeStr.replace(/[\(\)]/g, '').split(',').join(' × ');
  } catch (e) {
    return '';
  }
};

// 添加重试评测功能
const retryEvaluation = () => {
  loadVisualizationData();
};

// 加载文件信息
onMounted(() => {
  if (!dataFileId || !modelFileId) {
    ElMessage.error('缺少必要的参数');
    router.push('/my-files');
    return;
  }
  
  loadFileInfo();
});
</script>

<template>
  <AppLayout>
    <div class="visualization-container">
      <!-- 添加独立的返回按钮区域 -->
      <div class="back-button">
        <el-button @click="goBack" icon="ArrowLeft" size="small" text>返回文件列表</el-button>
      </div>
      
      <div class="page-header">
        <h1>模型预测可视化</h1>
        <div class="header-actions">
          <el-button type="primary" @click="downloadResults" :icon="Download">
            下载结果
          </el-button>
        </div>
      </div>
      
      <!-- 文件信息 -->
      <el-card v-if="dataFile && modelFile" class="file-info-card">
        <div class="file-info-grid">
          <div class="file-info-section">
            <h3>数据文件</h3>
            <div class="file-details">
              <p><strong>名称:</strong> {{ dataFile.name }}</p>
              <p><strong>格式:</strong> {{ dataFile.file_format }}</p>
              <p><strong>大小:</strong> {{ formatFileSize(dataFile.file_size) }}</p>
              <p><strong>上传时间:</strong> {{ formatDate(dataFile.upload_time) }}</p>
            </div>
          </div>
          
          <div class="file-info-section">
            <h3>模型文件</h3>
            <div class="file-details">
              <p><strong>名称:</strong> {{ modelFile.name }}</p>
              <p><strong>格式:</strong> {{ modelFile.file_format }}</p>
              <p><strong>大小:</strong> {{ formatFileSize(modelFile.file_size) }}</p>
              <p><strong>上传时间:</strong> {{ formatDate(modelFile.upload_time) }}</p>
            </div>
          </div>
        </div>
        
        <!-- 数据解释提示 -->
        <div class="data-interpretation-tips">
          <el-alert
            title="数据解释提示"
            type="info"
            :closable="false"
            show-icon
          >
            <div class="tips-content">
              <p>系统如何解释您的数据:</p>
              <ul>
                <li>若数据形状为 <code>(样本数, 时间点数)</code>，系统会选择第一个样本进行评测</li>
                <li>若数据形状为 <code>(通道数, 时间点数)</code>，系统会将其作为多通道EEG数据处理</li>
                <li>对于文件名包含 "EMG" 或 "epochs" 的数据，将视为样本集处理</li>
                <li>系统会根据模型类型 (fcNN/CNN) 自动调整数据形状，以确保兼容性</li>
              </ul>
            </div>
          </el-alert>
        </div>
        
        <!-- 模型兼容性提示 -->
        <div class="compatibility-tips">
          <el-alert
            title="模型兼容性提示"
            type="info"
            :closable="false"
            show-icon
          >
            <div class="tips-content">
              <p>为确保模型能正常加载，建议：</p>
              <ul>
                <li>使用标准Keras/TensorFlow层构建模型</li>
                <li>避免使用自定义层或损失函数</li>
                <li>使用 <code>model.save(path, save_format='h5', include_optimizer=False)</code> 保存模型</li>
              </ul>
            </div>
          </el-alert>
        </div>
      </el-card>
      
      <div v-if="isLoading" class="loading-placeholder">
        <el-icon class="loading-icon"><View /></el-icon>
        <p>正在加载分析结果，请稍候...</p>
      </div>
      
      <template v-else-if="originalData && processedData">
        <!-- 分析结果 -->
        <el-card class="analysis-card">
          <template #header>
            <div class="card-header">
              <h2>模型性能评测</h2>
              <el-tag type="success">模型类型: {{ modelFile.name }}</el-tag>
            </div>
          </template>
          
          <!-- 数据结构信息 -->
          <div class="data-structure-info" v-if="originalData">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="数据形状">
                {{ originalData.channels.length }} 通道 × {{ originalData.times.length }} 时间点
              </el-descriptions-item>
              <el-descriptions-item label="采样率">
                {{ originalData.sampling_rate || '-' }} Hz
              </el-descriptions-item>
              <el-descriptions-item label="评测样本">
                {{ originalData.channels.join(', ') }}
              </el-descriptions-item>
              <el-descriptions-item label="数据时长">
                {{ (originalData.duration || 0).toFixed(2) }} 秒
              </el-descriptions-item>
            </el-descriptions>
          </div>
          
          <div class="analysis-metrics">
            <div class="metrics-group">
              <h3>基础指标</h3>
              <div class="metrics-row">
                <div class="metric-item">
                  <h4>MSE</h4>
                  <div class="metric-value">{{ formatNumber(analysisResults.mse) }}</div>
                </div>
                <div class="metric-item">
                  <h4>MAE</h4>
                  <div class="metric-value">{{ formatNumber(analysisResults.mae) }}</div>
                </div>
                <div class="metric-item">
                  <h4>SNR</h4>
                  <div class="metric-value">{{ formatNumber(analysisResults.snr) }} dB</div>
                </div>
                <div class="metric-item">
                  <h4>SNR提升</h4>
                  <div class="metric-value">{{ formatNumber(analysisResults.snr_improvement) }} dB</div>
                </div>
              </div>
            </div>
            
            <div class="metrics-group">
              <h3>波形保真度指标</h3>
              <div class="metrics-row">
                <div class="metric-item">
                  <h4>Pearson相关系数</h4>
                  <div class="metric-value">{{ formatNumber(analysisResults.pearson) }}</div>
                </div>
                <div class="metric-item">
                  <h4>波形保真度</h4>
                  <div class="metric-value">{{ formatNumber(analysisResults.waveform_fidelity) }}</div>
                </div>
                <div class="metric-item">
                  <h4>准确率</h4>
                  <div class="metric-value">{{ formatPercent(analysisResults.accuracy) }}</div>
                </div>
                <div class="metric-item">
                  <h4>F1分数</h4>
                  <div class="metric-value">{{ formatPercent(analysisResults.f1_score) }}</div>
                </div>
              </div>
            </div>
            
            <div class="metrics-group">
              <div class="metrics-summary">
                <el-alert
                  title="模型评测结果"
                  type="success"
                  :closable="false"
                  description="模型对数据的降噪效果良好，适合应用于实际EEG数据"
                />
                <div class="processing-time">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>处理耗时: {{ analysisResults.elapsedTime }}秒</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 视图控制区域 -->
        <div class="view-controls">
          <el-radio-group v-model="viewMode" size="small" class="view-mode-selector">
            <el-radio-button label="time">时域</el-radio-button>
            <el-radio-button label="frequency">频域</el-radio-button>
          </el-radio-group>
          <span class="display-info">显示通道: {{ selectedChannels.length }}/{{ availableChannels.length }}</span>
        </div>
        
        <!-- 数据对比视图 -->
        <div class="compare-view">
          <div class="original-data">
            <h3>原始数据</h3>
            <EEGViewer 
              :data="originalData" 
              v-model:timeRange="timeRange"
              :selectedChannels="selectedChannels"
              :availableChannels="availableChannels"
              @update:timeRange="updateTimeRange"
              @update:selectedChannels="updateSelectedChannels"
              :viewMode="viewMode"
              @update:viewMode="updateViewMode"
            />
          </div>
          
          <div class="processed-data">
            <h3>模型降噪后数据</h3>
            <EEGViewer 
              :data="processedData" 
              v-model:timeRange="timeRange"
              :selectedChannels="selectedChannels"
              :availableChannels="availableChannels"
              @update:timeRange="updateTimeRange"
              @update:selectedChannels="updateSelectedChannels"
              :viewMode="viewMode"
              @update:viewMode="updateViewMode"
            />
          </div>
        </div>
      </template>
      
      <div v-else-if="!isLoading" class="empty-state">
        <el-empty description="暂无评测数据">
          <template #description>
            <p>暂无评测数据，请确保选择了有效的数据文件和模型</p>
          </template>
        </el-empty>
      </div>
      
      <!-- 错误状态展示 -->
      <div v-if="evaluationState === 'error'" class="error-container">
        <el-alert
          v-if="errorInfo && errorInfo.type === 'shape_mismatch'"
          title="模型形状不匹配"
          type="warning"
          :closable="false"
          show-icon
        >
          <div class="error-details">
            <p>模型的输入和输出形状与数据不匹配。这表明您的模型可能不适合处理此EEG数据。</p>
            
            <div class="shape-comparison" v-if="errorInfo.details">
              <h4>数据与模型形状比较:</h4>
              <div class="shape-item">
                <div class="shape-label">EEG数据形状:</div>
                <div class="shape-value">{{errorInfo.details.input_shape}}</div>
                <div class="shape-visualization">
                  <div class="shape-box" 
                       :style="{
                         width: `${Math.min(getShapeDimension(errorInfo.details.input_shape, 1) * 2, 500)}px`,
                         height: `${getShapeDimension(errorInfo.details.input_shape, 0) * 5}px`
                       }"
                  >
                    <div class="shape-text">数据</div>
                    <div class="shape-dimensions">
                      {{formatShapeDimensions(errorInfo.details.input_shape)}}
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="shape-item">
                <div class="shape-label">模型输出形状:</div>
                <div class="shape-value">{{errorInfo.details.output_shape}}</div>
                <div class="shape-visualization">
                  <div class="shape-box" 
                       :style="{
                         width: `${Math.min(getShapeDimension(errorInfo.details.output_shape, 1) * 2, 500)}px`,
                         height: `${getShapeDimension(errorInfo.details.output_shape, 0) * 5}px`,
                         backgroundColor: '#e6a23c'
                       }"
                  >
                    <div class="shape-text">模型输出</div>
                    <div class="shape-dimensions">
                      {{formatShapeDimensions(errorInfo.details.output_shape)}}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="error-actions">
              <el-button type="primary" @click="retryEvaluation">重试</el-button>
              <el-button @click="goBack">返回文件页面</el-button>
            </div>
          </div>
        </el-alert>
        
        <el-alert
          v-else-if="errorInfo && errorInfo.type === 'model_loading_error'"
          title="模型加载失败"
          type="error"
          :closable="false"
          show-icon
        >
          <div class="error-details">
            <p>无法加载模型文件。这可能是因为模型包含自定义层或使用了不兼容的TensorFlow版本。</p>
            <p class="error-message">错误详情: {{ errorInfo.message }}</p>
            
            <div class="error-info-box">
              <h4>推荐解决方案:</h4>
              <ul>
                <li>使用标准的TensorFlow/Keras层构建模型</li>
                <li>确保模型保存时使用 <code>model.save(filepath, save_format='h5')</code> 并设置 <code>include_optimizer=False</code></li>
                <li>使用常见的损失函数如 MSE、MAE 等，避免自定义损失函数</li>
                <li>如果模型中必须使用自定义层，请确保在保存时注册自定义层</li>
              </ul>
            </div>
            
            <div class="error-actions">
              <el-button type="primary" @click="retryEvaluation">重试</el-button>
              <el-button @click="goBack">返回文件页面</el-button>
            </div>
          </div>
        </el-alert>
        
        <el-alert
          v-else
          title="评测失败"
          type="error"
          :closable="false"
          show-icon
        >
          <div class="error-details">
            <p>评测模型时出现错误: {{ errorInfo?.message || '未知错误' }}</p>
            
            <div class="error-actions">
              <el-button type="primary" @click="retryEvaluation">重试</el-button>
              <el-button @click="goBack">返回文件页面</el-button>
            </div>
          </div>
        </el-alert>
      </div>
    </div>
  </AppLayout>
</template>

<style>
.visualization-container {
  padding: 0 20px 40px;
}

.back-button {
  margin-bottom: 10px;
  text-align: left;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.file-info-card {
  margin-bottom: 20px;
}

.file-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.file-info-section h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  color: #606266;
}

.file-details p {
  margin: 6px 0;
  font-size: 14px;
  color: #606266;
}

.analysis-card {
  margin-bottom: 20px;
}

.data-structure-info {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

/* 指标样式 */
.analysis-metrics {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metrics-group {
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  padding: 15px;
  background-color: #f9f9f9;
}

.metrics-group h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.metric-item {
  text-align: center;
  padding: 10px;
  border-radius: 4px;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.metric-item h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: normal;
  color: #606266;
}

.metric-value {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

.metrics-summary {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.processing-time {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
  margin-top: 10px;
}

/* 视图控制 */
.view-controls {
  display: flex;
  align-items: center;
  margin: 20px 0;
  gap: 10px;
}

.view-mode-selector {
  margin-right: 10px;
}

.display-info {
  font-size: 14px;
  color: #606266;
}

/* 对比视图样式 */
.compare-view {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.compare-view h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
}

.original-data, .processed-data {
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  padding: 15px;
  background-color: #fff;
}

/* 加载状态 */
.loading-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.loading-icon {
  font-size: 40px;
  color: #409EFF;
  animation: loading-rotate 2s linear infinite;
}

@keyframes loading-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  margin-top: 40px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .compare-view {
    grid-template-columns: 1fr;
  }
  
  .file-info-grid {
    grid-template-columns: 1fr;
  }
}

/* 错误状态样式 */
.error-container {
  margin: 20px 0;
}

.error-container .error-details {
  margin-top: 15px;
}

.error-container .error-details p {
  margin-bottom: 12px;
}

.error-container .error-details .error-message {
  background-color: #fde2e2;
  padding: 10px;
  border-radius: 4px;
  color: #F56C6C;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-container .error-details .error-info-box {
  background-color: #f5f7fa;
  border-left: 4px solid #409EFF;
  padding: 10px 15px;
  margin: 15px 0;
  border-radius: 0 4px 4px 0;
}

.error-container .error-details .error-info-box h4 {
  color: #409EFF;
  margin-top: 0;
  margin-bottom: 10px;
}

.error-container .error-details .error-info-box ul {
  margin: 0;
  padding-left: 20px;
}

.error-container .error-details .error-info-box li {
  margin-bottom: 8px;
}

.error-container .error-details .error-info-box code {
  background-color: #e6f1fc;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

.error-container .error-details .shape-comparison {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
}

.error-container .error-details .shape-comparison h4 {
  margin-bottom: 15px;
  font-weight: 600;
  color: #333;
}

.error-container .error-details .shape-comparison .shape-item {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.error-container .error-details .shape-comparison .shape-item .shape-label {
  font-weight: 600;
  margin-bottom: 5px;
}

.error-container .error-details .shape-comparison .shape-item .shape-value {
  font-family: monospace;
  background-color: #e9ecef;
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 10px;
}

.error-container .error-details .shape-comparison .shape-item .shape-visualization {
  margin-top: 5px;
}

.error-container .error-details .shape-comparison .shape-item .shape-visualization .shape-box {
  background-color: #409eff;
  border-radius: 4px;
  padding: 10px;
  color: white;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 100px;
  min-height: 50px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.error-container .error-details .shape-comparison .shape-item .shape-visualization .shape-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.error-container .error-details .shape-comparison .shape-item .shape-visualization .shape-box .shape-text {
  font-weight: bold;
  margin-bottom: 5px;
}

.error-container .error-details .shape-comparison .shape-item .shape-visualization .shape-box .shape-dimensions {
  font-size: 0.9em;
  opacity: 0.9;
}

.error-container .error-details .error-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.original-data-preview {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.original-data-preview h3 {
  margin-bottom: 15px;
  font-weight: 600;
}

.loading-container {
  padding: 30px;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin: 20px 0;
}

.compatibility-tips {
  margin-top: 15px;
}

.data-interpretation-tips {
  margin-top: 15px;
  margin-bottom: 15px;
}

.tips-content {
  padding: 5px 0;
}

.tips-content p {
  margin-bottom: 8px;
}

.tips-content ul {
  margin: 0;
  padding-left: 20px;
}

.tips-content li {
  margin-bottom: 5px;
}

.tips-content code {
  background-color: #f5f7fa;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
  color: #409EFF;
}
</style> 