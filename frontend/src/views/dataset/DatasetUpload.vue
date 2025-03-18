<script setup>
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/AppLayout.vue';

const router = useRouter();
const uploadForm = reactive({
  name: '',
  description: '',
  license: 'CC0',
  authors: [],
  tags: []
});
const fileList = ref([]);
const loading = ref(false);
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
    ElMessage.warning('请输入数据集名称');
    return;
  }
  
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件');
    return;
  }
  
  loading.value = true;
  
  try {
    const formData = new FormData();
    formData.append('file', fileList.value[0].raw);
    formData.append('name', uploadForm.name);
    formData.append('description', uploadForm.description);
    formData.append('license', uploadForm.license);
    formData.append('authors', JSON.stringify(uploadForm.authors));
    formData.append('tags', JSON.stringify(uploadForm.tags));
    
    const response = await datasetService.uploadDataset(formData);
    
    ElMessage.success('数据集上传成功!');
    router.push('/datasets');
  } catch (error) {
    console.error('上传失败:', error);
    ElMessage.error('数据集上传失败，请重试!');
  } finally {
    loading.value = false;
  }
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
  padding: 20px;
  max-width: 800px;
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
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.author-input, .tag-input {
  margin-bottom: 16px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.author-tag, .tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
  gap: 12px;
}

.upload-demo {
  width: 100%;
}
</style> 