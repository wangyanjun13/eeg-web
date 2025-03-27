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
    console.error('获取受试者列表失败:', error);
    ElMessage.error('获取受试者列表失败');
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
          </div>
        </template>

        <div v-if="dataset" class="dataset-info">
          <!-- 基本信息部分 -->
          <div class="info-section">
            <h3>基本信息</h3>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="数据集ID">{{ dataset.dataset_id }}</el-descriptions-item>
              <el-descriptions-item label="受试者数量">{{ dataset.subject_count }}</el-descriptions-item>
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
            <h3>受试者信息</h3>
            <el-tabs v-model="activeTab">
              <el-tab-pane label="受试者列表" name="subjects"></el-tab-pane>
              <el-tab-pane label="参与者统计" name="participants"></el-tab-pane>
            </el-tabs>
          </div>
        </template>

        <!-- 受试者列表标签页 -->
        <div v-if="activeTab === 'subjects'" v-loading="loading.subjects">
          <el-empty v-if="subjects.length === 0 && !loading.subjects" description="暂无受试者数据" />
          
          <el-table v-else :data="subjects" style="width: 100%" border stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="subject" label="受试者" />
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
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button size="small" @click="viewSubject(scope.row.id)">查看</el-button>
                <el-button size="small" type="primary" @click="analyzeSubject(scope.row.id)">分析</el-button>
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
  </AppLayout>
</template>

<style scoped>
.dataset-detail-container {
  padding: 20px; /* 容器内边距 */
}

.back-button {
  margin-bottom: 20px; /* 返回按钮下方间距 */
}

.dataset-info-card {
  margin-bottom: 20px; /* 信息卡片下方间距 */
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
  gap: 20px; /* 信息部分间距 */
}

.info-section {
  margin-bottom: 20px; /* 信息部分下方间距 */
}

.info-section h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #606266;
}

.author-tag {
  margin-right: 8px; /* 作者标签右侧间距 */
  margin-bottom: 8px; /* 作者标签下方间距 */
}

.subjects-card {
  margin-bottom: 20px; /* 受试者卡片下方间距 */
}

.participants-info {
  display: flex;
  flex-direction: column;
  gap: 20px; /* 参与者信息间距 */
}

.group-stats {
  margin-top: 20px; /* 分组统计上方间距 */
}

.group-item {
  margin-bottom: 20px; /* 分组项下方间距 */
}

.group-item h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #606266;
}
</style> 