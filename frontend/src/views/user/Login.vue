<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

// 路由实例
const router = useRouter();

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  remember: false
});

// 表单校验规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
};

// 表单引用
const formRef = ref(null);

// 加载状态
const loading = ref(false);

// 预定义的账号列表
const predefinedAccounts = [
  { username: 'admin', password: 'admin123', role: 'admin', displayName: '管理员' },
  { username: 'user', password: 'user123', role: 'user', displayName: '普通用户' },
  { username: 'guest', password: 'guest123', role: 'guest', displayName: '访客' }
];

// 登录处理
const handleLogin = () => {
  if (!formRef.value) return;
  
  formRef.value.validate((valid) => {
    if (valid) {
      loading.value = true;
      
      // 模拟登录请求延迟
      setTimeout(() => {
        // 在预定义账号中查找匹配的账号
        const account = predefinedAccounts.find(
          acc => acc.username === loginForm.username && acc.password === loginForm.password
        );
        
        if (account) {
          // 登录成功
          const userInfo = {
            username: account.displayName,
            role: account.role,
            isLoggedIn: true,
            lastLogin: new Date().toISOString()
          };
          
          // 保存用户信息到本地存储
          localStorage.setItem('userInfo', JSON.stringify(userInfo));
          
          // 如果选择了记住密码，保存登录凭证
          if (loginForm.remember) {
            localStorage.setItem('loginCredentials', JSON.stringify({
              username: loginForm.username,
              remember: true
            }));
          } else {
            // 清除之前保存的登录凭证
            localStorage.removeItem('loginCredentials');
          }
          
          // 记录访问量
          try {
            fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/datasets/record-visit`);
          } catch (e) {
            console.error('记录访问量失败', e);
          }
          
          ElMessage.success('登录成功');  
          
          // 跳转到首页
          router.push('/');
        } else {
          // 登录失败
          ElMessage.error('用户名或密码错误');
        }
        
        loading.value = false;
      }, 800);
    } else {
      return false;
    }
  });
};

// 加载保存的登录凭证
const loadSavedCredentials = () => {
  const savedCredentials = localStorage.getItem('loginCredentials');
  if (savedCredentials) {
    try {
      const credentials = JSON.parse(savedCredentials);
      loginForm.username = credentials.username || '';
      loginForm.remember = credentials.remember || false;
    } catch (e) {
      console.error('解析保存的登录凭证失败', e);
    }
  }
};

// 初始化时加载保存的登录凭证
loadSavedCredentials();
</script>

<template>
  <div class="login-container">
    <div class="login-content">
      <!-- 登录页顶部 -->
      <div class="login-header">
        <div class="logo-container">
          <img src="@/assets/eeg-logo.svg" alt="Logo" class="logo" />
          <h1 class="title">EEG数据分析交互式可视化平台</h1>
        </div>
        <p class="subtitle">脑电数据分析与模型评测系统</p>
      </div>
      
      <!-- 登录表单 -->
      <el-card class="login-card">
        <template #header>
          <div class="card-header">
            <h2>用户登录</h2>
          </div>
        </template>
        
        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          label-position="top"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              clearable
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              clearable
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <el-form-item>
            <div class="form-options">
              <el-checkbox v-model="loginForm.remember">记住用户名</el-checkbox>
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="login-button"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-tips">
          <p>系统登录说明：</p>
          <p>- 请使用管理员提供的账号密码登录</p>
          <p>- 如需账号，请联系系统管理员</p>
        </div>
      </el-card>
      
      <!-- 页脚信息 -->
      <div class="login-footer">
        <p>© {{ new Date().getFullYear() }} EEG数据分析交互式可视化平台 版权所有</p>
        <div class="developer-contact">
          <span>联系开发者/管理员：</span>
          <a href="mailto:wangyanjun13@foxmail.com">wangyanjun13@foxmail.com</a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  /* 添加背景图片 - 您可以替换为自己的图片 */
  background-image: url('@/assets/back2.png'); /* 请将图片放在 public 文件夹中 */
  background-size: cover;
  background-position: center;
  position: relative;
  overflow: hidden;
}

/* 背景遮罩，提高可读性 */
.login-container::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(202, 226, 254, 0.75); /* 半透明背景 */
  backdrop-filter: blur(5px); /* 毛玻璃效果 */
  z-index: 0;
}

.login-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 420px;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  width: 100%;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.logo {
  width: 50px;
  height: 50px;
  margin-right: 10px;
}

.title {
  font-size: 24px;
  color: #303133;
  margin: 0;
}

.subtitle {
  font-size: 16px;
  color: #606266;
  margin: 10px 0 0;
}

.login-card {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.login-button {
  width: 100%;
  padding: 12px 0;
  font-size: 16px;
}

.login-tips {
  margin-top: 20px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.login-tips p {
  margin: 5px 0;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  color: #606266;
  font-size: 12px;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 10px 20px;
  border-radius: 20px;
  backdrop-filter: blur(5px);
}

/* 开发者联系信息 */
.developer-contact {
  margin-top: 5px;
  font-size: 11px;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.developer-contact:hover {
  opacity: 1;
}

.developer-contact a {
  color: #409EFF;
  text-decoration: none;
  transition: color 0.3s;
}

.developer-contact a:hover {
  text-decoration: underline;
}

/* 响应式适配 */
@media (max-width: 576px) {
  .login-content {
    padding: 15px;
  }
  
  .title {
    font-size: 20px;
  }
  
  .subtitle {
    font-size: 14px;
  }
}
</style> 