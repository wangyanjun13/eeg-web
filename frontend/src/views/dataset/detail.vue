<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/layout/AppLayout.vue';
import { useLoading } from '@/composables/useLoading';

const route = useRoute();
const router = useRouter();
const datasetId = route.params.id;

// 数据状态
const dataset = ref(null);
const subjects = ref([]);
const participants = ref(null);
const participantsMap = ref({});  // 用于存储受试者ID到人口统计学信息的映射

// 使用组合式API管理加载状态
const { isLoading: loading, withLoading } = useLoading({
  dataset: false,
  subjects: false,
  participants: false
});

const activeTab = ref('subjects'); // 当前活动标签页
const downloadDialogVisible = ref(false); // 控制获取数据集对话框的显示

// 打开获取数据集对话框
const openDownloadDialog = () => {
  downloadDialogVisible.value = true;
};

// 获取数据集详情
const fetchDatasetInfo = async () => {
  try {
    const response = await withLoading(
      datasetService.getDatasetById(datasetId),
      'dataset'
    );
    dataset.value = response.data;
  } catch (error) {
    console.error('获取数据集详情失败:', error);
    ElMessage.error('获取数据集详情失败');
  }
};

// 获取受试者列表
const fetchSubjects = async () => {
  try {
    const response = await withLoading(
      datasetService.getDatasetSubjects(datasetId),
      'subjects'
    );
    subjects.value = response.data || [];
  } catch (error) {
    console.error('获取被试列表失败:', error);
    ElMessage.error('获取被试列表失败');
  }
};

// 获取参与者信息
const fetchParticipantsInfo = async () => {
  try {
    const response = await withLoading(
      datasetService.getParticipantsInfo(datasetId),
      'participants'
    );
    participants.value = response.data;
    
    // 处理participants.tsv数据，创建ID到信息的映射
    if (response.data && response.data.participants) {
      const participantsData = response.data.participants;
      participantsMap.value = participantsData.reduce((map, participant) => {
        // 从participant_id中提取数字部分（例如从"sub-1"提取"1"）
        const idMatch = participant.participant_id.match(/sub-(\d+)/);
        if (idMatch) {
          const id = idMatch[1];
          map[id] = participant;
        }
        return map;
      }, {});
    }
    console.log('参与者映射:', participantsMap.value); // 调试输出
  } catch (error) {
    console.error('获取参与者信息失败:', error);
    ElMessage.error('获取参与者信息失败');
  }
};

// 查看受试者详情
const viewSubject = (subjectId) => {
  router.push(`/datasets/${datasetId}/subjects/${subjectId}`);
};

// 分析受试者数据
const analyzeSubject = (subjectId) => {
  router.push(`/datasets/${datasetId}/subjects/${subjectId}/analyze`);
};

// 导出受试者数据
const exportSubjectData = async (subjectId) => {
  try {
    // 直接创建一个a标签，设置href为API URL
    const link = document.createElement('a');
    link.href = `${import.meta.env.VITE_API_BASE_URL}/api/datasets/${datasetId}/subjects/${subjectId}/export`;
    link.setAttribute('download', `${datasetId}_sub-${subjectId}_data.zip`);
    
    // 添加到DOM并触发点击
    document.body.appendChild(link);
    link.click();
    
    // 清理DOM
    setTimeout(() => {
      document.body.removeChild(link);
    }, 100);
    
  } catch (error) {
    console.error('导出数据失败:', error);
    ElMessage.error('导出数据失败');
  }
};

// 页面加载时获取数据
onMounted(() => {
  fetchDatasetInfo();
  fetchSubjects();
  fetchParticipantsInfo();
});
</script>

<template>
  <AppLayout>
    <div class="dataset-detail-container">
      <!-- 返回按钮 -->
      <div class="back-button">
        <el-button @click="router.push('/datasets')" icon="ArrowLeft">返回数据集列表</el-button>
      </div>

      <!-- 数据集基本信息卡片 -->
      <el-card v-loading="loading.dataset" class="dataset-info-card">
        <template #header>
          <div class="card-header">
            <h2 v-if="dataset">{{ dataset.Name }}</h2>
            <el-skeleton v-else :rows="1" animated />
            <el-button v-if="dataset" type="primary" @click="openDownloadDialog">获取数据集</el-button>
          </div>
        </template>

        <div v-if="dataset" class="dataset-info">
          <!-- 基本信息部分 -->
          <div class="info-section">
            <h3>基本信息</h3>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="数据集ID">{{ dataset.dataset_id }}</el-descriptions-item>
              <el-descriptions-item label="被试数量">{{ dataset.subject_count }}</el-descriptions-item>
              <el-descriptions-item label="BIDS版本">{{ dataset.BIDSVersion }}</el-descriptions-item>
              <el-descriptions-item label="许可证">{{ dataset.License }}</el-descriptions-item>
              <el-descriptions-item label="DOI" :span="2">{{ dataset.DatasetDOI }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 作者信息部分 -->
          <div class="info-section">
            <h3>作者信息</h3>
            <el-tag 
              v-for="(author, index) in dataset.Authors" 
              :key="index"
              class="author-tag"
              type="info"
              effect="plain"
            >
              {{ author }}
            </el-tag>
          </div>

          <!-- 引用说明部分 -->
          <div v-if="dataset.HowToAcknowledge" class="info-section">
            <h3>引用说明</h3>
            <p>{{ dataset.HowToAcknowledge }}</p>
          </div>

          <!-- 数据集描述部分 -->
          <div v-if="dataset.description" class="info-section">
            <h3>数据集描述</h3>
            <p>{{ dataset.description }}</p>
          </div>
        </div>
      </el-card>

      <!-- 受试者信息卡片 -->
      <el-card class="subjects-card">
        <template #header>
          <div class="card-header">
            <h3>被试信息</h3>
            <el-tabs v-model="activeTab">
              <el-tab-pane label="被试列表" name="subjects"></el-tab-pane>
              <el-tab-pane label="参与者统计" name="participants"></el-tab-pane>
            </el-tabs>
          </div>
        </template>

        <!-- 受试者列表标签页 -->
        <div v-if="activeTab === 'subjects'" v-loading="loading.subjects">
          <el-empty v-if="subjects.length === 0 && !loading.subjects" description="暂无受试者数据" />
          
          <el-table v-else :data="subjects" style="width: 100%" border stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="subject" label="被试" />
            <el-table-column prop="format" label="格式" width="100" />
            
            <!-- 年龄列 -->
            <el-table-column label="年龄" width="80">
              <template #default="scope">
                {{ participantsMap[scope.row.id]?.Age || '-' }}
              </template>
            </el-table-column>
            
            <!-- 性别列 -->
            <el-table-column label="性别" width="80">
              <template #default="scope">
                {{ participantsMap[scope.row.id]?.Gender || '-' }}
              </template>
            </el-table-column>
            
            <!-- 操作列 -->
            <el-table-column label="操作" width="280">
              <template #default="scope">
                <el-button size="small" type="primary" @click="viewSubject(scope.row.id)">查看/分析</el-button>
                <el-button size="small" type="success" @click="exportSubjectData(scope.row.id)">导出</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 参与者统计标签页 -->
        <div v-else-if="activeTab === 'participants'" v-loading="loading.participants" class="participants-info">
          <el-empty v-if="!participants && !loading.participants" description="暂无参与者信息" />
          
          <div v-else-if="participants">
            <!-- 参与者统计信息 -->
            <div v-if="participants.summary">
              <h3>基本统计</h3>
              <el-descriptions :column="3" border>
                <el-descriptions-item label="总人数">{{ participants.summary.total_count }}</el-descriptions-item>
                <el-descriptions-item label="平均年龄">{{ participants.summary.age_mean }} ± {{ participants.summary.age_std }}</el-descriptions-item>
                <el-descriptions-item label="性别分布">男: {{ participants.summary.male_count }}, 女: {{ participants.summary.female_count }}</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <!-- 分组统计信息 -->
            <div v-if="participants.groups && participants.groups.length > 0" class="group-stats">
              <h3>分组统计</h3>
              <div v-for="(group, index) in participants.groups" :key="index" class="group-item">
                <h4>{{ group.name }}</h4>
                <el-descriptions :column="3" border>
                  <el-descriptions-item label="人数">{{ group.count }}</el-descriptions-item>
                  <el-descriptions-item label="平均年龄">{{ group.age_mean }} ± {{ group.age_std }}</el-descriptions-item>
                  <el-descriptions-item label="性别分布">男: {{ group.male_count }}, 女: {{ group.female_count }}</el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 获取数据集对话框 -->
    <el-dialog
      v-model="downloadDialogVisible"
      title="获取数据集"
      width="800px"
      class="download-dialog"
    >
      <div class="download-methods">
        <h4>数据集ID: {{ dataset?.dataset_id }}</h4>
        
        <div class="method">
          <h5>方法1: 从 S3 下载</h5>
          <p>此方法最适合较大的数据集或不稳定的连接。此示例使用 AWS CLI。</p>
          <p>AWS CLI：<a href="https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html" target="_blank">安装指南</a></p>
          <p>安装后，命令行进入要下载的目录下：</p>
          <div class="code-block">
            <pre>aws s3 sync --no-sign-request s3://openneuro.org/{{ dataset?.dataset_id }} {{ dataset?.dataset_id }}</pre>
          </div>
        </div>
        
        <div class="method">
          <h5>方法2: 使用 DataLad 下载</h5>
          <p>有python环境和github账号情况下：</p>
          <div class="code-block">
            <pre>pip install datalad
# 示例：从 OpenNeuro 下载数据集
datalad clone https://github.com/OpenNeuroDatasets/{{ dataset?.dataset_id }}.git
cd {{ dataset?.dataset_id }}
datalad get .  # 获取数据集所有完整文件
datalad status  # 查看数据集状态</pre>
          </div>
        </div>
        
        <div class="method">
          <h5>方法3: 使用 OpenNeuro-py</h5>
          <p>基于python环境下：</p>
          <p>OpenNeuro-py<a href="https://github.com/hoechenberger/openneuro-py" target="_blank">详细介绍 </a></p>
          <div class="code-block">
            <pre>pip install openneuro-py
pip install ipywidgets
# 命令行进入要下载的目录后：
openneuro-py download --dataset={{ dataset?.dataset_id }}</pre>
          </div>
        </div>
      </div>
    </el-dialog>
  </AppLayout>
</template>

<style scoped>
.dataset-detail-container {
  padding: 0;
  max-width: 100%;
}

.back-button {
  margin-bottom: 20px;
}

.dataset-info-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.dataset-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-section {
  margin-bottom: 20px;
}

.info-section h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #606266;
}

.author-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.subjects-card {
  margin-bottom: 20px;
}

.participants-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.group-stats {
  margin-top: 20px;
}

.group-item {
  margin-bottom: 20px;
}

.group-item h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #606266;
}

/* 下载对话框样式 */
.download-methods {
  padding: 10px;
}

.download-methods h4 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 16px;
  color: #303133;
}

.method {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #EBEEF5;
}

.method:last-child {
  border-bottom: none;
}

.method h5 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 15px;
  color: #303133;
}

.method p {
  margin: 5px 0;
  color: #606266;
}

.code-block {
  background-color: #282c34;
  padding: 15px;
  border-radius: 6px;
  margin-top: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  position: relative;
}

.code-block pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  font-size: 13px;
  color: #e6e6e6;
  line-height: 1.5;
  text-align: left;
  padding-left: 0;
}

.code-block p {
  color: #e6e6e6;
  margin-bottom: 8px;
}

.code-block a {
  color: #61afef;
  text-decoration: none;
}

.code-block a:hover {
  text-decoration: underline;
}

/* 响应式布局 */
@media (max-width: 992px) {
  :deep(.el-descriptions) {
    width: 100%;
  }
  
  :deep(.el-descriptions__body) {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .card-header h2 {
    margin-bottom: 10px;
  }
  
  :deep(.el-descriptions__cell) {
    padding: 8px !important;
  }
  
  :deep(.el-descriptions__label) {
    width: 80px;
  }
}

@media (max-width: 576px) {
  :deep(.el-table) {
    font-size: 12px;
  }
  
  :deep(.el-button--small) {
    padding: 6px 10px;
    font-size: 12px;
  }
}
</style> 