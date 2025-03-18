<script setup>
import { ref } from 'vue';
import { Search } from '@element-plus/icons-vue';
import AppLayout from '@/components/AppLayout.vue';
import DatasetList from '@/components/dataset/DatasetList.vue';
import datasetService from '@/services/dataset';

const searchKeyword = ref('');
const datasetListRef = ref(null);

// 处理搜索
const handleSearch = async () => {
  if (datasetListRef.value) {
    // 调用DatasetList组件的搜索方法
    await datasetListRef.value.searchDatasets(searchKeyword.value);
  }
};
</script>

<template>
  <AppLayout>
    <div class="dataset-overview">
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
            <el-button :icon="Search" @click="handleSearch" size="large" />
          </template>
        </el-input>
      </div>
      <DatasetList ref="datasetListRef" :initial-keyword="''" />
    </div>
  </AppLayout>
</template>

<style scoped>
.dataset-overview {
  padding: 20px;
}

.search-container {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

.search-input {
  width: 100%;
  max-width: 600px;
  font-size: 16px;
}

:deep(.el-input__wrapper) {
  padding: 4px 11px;
}

:deep(.el-input__inner) {
  height: 40px;
  font-size: 16px;
}

:deep(.el-input-group__append) {
  padding: 0 20px;
}
</style> 