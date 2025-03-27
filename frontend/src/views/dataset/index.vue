<script setup>
import { ref, watch } from 'vue';
import { Search } from '@element-plus/icons-vue';
import AppLayout from '@/components/layout/AppLayout.vue';
import DatasetList from '@/components/dataset/DatasetList.vue';
import datasetService from '@/services/dataset';
import { useDebounce } from '@/composables/useDebounce';

const searchKeyword = ref('');
const datasetListRef = ref(null);
const debouncedKeyword = useDebounce('', 300);

// 监听防抖关键词变化
watch(debouncedKeyword, (newKeyword) => {
  if (datasetListRef.value) {
    datasetListRef.value.searchDatasets(newKeyword);
  }
});

// 处理搜索
const handleSearch = () => {
  debouncedKeyword.value = searchKeyword.value;
};
</script>

<template>
  <AppLayout>
    <div class="dataset-overview">
      <!-- 搜索框容器 -->
      <div class="search-container">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入数据集名称或ID"
          class="search-input"
          :prefix-icon="Search"
          clearable
          @keyup.enter="handleSearch"
          size="large"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" class="search-button" />
          </template>
        </el-input>
      </div>
      <!-- 数据集列表组件 -->
      <DatasetList ref="datasetListRef" :initial-keyword="''" />
    </div>
  </AppLayout>
</template>

<style scoped>
/* 整体容器样式 */
.dataset-overview {
  padding: 20px; /* 整体内边距 */
}

/* 搜索框容器样式 */
.search-container {
  margin-bottom: 30px; /* 与下方内容的间距 */
  display: flex;
  justify-content: center; /* 居中显示 */
  padding: 20px 0; /* 上下内边距 */
}

/* 搜索输入框样式 */
.search-input {
  width: 100%; /* 宽度占满容器 */
  max-width: 800px; /* 最大宽度限制 */
  font-size: 16px; /* 字体大小 */
}

/* 输入框外层容器样式 */
:deep(.el-input__wrapper) {
  border-radius: 24px !important; /* 圆角大小 */
  border: 1px solid #dcdfe6 !important; /* 边框样式 */
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05) !important; /* 阴影效果 */
  padding: 0 0 0 16px !important; /* 左侧内边距 */
  height: 54px; /* 输入框高度 */
  transition: all 0.3s; /* 过渡动画 */
}

/* 输入框悬停效果 */
:deep(.el-input__wrapper:hover) {
  border-color: #c0c4cc !important; /* 悬停时边框颜色 */
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1) !important; /* 悬停时阴影效果 */
}

/* 输入框聚焦效果 */
:deep(.el-input__wrapper.is-focus) {
  border-color: #409eff !important; /* 聚焦时边框颜色 */
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2) !important; /* 聚焦时阴影效果 */
}

/* 输入框内部样式 */
:deep(.el-input__inner) {
  height: 54px; /* 输入区域高度 */
  font-size: 18px; /* 输入文字大小 */
}

/* 输入框右侧按钮容器样式 */
:deep(.el-input-group__append) {
  border-top-right-radius: 24px !important; /* 右上圆角 */
  border-bottom-right-radius: 24px !important; /* 右下圆角 */
  background-color: transparent !important; /* 背景透明 */
  padding: 0 !important; /* 移除内边距 */
  border-left: none !important; /* 移除左边框 */
}

/* 搜索按钮样式 */
:deep(.search-button) {
  border-radius: 0 24px 24px 0 !important; /* 右侧圆角 */
  height: 54px; /* 按钮高度 */
  width: 70px; /* 按钮宽度 */
  border: none; /* 移除边框 */
  background-color: #f5f7fa; /* 背景颜色 */
  color: #606266; /* 图标颜色 */
}

/* 搜索按钮悬停效果 */
:deep(.search-button:hover) {
  background-color: #ecf5ff; /* 悬停时背景颜色 */
  color: #409eff; /* 悬停时图标颜色 */
}

/* 前缀图标样式 */
:deep(.el-input__prefix-inner) {
  font-size: 20px; /* 图标大小 */
  color: #909399; /* 图标颜色 */
}
</style> 