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
          placeholder="请输入数据集名称或ID，按回车键搜索"
          class="search-input"
          :prefix-icon="Search"
          clearable
          @keyup.enter="handleSearch"
          size="large"
        />
      </div>
      <!-- 数据集列表组件 -->
      <DatasetList ref="datasetListRef" :initial-keyword="''" />
    </div>
  </AppLayout>
</template>

<style scoped>
/* 整体容器样式 */
.dataset-overview {
  padding: 0;
  max-width: 100%;
}

/* 搜索框容器样式 */
.search-container {
  margin-bottom: 30px;
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

/* 搜索输入框样式 */
.search-input {
  width: 100%;
  max-width: 800px;
  font-size: 16px;
}

/* 输入框外层容器样式 */
:deep(.el-input__wrapper) {
  border-radius: 24px !important;
  border: 1px solid var(--primary-color) !important;
  box-shadow: 0 2px 5px var(--primary-color) !important;
  padding: 0 16px !important;
  height: 54px;
  transition: all 0.3s;
}

/* 输入框悬停效果 */
:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 3px 8px var(--primary-color) !important;
}

/* 输入框聚焦效果 */
:deep(.el-input__wrapper.is-focus) {
  border-color: #861f37 !important;
  box-shadow: 0 0 0 2px rgba(134, 31, 55, 0.2) !important;
}

/* 输入框内部样式 */
:deep(.el-input__inner) {
  height: 54px;
  font-size: 18px;
}

/* 前缀图标样式 */
:deep(.el-input__prefix-inner) {
  font-size: 20px;
  color: var(--primary-color);
}

/* 清除按钮样式 */
:deep(.el-input__suffix) {
  color: var(--primary-color);
}

:deep(.el-input__suffix-inner .el-icon) {
  font-size: 18px;
}

/* 响应式布局 */
@media (max-width: 992px) {
  .search-input {
    max-width: 600px;
  }
}

@media (max-width: 768px) {
  .search-container {
    padding: 15px 0;
  }
  
  .search-input {
    max-width: 100%;
  }
  
  :deep(.el-input__wrapper) {
    height: 46px;
  }
  
  :deep(.el-input__inner) {
    height: 46px;
    font-size: 16px;
  }
}

@media (max-width: 576px) {
  .search-container {
    padding: 10px 0;
  }
  
  :deep(.el-input__wrapper) {
    height: 40px;
    border-radius: 20px !important;
  }
  
  :deep(.el-input__inner) {
    height: 40px;
    font-size: 14px;
  }
  
  :deep(.el-input__prefix-inner) {
    font-size: 16px;
  }
}
</style> 