<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import AppLayout from '../../components/layout/AppLayout.vue';

// 用户信息
const userInfo = ref({
  username: '',
  email: '',
  avatar: '',
  organization: '',
  position: '',
  bio: ''
});

// 表单是否被修改
const formChanged = ref(false);

// 从本地存储加载用户信息
onMounted(() => {
  const storedUser = localStorage.getItem('userInfo');
  if (storedUser) {
    try {
      userInfo.value = JSON.parse(storedUser);
    } catch (e) {
      console.error('解析用户信息失败', e);
    }
  }
  
  // 如果没有用户名，设置一个默认值
  if (!userInfo.value.username) {
    userInfo.value.username = '用户' + Math.floor(Math.random() * 10000);
    saveUserInfo();
  }
});

// 监听表单变化
const handleFormChange = () => {
  formChanged.value = true;
};

// 保存用户信息
const saveUserInfo = () => {
  localStorage.setItem('userInfo', JSON.stringify(userInfo.value));
  formChanged.value = false;
  ElMessage.success('个人资料已更新');
};

// 上传头像
const handleAvatarSuccess = (res) => {
  if (res && res.url) {
    userInfo.value.avatar = res.url;
    formChanged.value = true;
  }
};

// 模拟上传头像
const uploadAvatar = (file) => {
  // 在实际项目中，这里应该调用API上传文件
  // 这里我们使用FileReader读取文件并转为base64存储
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = () => {
    userInfo.value.avatar = reader.result;
    formChanged.value = true;
    ElMessage.success('头像已更新');
  };
  return false; // 阻止自动上传
};
</script>

<template>
  <AppLayout>
    <div class="profile-container">
      <div class="profile-header">
        <h1 class="page-title">个人资料</h1>
        <el-button 
          type="primary" 
          @click="saveUserInfo" 
          :disabled="!formChanged"
        >
          保存更改
        </el-button>
      </div>
      
      <el-card class="profile-card">
        <el-form 
          label-position="top" 
          :model="userInfo" 
          @change="handleFormChange"
        >
          <div class="profile-layout">
            <!-- 左侧：头像上传 -->
            <div class="avatar-section">
              <el-upload
                class="avatar-uploader"
                action="#"
                :show-file-list="false"
                :before-upload="uploadAvatar"
              >
                <img 
                  v-if="userInfo.avatar" 
                  :src="userInfo.avatar" 
                  class="avatar" 
                  alt="用户头像"
                />
                <el-icon v-else class="avatar-uploader-icon">
                  <Plus />
                </el-icon>
              </el-upload>
              <div class="avatar-hint">点击上传头像</div>
            </div>
            
            <!-- 右侧：用户信息表单 -->
            <div class="form-section">
              <el-form-item label="用户名">
                <el-input 
                  v-model="userInfo.username" 
                  placeholder="请输入用户名"
                  @input="handleFormChange"
                />
              </el-form-item>
              
              <el-form-item label="邮箱">
                <el-input 
                  v-model="userInfo.email" 
                  placeholder="请输入邮箱"
                  @input="handleFormChange"
                />
              </el-form-item>
              
              <el-form-item label="组织/单位">
                <el-input 
                  v-model="userInfo.organization" 
                  placeholder="请输入组织或单位名称"
                  @input="handleFormChange"
                />
              </el-form-item>
              
              <el-form-item label="职位">
                <el-input 
                  v-model="userInfo.position" 
                  placeholder="请输入您的职位"
                  @input="handleFormChange"
                />
              </el-form-item>
              
              <el-form-item label="个人简介">
                <el-input 
                  v-model="userInfo.bio" 
                  type="textarea" 
                  :rows="4"
                  placeholder="请输入个人简介"
                  @input="handleFormChange"
                />
              </el-form-item>
            </div>
          </div>
        </el-form>
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.profile-card {
  margin-bottom: 20px;
}

.profile-layout {
  display: flex;
  gap: 30px;
}

.avatar-section {
  width: 200px;
}

.form-section {
  flex: 1;
}

.avatar-uploader {
  width: 150px;
  height: 150px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: border-color 0.3s;
}

.avatar-uploader:hover {
  border-color: var(--button-use);
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 150px;
  height: 150px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-hint {
  text-align: center;
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .profile-layout {
    flex-direction: column;
  }
  
  .avatar-section {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 20px;
  }
}
</style> 