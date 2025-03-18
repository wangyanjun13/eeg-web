<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import datasetService from '@/services/dataset';
import AppLayout from '@/components/AppLayout.vue';

const route = useRoute();
const router = useRouter();
const datasetId = route.params.id;

const dataset = ref(null);
const subjects = ref([]);
const participants = ref(null);
const participantsMap = ref({});  // 新增：用于存储受试者ID到人口统计学信息的映射
const loading = ref({
  dataset: false,
  subjects: false,
  participants: false
});
const activeTab = ref('subjects');

// 获取数据集详情
const fetchDatasetInfo = async () => {
  loading.value.dataset = true;
  try {
    const response = await datasetService.getDatasetById(datasetId);
    dataset.value = response.data;
  } catch (error) {
    console.error('获取数据集详情失败:', error);
    ElMessage.error('获取数据集详情失败');
  } finally {
    loading.value.dataset = false;
  }
};

// 获取受试者列表
const fetchSubjects = async () => {
  loading.value.subjects = true;
  try {
    const response = await datasetService.getDatasetSubjects(datasetId);
    subjects.value = response.data || [];
  } catch (error) {
    console.error('获取受试者列表失败:', error);
    ElMessage.error('获取受试者列表失败');
  } finally {
    loading.value.subjects = false;
  }
};

// 获取参与者信息
const fetchParticipantsInfo = async () => {
  loading.value.participants = true;
  try {
    const response = await datasetService.getParticipantsInfo(datasetId);
    participants.value = response.data;
    
    // 处理participants.tsv数据，创建ID到信息的映射
    if (response.data && response.data.participants) {
      const participantsData = response.data.participants;
      participantsMap.value = participantsData.reduce((map, participant) => {
        // 从participant_id中提取数字部分（例如从"sub-01"提取"01"）
        const idMatch = participant.participant_id.match(/sub-(\d+)/);
        if (idMatch) {
          const id = idMatch[1];
          map[id] = participant;
        }
        return map;
      }, {});
    }
  } catch (error) {
    console.error('获取参与者信息失败:', error);
    ElMessage.error('获取参与者信息失败');
  } finally {
    loading.value.participants = false;
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

      <!-- 数据集基本信息 -->
      <el-card v-loading="loading.dataset" class="dataset-info-card">
        <template #header>
          <div class="card-header">
            <h2 v-if="dataset">{{ dataset.Name }}</h2>
            <el-skeleton v-else :rows="1" animated />
          </div>
        </template>

        <div v-if="dataset" class="dataset-info">
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

          <div v-if="dataset.HowToAcknowledge" class="info-section">
            <h3>引用说明</h3>
            <p>{{ dataset.HowToAcknowledge }}</p>
          </div>
        </div>
        <el-skeleton v-else :rows="6" animated />
      </el-card>

      <!-- 受试者和参与者信息标签页 -->
      <el-card class="subjects-card">
        <template #header>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="受试者列表" name="subjects"></el-tab-pane>
            <el-tab-pane label="参与者统计" name="participants"></el-tab-pane>
          </el-tabs>
        </template>

        <!-- 受试者列表 -->
        <div v-if="activeTab === 'subjects'" v-loading="loading.subjects">
          <el-empty v-if="subjects.length === 0 && !loading.subjects" description="暂无受试者数据" />
          
          <el-table v-else :data="subjects" style="width: 100%" border stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="subject" label="受试者" />
            <el-table-column prop="format" label="格式" width="100" />
            
            <!-- 新增：年龄列 -->
            <el-table-column label="年龄" width="80">
              <template #default="{ row }">
                <span v-if="participantsMap[row.id] && participantsMap[row.id].Age">
                  {{ participantsMap[row.id].Age }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            
            <!-- 新增：性别列 -->
            <el-table-column label="性别" width="80">
              <template #default="{ row }">
                <span v-if="participantsMap[row.id] && participantsMap[row.id].Gender">
                  {{ participantsMap[row.id].Gender === 'M' ? '男' : participantsMap[row.id].Gender === 'F' ? '女' : participantsMap[row.id].Gender }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="viewSubject(row.id)">查看</el-button>
                <el-button size="small" type="primary" @click="analyzeSubject(row.id)">分析</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 参与者统计 -->
        <div v-else-if="activeTab === 'participants'" v-loading="loading.participants">
          <div v-if="participants" class="participants-info">
            <el-descriptions title="参与者统计" :column="1" border>
              <el-descriptions-item label="总人数">{{ participants.total_count }}</el-descriptions-item>
            </el-descriptions>

            <div v-if="participants.group_stats && Object.keys(participants.group_stats).length > 0" class="group-stats">
              <h3>分组统计</h3>
              <div v-for="(stats, group) in participants.group_stats" :key="group" class="group-item">
                <h4>{{ group }}</h4>
                <el-descriptions :column="2" border>
                  <el-descriptions-item 
                    v-for="(value, key) in stats" 
                    :key="key" 
                    :label="key"
                  >
                    {{ value }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </div>
          <el-empty v-else-if="!loading.participants" description="暂无参与者统计数据" />
        </div>
      </el-card>
    </div>
  </AppLayout>
</template>

<style scoped>
.dataset-detail-container {
  padding: 20px;
}

.back-button {
  margin-bottom: 20px;
}

.dataset-info-card {
  margin-bottom: 20px;
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
</style> 