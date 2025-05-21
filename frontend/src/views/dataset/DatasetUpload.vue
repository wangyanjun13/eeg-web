<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/layout/AppLayout.vue';
import { UploadFilled } from '@element-plus/icons-vue';
import { useFormState } from '@/composables/useFormState';
import { useLoading } from '@/composables/useLoading';

const router = useRouter();

// 使用表单状态管理
const { formState: uploadForm, resetForm, clearSaved } = useFormState('file-upload-form', {
  name: '',
  description: '',
  fileType: 'data', // 默认为数据文件上传
});

// 简化：使用单个文件引用
const selectedFile = ref(null);
const fileList = ref([]);
const { isLoading: loading, withLoading } = useLoading(false);

// 文件类型错误提示
const fileTypeError = ref(null);

// 上传进度相关
const uploadProgress = ref(0);
const showProgress = ref(false);
const uploadStatus = ref('');

// 上传超时警告相关
const uploadTimeoutWarning = ref(false);
const uploadTimeoutTimer = ref(null);
const UPLOAD_TIMEOUT_WARNING_DELAY = 30000; // 30秒后显示警告
const UPLOAD_MAX_RETRY = 3; // 最大重试次数
const uploadRetryCount = ref(0);
const chunkSize = ref(1024 * 1024 * 5); // 5MB 分块大小

// 上传错误处理
const uploadError = ref(null);
const isRetrying = ref(false);
const lastProgressUpdate = ref(Date.now());
const progressStalled = ref(false);

// 在组件卸载前清除定时器
onBeforeUnmount(() => {
  clearAllTimers();
});

// 清除所有定时器
const clearAllTimers = () => {
  if (uploadTimeoutTimer.value) {
    clearTimeout(uploadTimeoutTimer.value);
    uploadTimeoutTimer.value = null;
  }
};

// 验证文件类型是否匹配
const validateFileType = () => {
  if (!selectedFile.value) return true;
  
  const fileExtension = selectedFile.value.name.substring(selectedFile.value.name.lastIndexOf('.')).toLowerCase();
  
  if (uploadForm.fileType === 'data') {
    // 数据文件验证 (.set, .fdt, .mat, .npy)
    const validExtensions = ['.set', '.fdt', '.mat', '.npy'];
    if (!validExtensions.includes(fileExtension)) {
      fileTypeError.value = `您选择了数据文件类型，但上传的是 ${fileExtension} 格式文件。数据文件必须是 .set, .fdt, .mat 或 .npy 格式!`;
      return false;
    }
  } else {
    // 模型文件验证 (.h5)
    if (fileExtension !== '.h5') {
      fileTypeError.value = `您选择了模型文件类型，但上传的是 ${fileExtension} 格式文件。模型文件必须是 .h5 格式!`;
      return false;
    }
  }
  
  fileTypeError.value = null;
  return true;
};

// 文件上传前的验证
const beforeUpload = (file) => {
  console.log('验证文件:', file.name);
  
  if (uploadForm.fileType === 'data') {
    // 数据文件验证 (.set, .fdt, .mat, .npy)
    const validExtensions = ['.set', '.fdt', '.mat', '.npy'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
      ElMessage.error('数据文件必须是 .set, .fdt, .mat 或 .npy 格式!');
      return false;
    }
    
    // 文件大小限制：100MB
    const isLt100M = file.size / 1024 / 1024 < 100;
    if (!isLt100M) {
      ElMessage.warning('文件大小超过100MB，上传可能需要较长时间，请耐心等待');
      // 对于大文件，我们增加分块大小以提高效率
      chunkSize.value = 1024 * 1024 * 10; // 10MB
    }
  } else {
    // 模型文件验证 (.h5)
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (fileExtension !== '.h5') {
      ElMessage.error('模型文件必须是 .h5 格式!');
      return false;
    }
    
    // 文件大小限制：500MB
    const isLt500M = file.size / 1024 / 1024 < 500;
    if (!isLt500M) {
      ElMessage.warning('模型文件大小超过500MB，上传可能需要较长时间，请耐心等待');
      // 对于大文件，我们增加分块大小以提高效率
      chunkSize.value = 1024 * 1024 * 20; // 20MB
    }
  }
  
  // 保存选中的文件
  selectedFile.value = file;
  console.log('文件通过验证，已保存:', selectedFile.value.name);
  
  // 验证文件类型是否匹配
  validateFileType();
  
  return true;
};

// 处理文件变更
const handleFileChange = (file) => {
  console.log('文件变更:', file);
  if (file.raw) {
    selectedFile.value = file.raw;
    console.log('已选择文件:', selectedFile.value.name);
    
    // 验证文件类型是否匹配
    validateFileType();
  }
};

// 监听文件类型变更
const handleFileTypeChange = () => {
  // 如果已经选择了文件，验证文件类型是否匹配
  if (selectedFile.value) {
    validateFileType();
  }
};

// 处理上传进度
const handleUploadProgress = (percent) => {
  // 更新最后进度更新时间
  lastProgressUpdate.value = Date.now();
  
  // 重置进度停滞标志
  progressStalled.value = false;
  
  // 更新进度
  uploadProgress.value = percent;
  console.log(`上传进度: ${percent}%`);
  
  // 如果进度更新，重置超时警告定时器
  if (uploadTimeoutTimer.value) {
    clearTimeout(uploadTimeoutTimer.value);
  }
  
  // 如果上传未完成，设置新的超时警告定时器
  if (percent < 100) {
    uploadTimeoutTimer.value = setTimeout(() => {
      uploadTimeoutWarning.value = true;
      
      // 检查进度是否长时间未更新
      const now = Date.now();
      if (now - lastProgressUpdate.value > 30000) { // 30秒无进度更新
        progressStalled.value = true;
        ElMessage.warning('上传进度已停滞较长时间，可能遇到网络问题。您可以尝试刷新页面重新上传。');
      } else {
        ElMessage.warning('文件上传时间较长，请耐心等待。如果长时间无响应，可以尝试刷新页面重新上传。');
      }
    }, UPLOAD_TIMEOUT_WARNING_DELAY);
  } else if (percent === 100) {
    // 上传完成，清除定时器
    clearAllTimers();
    uploadTimeoutWarning.value = false;
  }
};

// 提交表单
const submitForm = async () => {
  console.log('开始提交表单');
  
  if (!uploadForm.name) {
    ElMessage.warning('请输入文件名称!');
    return;
  }
  
  console.log('选中的文件:', selectedFile.value);
  
  if (!selectedFile.value) {
    ElMessage.warning('请选择要上传的文件!');
    return;
  }
  
  // 验证文件类型是否匹配
  if (!validateFileType()) {
    ElMessage.error(fileTypeError.value);
    return;
  }
  
  try {
    // 重置状态
    uploadProgress.value = 0;
    showProgress.value = true;
    uploadStatus.value = '准备上传...';
    uploadRetryCount.value = 0;
    uploadError.value = null;
    isRetrying.value = false;
    progressStalled.value = false;
    lastProgressUpdate.value = Date.now();
    
    // 清除之前的超时警告
    clearAllTimers();
    
    // 设置新的超时警告定时器
    uploadTimeoutTimer.value = setTimeout(() => {
      uploadTimeoutWarning.value = true;
      ElMessage.warning('文件上传时间较长，请耐心等待。如果长时间无响应，可以尝试刷新页面重新上传。');
    }, UPLOAD_TIMEOUT_WARNING_DELAY);
    
    // 添加进度监控定时器 - 每10秒检查一次进度是否停滞
    const progressMonitor = setInterval(() => {
      const now = Date.now();
      if (now - lastProgressUpdate.value > 20000 && uploadProgress.value > 0 && uploadProgress.value < 100) {
        progressStalled.value = true;
        ElMessage.warning('上传进度已停滞较长时间，可能遇到网络问题。您可以继续等待或刷新页面重新上传。');
      }
    }, 10000);
    
    try {
      await uploadFile();
      
      // 清除进度监控
      clearInterval(progressMonitor);
    } catch (error) {
      // 清除进度监控
      clearInterval(progressMonitor);
      throw error;
    }
    
  } catch (error) {
    console.error('上传失败:', error);
    uploadStatus.value = '上传失败';
    loading.value = false;
    uploadError.value = error.message || '未知错误';
    
    // 清除超时警告定时器
    clearAllTimers();
    
    // 根据错误类型提供更详细的错误信息
    let errorMessage = '文件上传失败，请重试!';
    
    if (error.message) {
      if (error.message.includes('HTTP/2') || error.message.includes('PROTOCOL_ERROR')) {
        errorMessage = '文件上传失败：HTTP/2 协议错误。请尝试以下解决方法：\n1. 减小文件大小\n2. 使用其他浏览器\n3. 稍后再试';
        uploadStatus.value = 'HTTP/2 协议错误';
      } else if (error.message.includes('timeout')) {
        errorMessage = '上传超时，请尝试使用更小的文件或检查网络连接';
      } else if (error.message.includes('413')) {
        errorMessage = '文件太大，超出服务器接收限制';
      } else if (error.message.includes('Network Error')) {
        errorMessage = '网络错误，请检查您的网络连接';
      }
    }
    
    ElMessage.error(errorMessage);
    
    // 如果是 HTTP/2 协议错误，显示更详细的提示
    if (uploadStatus.value === 'HTTP/2 协议错误') {
      ElMessageBox.alert(
        '上传大文件时遇到 HTTP/2 协议错误。这是浏览器与服务器通信时的一个已知问题。\n\n' +
        '您可以尝试以下解决方法：\n' +
        '1. 减小文件大小（可能需要拆分文件）\n' +
        '2. 使用其他浏览器（如 Firefox 或 Edge）\n' +
        '3. 使用其他网络连接尝试上传\n' +
        '4. 稍后再试',
        'HTTP/2 协议错误',
        {
          confirmButtonText: '我知道了',
          type: 'warning'
        }
      );
    }
    
    // 延迟一小段时间后隐藏进度条
    setTimeout(() => {
      showProgress.value = false;
    }, 3000);
  }
};

// 上传文件，支持重试机制
const uploadFile = async () => {
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('name', uploadForm.name);
    formData.append('description', uploadForm.description);
    formData.append('file_type', uploadForm.fileType);
    
    // 自动获取文件格式
    const fileName = selectedFile.value.name;
    const fileExtension = fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase();
    formData.append('file_format', fileExtension);
    
    // 打印FormData内容（调试用）
    console.log('FormData已准备:');
    for (let [key, value] of formData.entries()) {
      if (key !== 'file') {
        console.log(`${key}: ${value}`);
      } else {
        console.log(`${key}: [File 对象], 大小: ${value.size} 字节`);
      }
    }
    
    // 使用带进度监控的上传方法
    uploadStatus.value = '上传中...';
    loading.value = true;
    
    // 注册进度回调
    const progressCallback = (percent) => {
      handleUploadProgress(percent);
      
      // 如果进度为100%，更新状态
      if (percent === 100) {
        uploadStatus.value = '处理中...';
      }
    };
    
    // 模拟进度更新 - 在网络慢或服务器未返回进度时提供视觉反馈
    let simulatedProgress = 0;
    const progressSimulator = setInterval(() => {
      // 只有在实际进度未更新时才模拟进度
      if (Date.now() - lastProgressUpdate.value > 3000 && uploadProgress.value < 95) {
        // 缓慢增加模拟进度，但不超过95%
        simulatedProgress = Math.min(95, simulatedProgress + 0.5);
        if (simulatedProgress > uploadProgress.value) {
          console.log(`模拟进度更新: ${simulatedProgress}%`);
          progressCallback(simulatedProgress);
        }
      }
    }, 2000);
    
    try {
      // 执行上传
      const response = await datasetService.uploadDataset(formData, progressCallback);
      console.log('上传成功，响应:', response);
      
      // 清除模拟进度
      clearInterval(progressSimulator);
      
      // 确保进度显示100%
      progressCallback(100);
      
      // 清除超时警告定时器
      clearAllTimers();
      uploadTimeoutWarning.value = false;
      
      uploadStatus.value = '上传完成';
      loading.value = false;
      ElMessage.success('文件上传成功!');
      clearSaved(); // 清除保存的表单数据
      selectedFile.value = null; // 清除已选文件
      fileList.value = []; // 清除文件列表
      
      // 延迟一小段时间后隐藏进度条
      setTimeout(() => {
        showProgress.value = false;
      }, 1000);
      
      // 跳转到我的文件页面
      router.push('/my-files?refresh=true');
    } catch (error) {
      // 清除模拟进度
      clearInterval(progressSimulator);
      
      // 检查是否可以重试
      if (uploadRetryCount.value < UPLOAD_MAX_RETRY) {
        uploadRetryCount.value++;
        console.log(`上传失败，正在尝试第 ${uploadRetryCount.value} 次重试...`);
        uploadStatus.value = `上传失败，正在重试 (${uploadRetryCount.value}/${UPLOAD_MAX_RETRY})...`;
        isRetrying.value = true;
        
        // 等待一段时间后重试
        await new Promise(resolve => setTimeout(resolve, 2000));
        isRetrying.value = false;
        return uploadFile(); // 递归调用自身重试
      }
      
      // 超过最大重试次数，抛出错误
      throw error;
    }
  } catch (error) {
    // 超过最大重试次数，抛出错误
    throw error;
  }
};

// 重置表单
const resetUploadForm = () => {
  resetForm();
  fileList.value = [];
  showProgress.value = false;
  uploadProgress.value = 0;
  uploadError.value = null;
  
  // 清除超时警告定时器
  clearAllTimers();
  uploadTimeoutWarning.value = false;
};

// 取消上传
const cancelUpload = () => {
  // 如果正在上传，显示确认对话框
  if (loading.value) {
    ElMessageBox.confirm('确定要取消当前上传吗？', '取消上传', {
      confirmButtonText: '确定',
      cancelButtonText: '继续上传',
      type: 'warning'
    }).then(() => {
      // 尝试取消上传请求
      datasetService.cancelUpload();
      
      // 清除超时警告定时器
      clearAllTimers();
      loading.value = false;
      showProgress.value = false;
      router.push('/my-files');
    }).catch(() => {
      // 用户选择继续上传，不做任何操作
    });
  } else {
    router.push('/my-files');
  }
};

// 计算上传文件类型的显示名称
const fileTypeDisplay = computed(() => {
  return uploadForm.fileType === 'data' ? '数据文件' : '模型文件';
});

// 计算进度条状态
const progressStatus = computed(() => {
  if (uploadProgress.value === 100) return 'success';
  if (uploadError.value) return 'exception';
  if (progressStalled.value) return 'warning';
  return '';
});

// 计算上传按钮文本
const uploadButtonText = computed(() => {
  if (loading.value) {
    if (isRetrying.value) {
      return `重试中 (${uploadRetryCount.value}/${UPLOAD_MAX_RETRY})`;
    }
    return `上传中 (${uploadProgress.value}%)`;
  }
  return `上传${fileTypeDisplay.value}`;
});

// 计算进度提示文本
const progressTipText = computed(() => {
  if (uploadProgress.value < 100) {
    if (progressStalled.value) {
      return '上传进度已停滞，可能遇到网络问题，请耐心等待或刷新页面重试...';
    }
    return '上传大文件可能需要较长时间，请耐心等待...';
  } else {
    return '文件上传完成，正在处理...';
  }
});
</script>

<template>
  <AppLayout>
    <div class="upload-container">
      <div class="page-header">
        <h1>上传文件</h1>
        <p class="description">上传脑电数据文件或模型文件</p>
      </div>
      
      <el-card class="upload-card">
        <el-form :model="uploadForm" label-width="100px">
          <!-- 文件类型选择 -->
          <el-form-item label="文件类型">
            <el-radio-group v-model="uploadForm.fileType" @change="handleFileTypeChange">
              <el-radio value="data">数据文件</el-radio>
              <el-radio value="model">模型文件</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <!-- 文件名称 -->
          <el-form-item label="名称" required>
            <el-input v-model="uploadForm.name" :placeholder="uploadForm.fileType === 'data' ? '请输入数据文件名称' : '请输入模型名称'" />
          </el-form-item>
          
          <!-- 文件描述 -->
          <el-form-item label="描述">
            <el-input 
              v-model="uploadForm.description" 
              type="textarea" 
              :rows="3" 
              :placeholder="uploadForm.fileType === 'data' ? '请描述数据文件内容' : '请描述模型功能和适用场景'"
            />
          </el-form-item>
          
          <!-- 文件上传 -->
          <el-form-item label="文件">
            <el-upload
              class="upload-demo"
              drag
              action="#"
              :auto-upload="false"
              :file-list="fileList"
              :on-change="(file) => handleFileChange(file)"
              :before-upload="beforeUpload"
              :limit="1"
              :disabled="loading"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip" v-if="uploadForm.fileType === 'data'">
                  支持的数据格式：.set, .fdt, .mat, .npy，建议大小不超过100MB
                </div>
                <div class="el-upload__tip" v-else>
                  支持的模型格式：.h5 (TensorFlow/Keras模型)，建议大小不超过500MB
                </div>
              </template>
            </el-upload>
            
            <!-- 显示已选文件 -->
            <div v-if="selectedFile" class="selected-file" :class="{ 'file-type-error': fileTypeError }">
              <p>已选择文件: {{ selectedFile.name }} ({{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB)</p>
              <!-- 文件类型错误提示 -->
              <p v-if="fileTypeError" class="file-type-error-message">{{ fileTypeError }}</p>
            </div>
            
            <!-- 上传进度条 -->
            <div v-if="showProgress" class="upload-progress">
              <p class="progress-status">{{ uploadStatus }} ({{ uploadProgress }}%)</p>
              <el-progress 
                :percentage="uploadProgress" 
                :status="progressStatus"
                :stroke-width="10"
                :show-text="false"
              />
              <p class="progress-tip" :class="{ 'warning': uploadTimeoutWarning || progressStalled, 'error': uploadError }">
                {{ progressTipText }}
              </p>
              
              <!-- 错误信息 -->
              <div v-if="uploadError" class="upload-error">
                <p>错误: {{ uploadError }}</p>
                <p>请尝试刷新页面或减小文件大小后重试</p>
              </div>
            </div>
          </el-form-item>
          
          <!-- 提交按钮 -->
          <el-form-item>
            <el-button @click="cancelUpload" :disabled="loading && uploadProgress < 95">取消</el-button>
            <el-button @click="resetUploadForm" :disabled="loading">重置</el-button>
            <el-button 
              type="primary" 
              @click="submitForm" 
              :loading="loading"
              :disabled="showProgress && uploadProgress < 100"
            >
              {{ uploadButtonText }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.upload-container {
  padding: 0;
  max-width: 700px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.description {
  color: #606266;
  font-size: 14px;
}

.upload-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.upload-demo {
  width: 100%;
}

.el-upload__tip {
  line-height: 1.5;
  margin-top: 8px;
}

/* 已选文件样式 */
.selected-file {
  margin-top: 12px;
  padding: 8px 12px;
  background-color: #f0f9eb;
  border: 1px solid #e1f3d8;
  border-radius: 4px;
  color: var(--success-color);
}

/* 上传进度条样式 */
.upload-progress {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px;
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.progress-status {
  margin: 0 0 8px;
  font-size: 14px;
  color: #606266;
}

.progress-tip {
  margin: 8px 0 0;
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

.progress-tip.warning {
  color: #e6a23c;
  font-weight: bold;
}

.progress-tip.error {
  color: #f56c6c;
  font-weight: bold;
}

.upload-error {
  margin-top: 10px;
  padding: 8px 12px;
  background-color: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 4px;
  color: #f56c6c;
}

/* 文件类型错误提示样式 */
.file-type-error {
  border-color: #f56c6c;
}

.file-type-error-message {
  margin-top: 8px;
  color: #f56c6c;
  font-size: 12px;
}
</style> 