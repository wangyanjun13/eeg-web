<script setup>
import { ref, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import datasetService from '@/services/dataset';
import { useDebounce, useDebounceFn } from '@/composables/useDebounce';
import { useLoading } from '@/composables/useLoading';

const router = useRouter();

// 筛选条件
const filterForm = ref({
  keyword: '',
  tags: [],
  dateRange: [],
  sortBy: 'updated_at',
  sortOrder: 'desc'
});

// 使用防抖的关键词
const debouncedKeyword = useDebounce('', 300);

// 分页
const pagination = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0
});

// 数据集列表
const datasets = ref([]);
const { isLoading: loading, withLoading } = useLoading(false);
// 控制筛选面板的显示/隐藏
const showFilterPanel = ref(false);

// 访问量
const visitCount = ref(0);

// 获取访问量
const fetchVisitCount = async () => {
  try {
    const response = await datasetService.getVisitCount();
    if (response.data && response.data.visit_count !== undefined) {
      visitCount.value = response.data.visit_count;
    }
  } catch (error) {
    console.error('获取访问量失败:', error);
  }
};

// 记录访问
const recordVisit = async () => {
  try {
    const response = await datasetService.recordVisit();
    if (response.data && response.data.visit_count !== undefined) {
      visitCount.value = response.data.visit_count;
    }
  } catch (error) {
    console.error('记录访问量失败:', error);
  }
};

// 防抖的获取数据集函数
const debouncedFetchDatasets = useDebounceFn(async () => {
  try {
    const response = await withLoading(datasetService.getDatasets(filterForm.value));
    datasets.value = response.data || [];
    pagination.value.total = datasets.value.length;
  } catch (error) {
    console.error('获取数据集列表失败:', error);
    ElMessage.error('获取数据集列表失败');
  }
}, 300);

// 监听防抖关键词变化
watch(debouncedKeyword, (newKeyword) => {
  debouncedFetchDatasets();
});

// 搜索数据集
const searchDatasets = async (keyword) => {
  filterForm.value.keyword = keyword;
  debouncedFetchDatasets();
};

// 处理筛选条件变化
const handleFilterChange = () => {
  debouncedFetchDatasets();
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
  debouncedFetchDatasets();
  document.addEventListener('click', closeFilterPanel);
  
  // 记录访问并获取访问量
  recordVisit();
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
              <!-- 访问量显示 -->
              <div class="visit-count">
                <el-tooltip content="网站总访问量" placement="bottom">
                  <div>
                    <el-icon><View /></el-icon>
                    <span>{{ visitCount }}</span>
                  </div>
                </el-tooltip>
              </div>
              <el-button @click="debouncedFetchDatasets">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
              <el-button @click="router.push('/my-files')">
                <el-icon><Document /></el-icon> 我的文件
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
          <el-card 
            v-for="dataset in datasets" 
            :key="dataset.dataset_id" 
            class="dataset-item"
            @click="viewDataset(dataset.dataset_id)"
            style="cursor: pointer;"
          >
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
                  <el-tag size="small" type="success" class="subject-count-tag">被试: {{ dataset.subject_count }}</el-tag>
                </span>
                <span v-if="dataset.BIDSVersion" class="detail-item">
                  <el-tag size="small" type="info">BIDS版本: {{ dataset.BIDSVersion }}</el-tag>
                </span>
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

/* 列表卡片 */
.list-card {
  background-color: rgba(255, 255, 255, 0.8); /* 半透明白色背景 */
  border: none; /* 移除边框 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); /* 轻微阴影 */
  border-radius: 8px; /* 圆角 */
}

/* 列表头部 */
.list-header {
  display: flex;
  justify-content: space-between; /* 两端对齐 */
  align-items: center; /* 垂直居中 */
  padding: 0 20px; /* 左右加宽一点 */
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
  color:  var(--primary-color); /* 设置字体颜色 */
  font-size: 24px; /* 增加字体大小 */
}

/* 头部右侧 */
.header-right {
  display: flex;
  gap: 10px; /* 按钮间距 */
}

/* 头部右侧按钮样式 */
.header-right :deep(.el-button) {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: #ffffff;
  font-weight: 600;
}

/* 确保按钮内的文字和图标都是白色 */
.header-right :deep(.el-button .el-icon) {
  color: #ffffff;
}

/* 访问量显示样式 */
.visit-count {
  color: #ffffff;
  font-weight: 600;
}

/* 数据集列表 */
.dataset-list {
  display: flex;
  flex-direction: column; /* 垂直排列 */
  gap: 8px; /* 进一步减小卡片间距，原为12px */
  max-width: 100%; /* 最大宽度 */
  margin: 0 auto; /* 水平居中 */
}

/* 数据集卡片 */
.dataset-item {
  transition: transform 0.2s, box-shadow 0.2s; /* 悬停动画 */
  border-left: 4px solid #abcff6; /* 左侧添加蓝色边框 */
  border-radius: 4px; /* 减小圆角 */
  overflow: hidden; /* 确保内容不超出边框 */
  background-color: rgba(255, 255, 255, 0.9); /* 半透明白色背景 */
}

/* 覆盖el-card的默认内边距 */
.dataset-item :deep(.el-card__body) {
  padding: 6px 10px !important; /* 进一步减小卡片内边距，*/
}

/* 卡片悬停效果 */
.dataset-item:hover {
  transform: translateY(-2px); /* 上移效果 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* 阴影增强 */
  background-color: #e1edff; /* 悬停时背景色变为更深的浅蓝 */
  border-left-color: var(--primary-color); /* 悬停时边框颜色变亮 */
}

/* 数据集信息容器 */
.dataset-info {
  display: flex;
  flex-direction: column;
  gap: 2px; /* 进一步减小元素间距，原为4px */
  background-color: transparent; /* 透明背景 */
  padding: 0; /* 移除内边距 */
}

/* 数据集标题行 */
.dataset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0; /* 移除下方间距 */
  line-height: 1.2; /* 减小行高，使标题更紧凑 */
}

/* 数据集ID样式 */
.dataset-id {
  color: #1b1b1c; /* 灰色文字909399 */
  font-size: 13px; /* 进一步减小字体大小 */
}

/* 数据集名称样式 */
.dataset-name {
  margin: 0;
  font-size: 15px; /* 保持字体大小不变 */
  color: var(--primary-color); /* 文字颜色 */
  text-align: left; /* 左对齐 */
  flex: 1; /* 占满剩余空间 */
  margin-right: 12px; /* 右侧间距 */
  line-height: 1.2; /* 减小行高 */
}

/* 作者信息样式 */
.dataset-author {
  font-size: 12px; /* 保持字体大小不变 */
  color: #606266; /* 灰色文字 */
  text-align: left; /* 左对齐 */
  margin-bottom: 2px; /* 减小下方间距，原为4px */
  line-height: 1.2; /* 减小行高 */
}

/* 详细信息容器 */
.dataset-details {
  display: flex;
  flex-wrap: wrap; /* 允许换行 */
  gap: 4px; /* 标签间距 */
  margin-bottom: 0; /* 移除下方间距 */
  line-height: 1.2; /* 减小行高 */
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

/* 访问量显示样式 */
.visit-count {
  display: flex;
  align-items: center;
  margin-right: 15px;
  font-size: 14px;
  color: #606266;
}

.visit-count .el-icon {
  margin-right: 5px;
  font-size: 16px;
}

/* 筛选面板容器 */
.filter-panel-container {
  margin-bottom: 20px;
}

.filter-panel {
  background-color: rgba(255, 255, 255, 0.9); /* 半透明白色背景 */
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

/* 被试数量标签样式 */
:deep(.subject-count-tag) {
  background-color: white !important;
  border-color: var(--success-color) !important;
  color: var(--success-color) !important;
}
</style> 