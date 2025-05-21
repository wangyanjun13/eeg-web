<script setup>
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { Delete, Upload, Document, Download, RefreshRight, Connection } from '@element-plus/icons-vue';
import AppLayout from '@/components/layout/AppLayout.vue';
import datasetService from '@/services/dataset';
import { formatDate } from '@/utils/formatters';
import { useLoading } from '@/composables/useLoading';

const router = useRouter();
const { isLoading: loading, withLoading } = useLoading(true);

// 文件列表
const fileList = ref([]);
const activeTab = ref('all'); // 默认显示所有文件，可选值：all, data, model

// 获取文件列表
const fetchFiles = async () => {
  try {
    const response = await withLoading(datasetService.getMyFiles());
    
    // 健壮性检查 - 防止response为undefined
    if (!response) {
      console.warn('API返回为空，设置空文件列表');
      fileList.value = [];
      return;
    }
    
    console.log('获取到文件列表响应:', response);
    console.log('响应类型:', typeof response);
    console.log('响应是否包含files属性:', 'files' in response);
    if (response.files) console.log('files类型:', typeof response.files, '长度:', response.files.length);
    
    // 直接使用response而不是response.data
    if (response.status === 'success' && Array.isArray(response.files)) {
      // 按上传时间降序排序
      const sortedFiles = [...response.files].sort((a, b) => {
        // 使用上传时间排序，降序（最新的在前面）
        return b.upload_time?.localeCompare(a.upload_time) || 0;
      });
      console.log('已排序的文件列表:', sortedFiles);
      fileList.value = sortedFiles;
    } else if (response.status === 'error') {
      // 显性错误
      console.warn('API返回错误状态:', response.message || '未知错误');
      fileList.value = [];
    } else {
      // 回退处理，如果响应格式不符合预期
      fileList.value = [];
      console.warn('文件列表响应格式不符合预期:', response);
    }
  } catch (error) {
    console.error('获取文件列表失败:', error);
    ElMessage.error('获取文件列表失败，请重试');
    fileList.value = []; // 确保在错误时文件列表为空
  }
};

// 根据标签筛选文件
const filteredFiles = computed(() => {
  if (activeTab.value === 'all') {
    return fileList.value;
  }
  return fileList.value.filter(file => file.file_type === activeTab.value);
});

// 处理标签切换
const handleTabChange = (tab) => {
  activeTab.value = tab;
};

// 上传新文件
const handleUpload = () => {
  router.push('/upload-file');
};

// 下载文件
const handleDownload = async (file) => {
  try {
    console.log('准备下载文件:', file);
    await datasetService.downloadFile(file.id);
    ElMessage.success('文件下载已开始');
  } catch (error) {
    console.error('文件下载失败:', error);
    ElMessage.error('文件下载失败，请重试');
  }
};

// 删除文件
const handleDelete = async (file) => {
  try {
    console.log('准备删除文件:', file);
    await ElMessageBox.confirm(
      `确定要删除文件 "${file.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    await datasetService.deleteFile(file.id);
    ElMessage.success('文件删除成功');
    fetchFiles(); // 刷新文件列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件失败:', error);
      ElMessage.error('删除文件失败，请重试');
    }
  }
};

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size) return '未知';
  
  const KB = 1024;
  const MB = KB * 1024;
  const GB = MB * 1024;
  
  if (size < KB) {
    return size + ' B';
  } else if (size < MB) {
    return (size / KB).toFixed(2) + ' KB';
  } else if (size < GB) {
    return (size / MB).toFixed(2) + ' MB';
  } else {
    return (size / GB).toFixed(2) + ' GB';
  }
};

// 获取文件图标和颜色
const getFileTypeInfo = (fileType, fileFormat) => {
  if (fileType === 'data') {
    return {
      icon: Document,
      color: 'var(--button-use)',
      label: '数据文件'
    };
  } else if (fileType === 'model') {
    return {
      icon: Document,
      color: 'var(--success-color)',
      label: '模型文件'
    };
  } else {
    return {
      icon: Document,
      color: '#909399',
      label: '其他文件'
    };
  }
};

// 页面加载时获取文件列表
onMounted(() => {
  console.log('MyFiles 组件已挂载，准备获取文件列表');
  
  // 获取路由查询参数，检查是否需要刷新
  const refreshParam = new URLSearchParams(window.location.search).get('refresh');
  if (refreshParam === 'true') {
    console.log('检测到refresh参数，强制刷新文件列表');
    refreshFiles();
    
    // 清除URL参数，避免刷新页面时重复触发
    const url = new URL(window.location.href);
    url.searchParams.delete('refresh');
    window.history.replaceState({}, '', url);
  } else {
    fetchFiles();
  }
});

// 添加刷新功能
const refreshFiles = async () => {
  console.log('手动刷新文件列表');
  // 强制重新获取文件列表
  try {
    // 先显示加载中状态
    loading.value = true;
    ElMessage.info('正在刷新文件列表...');
    
    // 使用fetch直接调用API，绕过缓存
    const response = await fetch('/api/upload/files?_=' + new Date().getTime(), {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error('刷新文件列表失败');
    }
    
    const data = await response.json();
    console.log('直接通过fetch获取的文件列表:', data);
    
    // 重新调用获取文件的标准函数
    await fetchFiles();
    
    ElMessage.success('文件列表已刷新');
  } catch (error) {
    console.error('刷新文件列表失败:', error);
    ElMessage.error('刷新文件列表失败，请手动刷新即可');
  } finally {
    loading.value = false;
  }
};

// 在页面中显示文件列表的实际内容
const debugInfo = ref(false);
const toggleDebugInfo = () => {
  debugInfo.value = !debugInfo.value;
};

// 添加数据文件与模型整合功能
const integrateModel = (file) => {
  // 只有数据文件才能进行整合操作
  if (file.file_type !== 'data') {
    ElMessage.warning('只能对数据文件进行预测可视化');
    return;
  }
  
  // 获取可用的模型文件
  const modelFiles = fileList.value.filter(f => f.file_type === 'model');
  if (modelFiles.length === 0) {
    ElMessage.warning('没有可用的模型文件，请先上传模型');
    return;
  }
  
  // 生成模型选项的HTML
  const modelOptions = modelFiles.map(model => {
    const formattedDate = formatDate(model.upload_time, 'MM-DD HH:mm');
    return `<option value="${model.id}">${model.name} (${model.file_format || 'h5'}) - ${formattedDate}</option>`;
  }).join('');
  
  // 使用自定义HTML的对话框
  ElMessageBox({
    title: '选择模型进行预测',
    dangerouslyUseHTMLString: true,
    message: `
      <div>
        <p>请选择要用于预测的模型:</p>
        <div style="margin: 15px 0;">
          <select id="model-select" class="el-select" style="width: 100%; padding: 8px; border: 1px solid #DCDFE6; border-radius: 4px; font-size: 14px;">
            ${modelOptions}
          </select>
        </div>
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 13px;">
          <p style="margin-top: 0; font-weight: bold;">数据匹配提示：</p>
          <ul style="margin-bottom: 0; padding-left: 20px;">
            <li>选择与数据格式匹配的模型，如单通道数据应选择单通道模型</li>
            <li>数据维度应与模型期望的输入维度匹配</li>
            <li>对于样本集数据（如EMG_epochs），系统将选择第一个样本进行预测</li>
          </ul>
        </div>
      </div>
    `,
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  }).then(() => {
    // 从DOM中获取选择的模型ID
    const selectElement = document.getElementById('model-select');
    const modelId = selectElement ? selectElement.value : null;
    
    if (!modelId) {
      ElMessage.warning('未选择模型');
      return;
    }
    
    // 找到选中的模型信息
    const selectedModel = modelFiles.find(m => m.id === modelId);
    
    // 显示即将整合的信息
    ElMessageBox.confirm(
      `<div>
        <p>确定要对数据文件 "${file.name}" 使用模型 "${selectedModel.name}" 进行预测可视化吗？</p>
        <div style="background-color: #eef6ff; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 13px;">
          <p style="margin-top: 0; font-weight: bold;">系统将：</p>
          <ul style="margin-bottom: 0; padding-left: 20px;">
            <li>自动检测模型类型（fcNN、CNN等）</li>
            <li>根据数据形状和文件名进行适当的预处理</li>
            <li>将数据转换为模型所需的输入格式</li>
            <li>运行模型并可视化结果</li>
          </ul>
        </div>
      </div>`,
      '预测确认',
      {
        confirmButtonText: '开始预测',
        cancelButtonText: '取消',
        type: 'info',
        dangerouslyUseHTMLString: true
      }
    ).then(() => {
      // 在这里导航到模型可视化页面，携带数据文件和模型的信息
      router.push({
        path: '/model-visualization',
        query: {
          dataFileId: file.id,
          modelFileId: modelId
        }
      });
    }).catch(() => {
      // 用户取消整合
    });
  }).catch(() => {
    // 用户取消选择模型
  });
};

// 添加可视化中心功能
const openTestingCenter = () => {
  // 统计数据文件和模型文件数量
  const dataFiles = fileList.value.filter(f => f.file_type === 'data');
  const modelFiles = fileList.value.filter(f => f.file_type === 'model');
  
  if (dataFiles.length === 0) {
    ElMessage.warning('请先上传数据文件才能进行模型预测可视化');
    return;
  }
  
  if (modelFiles.length === 0) {
    ElMessage.warning('请先上传模型文件才能进行模型预测可视化');
    return;
  }
  
  // 打开可视化中心对话框
  ElMessageBox({
    title: '数据模型可视化中心',
    dangerouslyUseHTMLString: true,
    message: `
      <div style="text-align: left;">
        <div style="margin-bottom: 15px; background-color: #f0f9eb; padding: 10px; border-radius: 4px;">
          <p style="margin: 0; font-weight: bold;">可用资源:</p>
          <div style="display: flex; margin-top: 8px;">
            <div style="flex: 1;">
              <p style="margin: 5px 0;"><strong>数据文件:</strong> ${dataFiles.length}个</p>
              <ul style="margin: 0; padding-left: 20px;">
                ${dataFiles.slice(0, 3).map(file => `<li>${file.name}</li>`).join('')}
                ${dataFiles.length > 3 ? `<li>...等${dataFiles.length}个文件</li>` : ''}
              </ul>
            </div>
            <div style="flex: 1;">
              <p style="margin: 5px 0;"><strong>模型文件:</strong> ${modelFiles.length}个</p>
              <ul style="margin: 0; padding-left: 20px;">
                ${modelFiles.slice(0, 3).map(file => `<li>${file.name}</li>`).join('')}
                ${modelFiles.length > 3 ? `<li>...等${modelFiles.length}个文件</li>` : ''}
              </ul>
            </div>
          </div>
        </div>
        
        <p style="margin-bottom: 10px;">请选择要预测的数据文件:</p>
        <select id="data-file-select" class="el-select" style="width: 100%; padding: 8px; border: 1px solid #DCDFE6; border-radius: 4px; margin-bottom: 15px; font-size: 14px;">
          ${dataFiles.map(file => `<option value="${file.id}">${file.name} (${file.file_format || '未知'}) - ${formatDate(file.upload_time, 'MM-DD HH:mm')}</option>`).join('')}
        </select>
        
        <p style="margin-bottom: 10px;">请选择要使用的模型:</p>
        <select id="model-file-select" class="el-select" style="width: 100%; padding: 8px; border: 1px solid #DCDFE6; border-radius: 4px; font-size: 14px;">
          ${modelFiles.map(model => `<option value="${model.id}">${model.name} (${model.file_format || 'h5'}) - ${formatDate(model.upload_time, 'MM-DD HH:mm')}</option>`).join('')}
        </select>
        
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 15px; font-size: 13px;">
          <p style="margin-top: 0; font-weight: bold;">数据匹配提示：</p>
          <ul style="margin-bottom: 0; padding-left: 20px;">
            <li>选择与数据格式匹配的模型，如单通道数据应选择单通道模型</li>
            <li>数据维度应与模型期望的输入维度匹配</li>
            <li>对于样本集数据，系统将选择第一个样本进行预测</li>
          </ul>
        </div>
      </div>
    `,
    showCancelButton: true,
    confirmButtonText: '开始预测',
    cancelButtonText: '取消',
    customClass: 'testing-center-dialog',
  }).then(() => {
    // 获取选中的数据文件和模型ID
    const dataFileId = document.getElementById('data-file-select').value;
    const modelFileId = document.getElementById('model-file-select').value;
    
    if (!dataFileId || !modelFileId) {
      ElMessage.warning('请选择数据文件和模型文件');
      return;
    }
    
    // 找到选中的文件信息
    const selectedData = dataFiles.find(f => f.id === dataFileId);
    const selectedModel = modelFiles.find(m => m.id === modelFileId);
    
    // 确认选择
    ElMessageBox.confirm(
      `<div>
        <p>确认开始预测可视化:</p>
        <ul style="text-align: left; margin-bottom: 15px;">
          <li><strong>数据文件:</strong> ${selectedData.name}</li>
          <li><strong>模型文件:</strong> ${selectedModel.name}</li>
        </ul>
        <div style="background-color: #eef6ff; padding: 10px; border-radius: 4px; text-align: left; font-size: 13px;">
          <p style="margin-top: 0; font-weight: bold;">系统将：</p>
          <ul style="margin-bottom: 0; padding-left: 20px;">
            <li>自动检测模型类型（fcNN、CNN等）</li>
            <li>根据数据形状和文件名进行适当的预处理</li>
            <li>将数据转换为模型所需的输入格式</li>
            <li>运行模型并可视化结果</li>
          </ul>
        </div>
      </div>`,
      '预测确认',
      {
        confirmButtonText: '开始预测',
        cancelButtonText: '返回',
        type: 'info',
        dangerouslyUseHTMLString: true
      }
    ).then(() => {
      // 导航到模型可视化页面
      router.push({
        path: '/model-visualization',
        query: {
          dataFileId,
          modelFileId
        }
      });
    }).catch(() => {
      // 用户取消，返回可视化中心
      openTestingCenter();
    });
  }).catch(() => {
    // 用户取消
  });
};

// 从模型文件发起预测流程
const testWithModel = (modelFile) => {
  // 获取可用的数据文件
  const dataFiles = fileList.value.filter(f => f.file_type === 'data');
  if (dataFiles.length === 0) {
    ElMessage.warning('没有可用的数据文件，请先上传数据文件');
    return;
  }
  
  // 生成数据文件选项的HTML
  const dataOptions = dataFiles.map(data => {
    const formattedDate = formatDate(data.upload_time, 'MM-DD HH:mm');
    return `<option value="${data.id}">${data.name} (${data.file_format || '未知'}) - ${formattedDate}</option>`;
  }).join('');
  
  // 使用自定义HTML的对话框
  ElMessageBox({
    title: `使用"${modelFile.name}"模型预测数据`,
    dangerouslyUseHTMLString: true,
    message: `
      <div>
        <p>请选择要预测的数据文件:</p>
        <div style="margin: 15px 0;">
          <select id="data-select" class="el-select" style="width: 100%; padding: 8px; border: 1px solid #DCDFE6; border-radius: 4px; font-size: 14px;">
            ${dataOptions}
          </select>
        </div>
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 13px;">
          <p style="margin-top: 0; font-weight: bold;">数据匹配提示：</p>
          <ul style="margin-bottom: 0; padding-left: 20px;">
            <li>选择与模型兼容的数据格式，如单通道模型应选择单通道数据</li>
            <li>数据维度应与模型期望的输入维度匹配</li>
            <li>对于样本集数据（如EMG_epochs），系统将选择第一个样本进行预测</li>
          </ul>
        </div>
      </div>
    `,
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  }).then(() => {
    // 从DOM中获取选择的数据文件ID
    const selectElement = document.getElementById('data-select');
    const dataFileId = selectElement ? selectElement.value : null;
    
    if (!dataFileId) {
      ElMessage.warning('未选择数据文件');
      return;
    }
    
    // 找到选中的数据文件信息
    const selectedData = dataFiles.find(d => d.id === dataFileId);
    
    // 显示即将预测的信息
    ElMessageBox.confirm(
      `<div>
        <p>确定要使用模型"${modelFile.name}"对数据文件"${selectedData.name}"进行预测吗？</p>
        <div style="background-color: #eef6ff; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 13px;">
          <p style="margin-top: 0; font-weight: bold;">系统将：</p>
          <ul style="margin-bottom: 0; padding-left: 20px;">
            <li>自动检测模型类型（fcNN、CNN等）</li>
            <li>根据数据形状和文件名进行适当的预处理</li>
            <li>将数据转换为模型所需的输入格式</li>
            <li>运行模型并可视化结果</li>
          </ul>
        </div>
      </div>`,
      '预测确认',
      {
        confirmButtonText: '开始预测',
        cancelButtonText: '取消',
        type: 'info',
        dangerouslyUseHTMLString: true
      }
    ).then(() => {
      // 在这里导航到模型可视化页面，携带数据文件和模型的信息
      router.push({
        path: '/model-visualization',
        query: {
          dataFileId: dataFileId,
          modelFileId: modelFile.id
        }
      });
    }).catch(() => {
      // 用户取消预测
    });
  }).catch(() => {
    // 用户取消选择数据文件
  });
};
</script>

<template>
  <AppLayout>
    <div class="my-files-container">
      <!-- 添加独立的返回按钮区域 -->
      <div class="back-button">
        <el-button @click="router.push('/datasets')" icon="ArrowLeft" size="small" text>返回数据集</el-button>
      </div>

      <div class="page-header">
        <h1>我的文件</h1>
        <div class="header-actions">
          <el-button v-if="fileList.filter(f => f.file_type === 'data').length > 0 && fileList.filter(f => f.file_type === 'model').length > 0" 
            type="success" @click="openTestingCenter" class="visualization-btn">
            <el-icon><component :is="Connection" /></el-icon> 数据模型可视化
          </el-button>
          <el-button @click="refreshFiles" class="refresh-btn">
            <el-icon><RefreshRight /></el-icon> 刷新
          </el-button>
          <el-button type="primary" @click="handleUpload">
            <el-icon><Upload /></el-icon> 上传文件
          </el-button>
        </div>
      </div>
      
      <!-- 文件类型标签页 -->
      <div class="tabs-container">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="全部文件" name="all"></el-tab-pane>
          <el-tab-pane label="数据文件" name="data"></el-tab-pane>
          <el-tab-pane label="模型文件" name="model"></el-tab-pane>
        </el-tabs>
      </div>
      
      <!-- 文件列表 -->
      <div class="files-list">
        <el-card shadow="hover" class="file-list-card">
          <el-table
            :data="filteredFiles"
            v-loading="loading"
            style="width: 100%"
            :empty-text="loading ? '加载中...' : '暂无文件'"
          >
            <el-table-column label="文件名" min-width="240">
              <template #default="{ row }">
                <div class="file-name">
                  <el-icon :color="getFileTypeInfo(row.file_type, row.file_format).color">
                    <component :is="getFileTypeInfo(row.file_type, row.file_format).icon" />
                  </el-icon>
                  <span class="file-title">{{ row.name }}</span>
                  <el-tag size="small" :type="row.file_type === 'data' ? 'primary' : 'success'">
                    {{ getFileTypeInfo(row.file_type, row.file_format).label }}
                  </el-tag>
                  <el-tag v-if="row.file_type === 'data' && fileList.some(f => f.file_type === 'model')" 
                    size="small" type="info" effect="plain" class="model-ready-tag">
                    可使用
                  </el-tag>
                  <el-tag v-if="row.file_type === 'model' && fileList.some(f => f.file_type === 'data')" 
                    size="small" type="info" effect="plain" class="model-ready-tag">
                    可预测
                  </el-tag>
                </div>
                <div class="file-description" v-if="row.description">
                  {{ row.description }}
                </div>
              </template>
            </el-table-column>
            
            <el-table-column label="格式" width="100">
              <template #default="{ row }">
                <el-tag size="small" type="info" v-if="row.file_format">
                  {{ row.file_format }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            
            <el-table-column label="大小" width="120">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            
            <el-table-column label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.upload_time) || '-' }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button
                    type="primary"
                    size="small"
                    text
                    @click="handleDownload(row)"
                    title="下载"
                  >
                    <el-icon><Download /></el-icon>
                    <span>下载</span>
                  </el-button>
                  
                  <!-- 添加预测按钮，对数据文件和模型文件分别显示不同文本 -->
                  <el-button
                    v-if="row.file_type === 'data'"
                    type="success"
                    size="small"
                    text
                    @click="integrateModel(row)"
                    title="使用模型预测此数据"
                  >
                    <el-icon><component :is="Connection" /></el-icon>
                    <span>模型预测</span>
                  </el-button>

                  <!-- 添加预测按钮，对模型文件显示 -->
                  <el-button
                    v-if="row.file_type === 'model'"
                    type="success"
                    size="small"
                    text
                    @click="testWithModel(row)"
                    title="使用此模型预测数据"
                  >
                    <el-icon><component :is="Connection" /></el-icon>
                    <span>预测数据</span>
                  </el-button>
                  
                  <!-- 删除按钮 -->
                  <el-button
                    type="danger"
                    size="small"
                    @click="handleDelete(row)"
                    title="删除"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 空状态 -->
          <el-empty v-if="filteredFiles.length === 0 && !loading" description='暂无文件，点击上方"上传文件"按钮添加文件'>
            <el-button type="primary" @click="handleUpload">上传文件</el-button>
          </el-empty>
        </el-card>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.my-files-container {
  padding: 0;
}

.back-button {
  margin-bottom: 10px;
  text-align: left;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.tabs-container {
  margin-bottom: 20px;
}

.file-list-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-title {
  font-weight: 500;
  margin-right: 8px;
  flex: 1;
}

.file-description {
  color: #606266;
  font-size: 13px;
  margin-top: 4px;
}

.table-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
}

.debug-panel {
  margin-top: 20px;
  padding: 10px;
  background-color: #f8f8f8;
  border: 1px dashed #ddd;
  border-radius: 5px;
  font-family: monospace;
  overflow: auto;
}

.debug-panel pre {
  margin: 5px 0;
  white-space: pre-wrap;
}

.model-ready-tag {
  margin-left: 5px;
  font-size: 11px;
  opacity: 0.8;
}

/* 可预测标签样式 */
:deep(.model-ready-tag) {
  background-color: white !important;
  border-color: var(--el-color-info) !important;
  color: var(--el-color-info) !important;
}

/* 文件类型标签样式 */
:deep(.el-tag--primary.el-tag--light),
:deep(.el-tag--success.el-tag--light) {
  background-color: white !important;
}

/* 刷新按钮样式 */
.refresh-btn {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

/* 数据模型可视化按钮样式 */
.visualization-btn {
  background-color: var(--success-color) !important;
  border-color: var(--success-color) !important;
  color: white !important;
}

.visualization-btn:hover {
  background-color: var(--success-color) !important;
  border-color: var(--success-color) !important;
  opacity: 1 !important;
}
</style>