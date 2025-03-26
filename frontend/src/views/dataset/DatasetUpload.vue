<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/AppLayout.vue';
import { UploadFilled } from '@element-plus/icons-vue';
import { useFormState } from '@/composables/useFormState';
import { useLoading } from '@/composables/useLoading';

const router = useRouter();

// 使用表单状态管理
const { formState: uploadForm, resetForm, clearSaved } = useFormState('dataset-upload-form', {
  name: '',
  description: '',
  license: 'CC0',
  authors: [],
  tags: []
});

const fileList = ref([]);
const { isLoading: loading, withLoading } = useLoading(false);
const newAuthor = ref('');
const newTag = ref('');

// 添加作者
const addAuthor = () => {
  if (newAuthor.value && !uploadForm.authors.includes(newAuthor.value)) {
    uploadForm.authors.push(newAuthor.value);
    newAuthor.value = '';
  }
};

// 移除作者
const removeAuthor = (author) => {
  const index = uploadForm.authors.indexOf(author);
  if (index !== -1) {
    uploadForm.authors.splice(index, 1);
  }
};

// 添加标签
const addTag = () => {
  if (newTag.value && !uploadForm.tags.includes(newTag.value)) {
    uploadForm.tags.push(newTag.value);
    newTag.value = '';
  }
};

// 移除标签
const removeTag = (tag) => {
  const index = uploadForm.tags.indexOf(tag);
  if (index !== -1) {
    uploadForm.tags.splice(index, 1);
  }
};

// 文件上传前的验证
const beforeUpload = (file) => {
  const isZip = file.type === 'application/zip' || 
                file.type === 'application/x-zip-compressed' ||
                file.name.endsWith('.zip');
  
  if (!isZip) {
    ElMessage.error('只能上传ZIP格式的文件!');
    return false;
  }
  
  const isLt2G = file.size / 1024 / 1024 / 1024 < 2;
  
  if (!isLt2G) {
    ElMessage.error('文件大小不能超过2GB!');
    return false;
  }
  
  return true;
};

// 文件上传成功的回调
const handleSuccess = (response) => {
  ElMessage.success('文件上传成功!');
  loading.value = false;
  router.push('/datasets');
};

// 文件上传失败的回调
const handleError = (error) => {
  console.error('上传失败:', error);
  ElMessage.error('文件上传失败，请重试!');
  loading.value = false;
};

// 提交表单
const submitForm = async () => {
  if (!uploadForm.name) {
    ElMessage.warning('请输入数据集名称!');
    return;
  }
  
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件!');
    return;
  }
  
  try {
    const formData = new FormData();
    formData.append('file', fileList.value[0].raw);
    formData.append('name', uploadForm.name);
    formData.append('description', uploadForm.description);
    formData.append('license', uploadForm.license);
    formData.append('authors', JSON.stringify(uploadForm.authors));
    formData.append('tags', JSON.stringify(uploadForm.tags));
    
    await withLoading(datasetService.uploadDataset(formData));
    
    ElMessage.success('数据集上传成功!');
    clearSaved(); // 清除保存的表单数据
    router.push('/datasets');
  } catch (error) {
    console.error('上传失败:', error);
    ElMessage.error('数据集上传失败，请重试!');
  }
};

// 重置表单
const resetUploadForm = () => {
  resetForm();
  fileList.value = [];
};

// 取消上传
const cancelUpload = () => {
  router.push('/datasets');
};
</script>

<template>
  <AppLayout>
    <div class="upload-container">
      <div class="page-header">
        <h1>上传数据集</h1>
        <p class="description">上传符合BIDS标准的EEG数据集，支持ZIP格式</p>
      </div>
      
      <el-card class="upload-card">
        <el-form :model="uploadForm" label-width="120px" label-position="top">
          <!-- 基本信息 -->
          <h2 class="section-title">基本信息</h2>
          
          <el-form-item label="数据集名称" required>
            <el-input v-model="uploadForm.name" placeholder="请输入数据集名称" />
          </el-form-item>
          
          <el-form-item label="数据集描述">
            <el-input 
              v-model="uploadForm.description" 
              type="textarea" 
              :rows="3" 
              placeholder="请输入数据集描述"
            />
          </el-form-item>
          
          <el-form-item label="许可证">
            <el-select v-model="uploadForm.license" style="width: 100%">
              <el-option label="CC0 (公共领域)" value="CC0" />
              <el-option label="CC-BY (署名)" value="CC-BY" />
              <el-option label="CC-BY-SA (署名-相同方式共享)" value="CC-BY-SA" />
              <el-option label="CC-BY-NC (署名-非商业性使用)" value="CC-BY-NC" />
              <el-option label="其他" value="OTHER" />
            </el-select>
          </el-form-item>
          
          <!-- 作者信息 -->
          <h2 class="section-title">作者信息</h2>
          
          <div class="author-input">
            <el-input 
              v-model="newAuthor" 
              placeholder="添加作者" 
              @keyup.enter="addAuthor"
            >
              <template #append>
                <el-button @click="addAuthor">添加</el-button>
              </template>
            </el-input>
          </div>
          
          <div class="tags-container" v-if="uploadForm.authors.length > 0">
            <el-tag
              v-for="author in uploadForm.authors"
              :key="author"
              closable
              @close="removeAuthor(author)"
              class="author-tag"
            >
              {{ author }}
            </el-tag>
          </div>
          
          <!-- 标签 -->
          <h2 class="section-title">标签</h2>
          
          <div class="tag-input">
            <el-input 
              v-model="newTag" 
              placeholder="添加标签" 
              @keyup.enter="addTag"
            >
              <template #append>
                <el-button @click="addTag">添加</el-button>
              </template>
            </el-input>
          </div>
          
          <div class="tags-container" v-if="uploadForm.tags.length > 0">
            <el-tag
              v-for="tag in uploadForm.tags"
              :key="tag"
              closable
              @close="removeTag(tag)"
              class="tag-item"
              type="info"
            >
              {{ tag }}
            </el-tag>
          </div>
          
          <!-- 文件上传 -->
          <h2 class="section-title">数据文件</h2>
          
          <el-upload
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :file-list="fileList"
            :on-change="(file, fileList) => fileList.value = fileList"
            :before-upload="beforeUpload"
            :limit="1"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                请上传符合BIDS标准的ZIP格式数据集文件，大小不超过2GB
              </div>
            </template>
          </el-upload>
          
          <!-- 提交按钮 -->
          <div class="form-actions">
            <el-button @click="cancelUpload">取消</el-button>
            <el-button 
              type="primary" 
              @click="submitForm" 
              :loading="loading"
            >
              上传数据集
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.upload-container {
  padding: 20px; /* 容器内边距 */
  max-width: 800px; /* 最大宽度 */
  margin: 0 auto; /* 居中显示 */
}

.page-header {
  margin-bottom: 24px; /* 页头下方间距 */
}

.page-header h1 {
  font-size: 24px; /* 标题字体大小 */
  font-weight: 600; /* 标题字体粗细 */
  margin-bottom: 8px; /* 标题下方间距 */
}

.description {
  color: #606266; /* 描述文字颜色 */
  font-size: 14px; /* 描述文字大小 */
}

.upload-card {
  border-radius: 8px; /* 卡片圆角 */
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); /* 卡片阴影 */
}

.section-title {
  font-size: 18px; /* 分节标题字体大小 */
  font-weight: 600; /* 分节标题字体粗细 */
  margin: 24px 0 16px 0; /* 分节标题上下间距 */
  color: #303133; /* 分节标题颜色 */
}

.author-input, .tag-input {
  margin-bottom: 16px; /* 输入框下方间距 */
}

.tags-container {
  display: flex;
  flex-wrap: wrap; /* 允许标签换行 */
  gap: 8px; /* 标签间距 */
  margin-bottom: 24px; /* 标签容器下方间距 */
}

.author-tag, .tag-item {
  margin-right: 8px; /* 标签右侧间距 */
  margin-bottom: 8px; /* 标签下方间距 */
}

.form-actions {
  display: flex;
  justify-content: flex-end; /* 按钮右对齐 */
  margin-top: 32px; /* 按钮上方间距 */
  gap: 16px; /* 按钮间距 */
}

.upload-demo {
  margin-top: 16px; /* 上传区域上方间距 */
}

.el-upload__tip {
  line-height: 1.5; /* 提示文字行高 */
  margin-top: 8px; /* 提示文字上方间距 */
}
</style> 