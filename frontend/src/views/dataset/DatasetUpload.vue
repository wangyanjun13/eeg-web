<script setup>
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
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
      ElMessage.error('文件大小不能超过100MB!');
      return false;
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
      ElMessage.error('模型文件大小不能超过500MB!');
      return false;
    }
  }
  
  // 保存选中的文件
  selectedFile.value = file;
  console.log('文件通过验证，已保存:', selectedFile.value.name);
  return true;
};

// 处理文件变更
const handleFileChange = (file) => {
  console.log('文件变更:', file);
  if (file.raw) {
    selectedFile.value = file.raw;
    console.log('已选择文件:', selectedFile.value.name);
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
        console.log(`${key}: [File 对象]`);
      }
    }
    
    const response = await withLoading(datasetService.uploadDataset(formData));
    console.log('上传成功，响应:', response);
    
    ElMessage.success('文件上传成功!');
    clearSaved(); // 清除保存的表单数据
    selectedFile.value = null; // 清除已选文件
    fileList.value = []; // 清除文件列表
    
    // 跳转到我的文件页面
    router.push('/my-files?refresh=true');
  } catch (error) {
    console.error('上传失败:', error);
    ElMessage.error('文件上传失败，请重试!');
  }
};

// 重置表单
const resetUploadForm = () => {
  resetForm();
  fileList.value = [];
};

// 取消上传
const cancelUpload = () => {
  router.push('/my-files');
};
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
            <el-radio-group v-model="uploadForm.fileType">
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
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip" v-if="uploadForm.fileType === 'data'">
                  支持的数据格式：.set, .fdt, .mat, .npy，大小不超过100MB
                </div>
                <div class="el-upload__tip" v-else>
                  支持的模型格式：.h5 (TensorFlow/Keras模型)，大小不超过500MB
                </div>
              </template>
            </el-upload>
            
            <!-- 显示已选文件 -->
            <div v-if="selectedFile" class="selected-file">
              <p>已选择文件: {{ selectedFile.name }} ({{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB)</p>
            </div>
          </el-form-item>
          
          <!-- 提交按钮 -->
          <el-form-item>
            <el-button @click="cancelUpload">取消</el-button>
            <el-button @click="resetUploadForm">重置</el-button>
            <el-button 
              type="primary" 
              @click="submitForm" 
              :loading="loading"
            >
              上传文件
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
  color: #67c23a;
}
</style> 