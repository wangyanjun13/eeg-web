<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import AppLayout from '../../components/layout/AppLayout.vue';

// 用户设置
const settings = ref({
  theme: 'light',
  language: 'zh-CN',
  notifications: {
    email: false,
    browser: true
  },
  display: {
    showTips: true,
    compactMode: false,
    dataPreview: true
  },
  privacy: {
    shareUsageData: false,
    allowCookies: true
  }
});

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
        notifications: {
          email: false,
          browser: true
        },
        display: {
          showTips: true,
          compactMode: false,
          dataPreview: true
        },
        privacy: {
          shareUsageData: false,
          allowCookies: true
        }
      };
      formChanged.value = true;
      ElMessage.success('设置已重置为默认值');
    }
  });
};

// 应用主题
const applyTheme = (theme) => {
  // 在实际项目中，这里应该根据主题更改应用的样式
  console.log('应用主题:', theme);
  // 例如：document.documentElement.setAttribute('data-theme', theme);
};
</script>

<template>
  <AppLayout>
    <div class="settings-container">
      <div class="settings-header">
        <h1 class="page-title">用户设置</h1>
        <div class="header-actions">
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
        <el-tabs tab-position="left">
          <!-- 外观设置 -->
          <el-tab-pane label="外观与语言">
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
          
          <!-- 通知设置 -->
          <el-tab-pane label="通知设置">
            <h3 class="section-title">通知偏好</h3>
            
            <el-form label-width="120px" @change="handleSettingChange">
              <el-form-item label="浏览器通知">
                <el-switch 
                  v-model="settings.notifications.browser"
                  @change="handleSettingChange"
                />
              </el-form-item>
              
              <el-form-item label="邮件通知">
                <el-switch 
                  v-model="settings.notifications.email"
                  @change="handleSettingChange"
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
          <!-- 隐私设置 -->
          <el-tab-pane label="隐私设置">
            <h3 class="section-title">隐私选项</h3>
            
            <el-form label-width="150px" @change="handleSettingChange">
              <el-form-item label="分享使用数据">
                <el-switch 
                  v-model="settings.privacy.shareUsageData"
                  @change="handleSettingChange"
                />
                <div class="setting-description">
                  允许分享匿名使用数据以帮助改进平台
                </div>
              </el-form-item>
              
              <el-form-item label="允许使用Cookie">
                <el-switch 
                  v-model="settings.privacy.allowCookies"
                  @change="handleSettingChange"
                />
                <div class="setting-description">
                  Cookie用于保存您的偏好设置和登录状态
                </div>
              </el-form-item>
            </el-form>
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