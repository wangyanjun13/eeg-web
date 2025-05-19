<script setup>
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import AppLayout from '../../components/layout/AppLayout.vue';

// 用户设置
const settings = ref({
  theme: 'light',
  language: 'zh-CN',
  display: {
    showTips: true,
    compactMode: false,
    dataPreview: true
  }
});

// 当前激活的标签页
const activeTab = ref('appearance');

// 主题选项
const themeOptions = [
  { label: '浅色主题', value: 'light' },
  { label: '深色主题', value: 'dark' },
  { label: '跟随系统', value: 'system' }
];

// 语言选项
const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: '英文', value: 'en-US' }
];

// 表单是否被修改
const formChanged = ref(false);

// 用户反馈表单
const feedbackForm = ref({
  description: '',
  screenshot: null
});

// 反馈表单规则
const feedbackRules = {
  description: [
    { required: true, message: '请输入问题描述', trigger: 'blur' },
    { min: 10, message: '问题描述至少10个字符', trigger: 'blur' }
  ]
};

// 反馈表单引用
const feedbackFormRef = ref(null);

// 计算属性：是否显示设置按钮
const showSettingsButtons = computed(() => {
  return activeTab.value === 'appearance';
});

// 从本地存储加载设置
onMounted(() => {
  const storedSettings = localStorage.getItem('userSettings');
  if (storedSettings) {
    try {
      settings.value = { ...settings.value, ...JSON.parse(storedSettings) };
    } catch (e) {
      console.error('解析用户设置失败', e);
    }
  }
});

// 监听设置变化
const handleSettingChange = () => {
  formChanged.value = true;
};

// 保存设置
const saveSettings = () => {
  localStorage.setItem('userSettings', JSON.stringify(settings.value));
  formChanged.value = false;
  ElMessage.success('设置已保存');
  
  // 应用主题设置
  applyTheme(settings.value.theme);
};

// 重置设置
const resetSettings = () => {
  ElMessage.warning({
    message: '确定要重置所有设置吗？',
    type: 'warning',
    showClose: true,
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    onConfirm: () => {
      settings.value = {
        theme: 'light',
        language: 'zh-CN',
        display: {
          showTips: true,
          compactMode: false,
          dataPreview: true
        }
      };
      formChanged.value = true;
      ElMessage.success('设置已重置为默认值');
    }
  });
};

// 处理标签页切换
const handleTabChange = (tab) => {
  activeTab.value = tab;
};

// 应用主题
const applyTheme = (theme) => {
  // 获取根元素
  const htmlElement = document.documentElement;
  
  // 移除之前的主题类
  htmlElement.classList.remove('theme-light', 'theme-dark');
  
  // 添加新的主题类
  if (theme === 'light') {
    htmlElement.classList.add('theme-light');
    ElMessage({
      message: '已切换到浅色主题',
      type: 'success',
      duration: 1500
    });
  } else if (theme === 'dark') {
    htmlElement.classList.add('theme-dark');
    ElMessage({
      message: '已切换到深色主题',
      type: 'success',
      duration: 1500
    });
  } else if (theme === 'system') {
    // 检测系统主题
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    htmlElement.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
    
    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      htmlElement.classList.remove('theme-light', 'theme-dark');
      htmlElement.classList.add(e.matches ? 'theme-dark' : 'theme-light');
    });
    
    ElMessage({
      message: `已跟随系统主题（当前：${prefersDark ? '深色' : '浅色'}）`,
      type: 'success',
      duration: 1500
    });
  }
  
  // 确保添加过渡动画类
  if (!htmlElement.classList.contains('theme-transition')) {
    htmlElement.classList.add('theme-transition');
  }
  
  console.log('主题已切换:', theme);
};

// 处理截图上传
const handleScreenshotChange = (file) => {
  feedbackForm.value.screenshot = file;
  return false; // 阻止自动上传
};

// 提交反馈
const submitFeedback = () => {
  if (!feedbackFormRef.value) return;
  
  feedbackFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 创建一个包含反馈内容的邮件链接
        const subject = encodeURIComponent('EEG平台用户反馈');
        const body = encodeURIComponent(`问题描述：\n${feedbackForm.value.description}\n\n`);
        
        // 打开邮件客户端
        window.location.href = `mailto:wangyanjun13@foxmail.com?subject=${subject}&body=${body}`;
        
        // 如果有截图，提示用户在邮件中附加
        if (feedbackForm.value.screenshot) {
          ElMessage.info('请在邮件中附加您的截图后发送');
        }
        
        // 清空表单
        feedbackForm.value.description = '';
        feedbackForm.value.screenshot = null;
        
        ElMessage.success('感谢您的反馈！');
      } catch (error) {
        console.error('提交反馈失败:', error);
        ElMessage.error('提交反馈失败，请稍后再试');
      }
    }
  });
};
</script>

<template>
  <AppLayout>
    <div class="settings-container">
      <div class="settings-header">
        <h1 class="page-title">用户设置</h1>
        <div class="header-actions" v-if="showSettingsButtons">
          <el-button @click="resetSettings">重置默认</el-button>
          <el-button 
            type="primary" 
            @click="saveSettings" 
            :disabled="!formChanged"
          >
            保存设置
          </el-button>
        </div>
      </div>
      
      <el-card class="settings-card">
        <el-tabs tab-position="left" @tab-change="handleTabChange" v-model="activeTab">
          <!-- 外观设置 -->
          <el-tab-pane label="外观与语言" name="appearance">
            <h3 class="section-title">外观设置</h3>
            
            <el-form label-width="100px" @change="handleSettingChange">
              <el-form-item label="主题">
                <el-select 
                  v-model="settings.theme" 
                  placeholder="选择主题"
                  @change="handleSettingChange"
                >
                  <el-option 
                    v-for="item in themeOptions" 
                    :key="item.value" 
                    :label="item.label" 
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              
              <el-form-item label="语言">
                <el-select 
                  v-model="settings.language" 
                  placeholder="选择语言"
                  @change="handleSettingChange"
                >
                  <el-option 
                    v-for="item in languageOptions" 
                    :key="item.value" 
                    :label="item.label" 
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              
              <el-form-item label="紧凑模式">
                <el-switch 
                  v-model="settings.display.compactMode"
                  @change="handleSettingChange"
                />
              </el-form-item>
              
              <el-form-item label="显示提示">
                <el-switch 
                  v-model="settings.display.showTips"
                  @change="handleSettingChange"
                />
              </el-form-item>
              
              <el-form-item label="数据预览">
                <el-switch 
                  v-model="settings.display.dataPreview"
                  @change="handleSettingChange"
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
          <!-- 用户反馈 -->
          <el-tab-pane label="用户反馈" name="feedback">
            <div class="feedback-container">
              <div class="feedback-intro">
                <h3 class="section-title">问题反馈</h3>
                <p class="feedback-description">
                  尊敬的用户您好，感谢您对本系统的信赖。我深知本系统还存在较多缺陷，如影响使用，希望留下您宝贵的意见。
                </p>
              </div>
              
              <el-form 
                ref="feedbackFormRef"
                :model="feedbackForm"
                :rules="feedbackRules"
                label-position="top"
                class="feedback-form"
              >
                <el-form-item label="问题描述" prop="description">
                  <el-input 
                    v-model="feedbackForm.description"
                    type="textarea"
                    :rows="5"
                    placeholder="请详细描述您遇到的问题..."
                  />
                </el-form-item>
                
                <el-form-item label="问题截图（可选）">
                  <el-upload
                    class="screenshot-uploader"
                    action="#"
                    :auto-upload="false"
                    :on-change="handleScreenshotChange"
                    :limit="1"
                    :file-list="feedbackForm.screenshot ? [feedbackForm.screenshot] : []"
                  >
                    <el-button type="primary">选择截图</el-button>
                    <template #tip>
                      <div class="el-upload__tip">
                        支持 jpg/png 格式图片，不超过 5MB
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="submitFeedback">提交反馈</el-button>
                </el-form-item>
              </el-form>
              
              <div class="direct-contact">
                <p class="contact-text">
                  您也可以直接发送邮件至：
                  <a href="mailto:wangyanjun13@foxmail.com">wangyanjun13@foxmail.com</a>
                </p>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.settings-card {
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.setting-description {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.4;
}

/* 反馈相关样式 */
.feedback-container {
  max-width: 100%;
  width: 100%;
}

.feedback-description {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 25px;
  padding: 10px 15px;
  background-color: #f0f9ff;
  border-left: 4px solid #409EFF;
  border-radius: 4px;
}

.feedback-form {
  margin-bottom: 30px;
  max-width: 800px;
}

.direct-contact {
  margin-top: 20px;
  padding: 12px 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
  max-width: 800px;
}

.contact-text {
  font-size: 13px;
  color: #606266;
  margin: 0;
}

.direct-contact a {
  color: #409EFF;
  text-decoration: none;
  font-weight: 500;
  font-size: 13px;
}

.direct-contact a:hover {
  text-decoration: underline;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .settings-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  :deep(.el-tabs__header) {
    margin-right: 0;
  }
}

@media (max-width: 576px) {
  :deep(.el-tabs--left) {
    flex-direction: column;
  }
  
  :deep(.el-tabs__header.is-left) {
    margin-right: 0;
    margin-bottom: 15px;
  }
  
  :deep(.el-tabs__nav-wrap.is-left) {
    margin-bottom: 0;
  }
  
  :deep(.el-tabs__nav.is-left) {
    flex-wrap: nowrap;
    overflow-x: auto;
    white-space: nowrap;
    display: flex;
  }
  
  :deep(.el-tabs__item.is-left) {
    display: inline-block;
  }
}
</style> 