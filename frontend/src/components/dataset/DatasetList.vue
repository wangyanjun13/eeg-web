<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import datasetService from '@/services/dataset';

const router = useRouter();

// 筛选条件
const filterForm = ref({
  keyword: '',
  tags: [],
  dateRange: [],
  sortBy: 'updated_at',
  sortOrder: 'desc'
});

// 分页
const pagination = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0
});

// 数据集列表
const datasets = ref([]);
const loading = ref(false);

// 获取数据集列表
const loadDatasets = async () => {
  loading.value = true;
  try {
    const response = await datasetService.getDatasets({
      ...filterForm.value,
      page: pagination.value.currentPage,
      pageSize: pagination.value.pageSize
    });
    
    console.log('API响应:', response); // 调试日志
    
    if (response && response.data) {
      datasets.value = response.data;
      pagination.value.total = datasets.value.length;
    }
  } catch (error) {
    console.error('获取数据集列表失败:', error);
    ElMessage.error('获取数据集列表失败');
  } finally {
    loading.value = false;
  }
};

// 处理筛选条件变化
const handleFilterChange = () => {
  pagination.value.currentPage = 1;
  loadDatasets();
};

// 处理分页变化
const handlePageChange = (page) => {
  pagination.value.currentPage = page;
  loadDatasets();
};

// 查看数据集详情
const viewDataset = (id) => {
  router.push(`/datasets/${id}`);
};

// 分析数据集
const analyzeDataset = (id) => {
  router.push(`/datasets/${id}/analyze`);
};

onMounted(() => {
  loadDatasets();
});
</script>

<template>
  <div class="dataset-container">
    <!-- 左侧筛选区域 -->
    <aside class="filter-sidebar">
      <el-card class="filter-card">
        <template #header>
          <div class="filter-header">
            <h3>筛选选项</h3>
            <el-button text @click="handleFilterChange">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </template>
        
        <el-form :model="filterForm" label-position="top">
          <el-form-item label="关键词搜索">
            <el-input 
              v-model="filterForm.keyword" 
              placeholder="搜索数据集名称或描述" 
              clearable
              @change="handleFilterChange" 
            />
          </el-form-item>
          
          <el-form-item label="数据类型">
            <el-select 
              v-model="filterForm.tags" 
              multiple 
              placeholder="选择数据类型" 
              style="width: 100%"
              clearable
              @change="handleFilterChange"
            >
              <el-option label="ERP" value="erp" />
              <el-option label="静息态" value="resting" />
              <el-option label="任务态" value="task" />
              <el-option label="睡眠" value="sleep" />
              <el-option label="运动想象" value="mi" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="更新时间">
            <el-date-picker
              v-model="filterForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 100%"
              value-format="YYYY-MM-DD"
              @change="handleFilterChange"
            />
          </el-form-item>
          
          <el-form-item label="排序方式">
            <div class="sort-options">
              <el-select 
                v-model="filterForm.sortBy" 
                style="width: 70%"
                @change="handleFilterChange"
              >
                <el-option label="更新时间" value="updated_at" />
                <el-option label="下载次数" value="downloads" />
                <el-option label="评分" value="rating" />
              </el-select>
              <el-switch
                v-model="filterForm.sortOrder"
                active-text="降序"
                inactive-text="升序"
                active-value="desc"
                inactive-value="asc"
                @change="handleFilterChange"
              />
            </div>
          </el-form-item>
        </el-form>
      </el-card>
    </aside>
    
    <!-- 右侧数据集列表 -->
    <div class="dataset-list-container">
      <el-card class="list-card">
        <template #header>
          <div class="list-header">
            <h2>数据集列表</h2>
            <el-button type="primary" @click="router.push('/upload')">上传数据集</el-button>
          </div>
        </template>
        
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="3" animated />
          <el-skeleton :rows="3" animated />
        </div>
        
        <el-empty v-else-if="datasets.length === 0" description="暂无数据集" />
        
        <div v-else class="dataset-list">
          <el-card v-for="dataset in datasets" :key="dataset.dataset_id" class="dataset-item">
            <div class="dataset-info">
              <h3 class="dataset-name">{{ dataset.Name }}</h3>
              <p class="dataset-description">{{ dataset.BIDSVersion ? `BIDS版本: ${dataset.BIDSVersion}` : '' }}</p>
              
              <div class="dataset-meta">
                <div class="tags">
                  <el-tag v-if="dataset.License" size="small" class="meta-tag">
                    许可证: {{ dataset.License }}
                  </el-tag>
                  <el-tag v-if="dataset.subject_count" size="small" class="meta-tag" type="success">
                    受试者: {{ dataset.subject_count }}
                  </el-tag>
                </div>
                <span class="authors" v-if="dataset.Authors && dataset.Authors.length">
                  作者: {{ dataset.Authors.join(', ') }}
                </span>
              </div>
              
              <div class="dataset-actions">
                <el-button @click="viewDataset(dataset.dataset_id)" size="small">查看</el-button>
                <el-button type="primary" @click="analyzeDataset(dataset.dataset_id)" size="small">分析</el-button>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 分页 -->
        <div class="pagination" v-if="datasets.length > 0">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            :page-size="pagination.pageSize"
            :total="pagination.total"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.dataset-container {
  display: flex;
  gap: 20px;
  min-height: calc(100vh - 100px);
  padding: 0;
  margin-left: -20px;
}

.filter-sidebar {
  width: 280px;
  flex-shrink: 0;
  margin-left: -120px;
}

.filter-card {
  position: sticky;
  top: 80px;
  border-radius: 0;
  margin-left: 0;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-header h3 {
  margin: 0;
  font-size: 16px;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dataset-list-container {
  flex: 1;
  padding-right: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-header h2 {
  margin: 0;
}

.loading-container {
  padding: 20px 0;
}

.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dataset-item {
  transition: transform 0.2s, box-shadow 0.2s;
}

.dataset-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dataset-name {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 18px;
  color: #303133;
}

.dataset-description {
  margin-bottom: 16px;
  color: #606266;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.dataset-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.tags {
  display: flex;
  gap: 8px;
}

.meta-tag {
  margin: 0;
}

.authors {
  font-size: 12px;
  color: #606266;
}

.dataset-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style> 