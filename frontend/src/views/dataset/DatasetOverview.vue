<script setup>
import { onMounted, ref } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import DatasetList from '@/components/dataset/DatasetList.vue';
import { Search } from '@element-plus/icons-vue';

const searchKeyword = ref('');
const datasetListRef = ref(null);

const handleSearch = () => {
  // 触发DatasetList组件的搜索
  if (datasetListRef.value) {
    datasetListRef.value.filterForm.keyword = searchKeyword.value;
    datasetListRef.value.handleFilterChange();
  }
};
</script>

<template>
  <AppLayout>
    <div class="dataset-overview">
      <div class="search-container">
        <el-input
          v-model="searchKeyword"
          placeholder="查找需要的数据集"
          class="search-input"
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
        >
          <template #append>
            <el-button :icon="Search" />
          </template>
        </el-input>
      </div>
      <DatasetList ref="datasetListRef" />
    </div>
  </AppLayout>
</template>

<style scoped>
.dataset-overview {
  padding: 0 20px;
}

.search-container {
  margin-bottom: 24px;
  max-width: 1200px;
  margin: 0 auto 24px;
}

.search-input {
  --el-input-height: 50px;
  font-size: 16px;
  border: 1px solid #000;
  border-radius: 25px;
}

.search-input :deep(.el-input__wrapper) {
  padding: 0 15px;
  box-shadow: 0 2px 12px rgba(81, 50, 171, 0.1);
  border-radius: 25px;
}

.search-input :deep(.el-input__inner) {
  height: 50px;
  font-size: 16px;
}

.search-input :deep(.el-input-group__append) {
  padding: 0 20px;
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: white;
  border-radius: 0 25px 25px 0;
}

.search-input :deep(.el-input-group__append .el-button) {
  color: white;
  border: none;
}
</style> 