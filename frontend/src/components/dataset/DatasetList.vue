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
// 控制筛选面板的显示/隐藏
const showFilterPanel = ref(false);

// 获取数据集列表
const fetchDatasets = async (keyword = '') => {
  loading.value = true;
  try {
    const response = await datasetService.getDatasets({ keyword });
    datasets.value = response.data || [];
  } catch (error) {
    console.error('获取数据集列表失败:', error);
    ElMessage.error('获取数据集列表失败');
  } finally {
    loading.value = false;
  }
};

// 搜索数据集
const searchDatasets = async (keyword) => {
  await fetchDatasets(keyword);
};

// 处理筛选条件变化
const handleFilterChange = () => {
  fetchDatasets();
};

// 处理页码变化
const handleCurrentChange = (page) => {
  pagination.value.currentPage = page;
};

// 查看数据集详情
const viewDataset = (datasetId) => {
  router.push(`/datasets/${datasetId}`);
};

// 分析数据集
const analyzeDataset = (datasetId) => {
  router.push(`/datasets/${datasetId}/analyze`);
};

// 可视化数据集
const visualizeDataset = (datasetId) => {
  router.push(`/datasets/${datasetId}/visualize`);
};

// 切换筛选面板显示状态
const toggleFilterPanel = () => {
  showFilterPanel.value = !showFilterPanel.value;
};

// 点击外部关闭筛选面板
const closeFilterPanel = (event) => {
  const filterPanel = document.querySelector('.filter-panel');
  const filterButton = document.querySelector('.filter-button');
  
  if (showFilterPanel.value && filterPanel && !filterPanel.contains(event.target) && 
      filterButton && !filterButton.contains(event.target)) {
    showFilterPanel.value = false;
  }
};

// 监听点击事件，用于关闭筛选面板
onMounted(() => {
  fetchDatasets();
  document.addEventListener('click', closeFilterPanel);
});

// 暴露方法给父组件
defineExpose({
  searchDatasets,
  handleFilterChange
});
</script>

<template>
  <div class="dataset-container">
    <!-- 数据集列表容器 -->
    <div class="dataset-list-container">
      <el-card class="list-card">
        <!-- 卡片头部 -->
        <template #header>
          <div class="list-header">
            <!-- 左侧标题和筛选按钮 -->
            <div class="header-left">
              <el-button 
                class="filter-button" 
                type="primary" 
                @click.stop="toggleFilterPanel"
                :icon="showFilterPanel ? 'Close' : 'Filter'"
                circle
              />
              <h2>数据集列表</h2>
            </div>
            
            <!-- 右侧操作按钮 -->
            <div class="header-right">
              <el-button @click="fetchDatasets">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
              <el-button type="primary" @click="router.push('/upload')">上传数据集</el-button>
            </div>
          </div>
        </template>
        
        <!-- 筛选面板 -->
        <div class="filter-panel-container" v-if="showFilterPanel">
          <div class="filter-panel">
            <h3>筛选选项</h3>
            
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
              
              <div class="filter-actions">
                <el-button @click="showFilterPanel = false">取消</el-button>
                <el-button type="primary" @click="handleFilterChange">应用筛选</el-button>
              </div>
            </el-form>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="3" animated />
          <el-skeleton :rows="3" animated />
        </div>
        
        <!-- 空数据提示 -->
        <el-empty v-else-if="datasets.length === 0" description="暂无数据集" />
        
        <!-- 数据集列表 -->
        <div v-else class="dataset-list">
          <!-- 单个数据集卡片 -->
          <el-card v-for="dataset in datasets" :key="dataset.dataset_id" class="dataset-item">
            <div class="dataset-info">
              <!-- 数据集标题和ID -->
              <div class="dataset-header">
                <h3 class="dataset-name">{{ dataset.Name }}</h3>
                <span class="dataset-id">ID: {{ dataset.dataset_id }}</span>
              </div>
              
              <!-- 作者信息 -->
              <div class="dataset-author">
                <span v-if="dataset.Authors && dataset.Authors.length">
                  作者: {{ dataset.Authors.join(', ') }}
                </span>
              </div>
              
              <!-- 数据集详细信息 -->
              <div class="dataset-details">
                <span v-if="dataset.subject_count" class="detail-item">
                  <el-tag size="small" type="success">受试者: {{ dataset.subject_count }}</el-tag>
                </span>
                <span v-if="dataset.BIDSVersion" class="detail-item">
                  <el-tag size="small" type="info">BIDS版本: {{ dataset.BIDSVersion }}</el-tag>
                </span>
              </div>
              
              <!-- 操作按钮 -->
              <div class="dataset-actions">
                <el-button @click="viewDataset(dataset.dataset_id)" size="small">查看</el-button>
                <el-button type="primary" @click="analyzeDataset(dataset.dataset_id)" size="small">分析</el-button>
                <el-button type="success" @click="visualizeDataset(dataset.dataset_id)" size="small">可视化</el-button>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 分页控件 -->
        <div class="pagination" v-if="datasets.length > 0">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            :page-size="pagination.pageSize"
            :total="pagination.total"
            layout="total, prev, pager, next"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
/* 整体容器 */
.dataset-container {
  display: flex;
  min-height: calc(100vh - 100px); /* 最小高度 */
  padding: 0; /* 移除内边距以充分利用空间 */
}

/* 列表容器 */
.dataset-list-container {
  flex: 1; /* 占满可用空间 */
  padding-right: 20px; /* 右侧内边距 */
  width: 100%; /* 宽度占满 */
}

/* 列表头部 */
.list-header {
  display: flex;
  justify-content: space-between; /* 两端对齐 */
  align-items: center; /* 垂直居中 */
}

/* 头部左侧 */
.header-left {
  display: flex;
  align-items: center;
  gap: 12px; /* 元素间距 */
}

/* 头部标题 */
.header-left h2 {
  margin: 0; /* 移除默认外边距 */
}

/* 头部右侧 */
.header-right {
  display: flex;
  gap: 10px; /* 按钮间距 */
}

/* 数据集列表 */
.dataset-list {
  display: flex;
  flex-direction: column; /* 垂直排列 */
  gap: 16px; /* 卡片间距 */
  max-width: 100%; /* 最大宽度 */
  margin: 0 auto; /* 水平居中 */
}

/* 数据集卡片 */
.dataset-item {
  transition: transform 0.2s, box-shadow 0.2s; /* 悬停动画 */
}

/* 卡片悬停效果 */
.dataset-item:hover {
  transform: translateY(-2px); /* 上移效果 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* 阴影增强 */
}

/* 数据集信息容器 */
.dataset-info {
  display: flex;
  flex-direction: column;
  gap: 8px; /* 元素间距 */
}

/* 数据集标题行 */
.dataset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px; /* 下方间距 */
}

/* 数据集ID样式 */
.dataset-id {
  color: #909399; /* 灰色文字 */
  font-size: 14px; /* 字体大小 */
}

/* 数据集名称样式 */
.dataset-name {
  margin: 0;
  font-size: 18px; /* 字体大小 */
  color: #303133; /* 文字颜色 */
  text-align: left; /* 左对齐 */
  flex: 1; /* 占满剩余空间 */
  margin-right: 16px; /* 右侧间距 */
}

/* 作者信息样式 */
.dataset-author {
  font-size: 12px; /* 小字体 */
  color: #606266; /* 灰色文字 */
  text-align: left; /* 左对齐 */
  margin-bottom: 8px; /* 下方间距 */
}

/* 详细信息容器 */
.dataset-details {
  display: flex;
  flex-wrap: wrap; /* 允许换行 */
  gap: 8px; /* 标签间距 */
  margin-bottom: 12px; /* 下方间距 */
}

/* 详细信息项 */
.detail-item {
  margin-right: 8px; /* 右侧间距 */
}

/* 操作按钮容器 */
.dataset-actions {
  display: flex;
  justify-content: flex-start; /* 左对齐 */
  gap: 10px; /* 按钮间距 */
  margin-top: 8px; /* 上方间距 */
}

/* 分页控件 */
.pagination {
  margin-top: 20px; /* 上方间距 */
  display: flex;
  justify-content: center; /* 居中显示 */
}
</style> 