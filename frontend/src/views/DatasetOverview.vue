<template>
  <div class="dataset-overview">
    <el-card>
      <template #header>
        <h2>数据集基本信息</h2>
      </template>
      <div class="info-content">
        <p>实验名称：{{ datasetInfo.Name }}</p>
        <p>参与者数量：48</p>
        <p>实验任务：Flankers任务</p>
        <p>EEG通道数：32</p>
      </div>
    </el-card>
    
    <el-card class="participant-stats">
      <template #header>
        <h2>参与者统计</h2>
      </template>
      <el-table :data="participantStats">
        <el-table-column prop="group" label="组别" />
        <el-table-column prop="count" label="人数" />
        <el-table-column prop="avgAge" label="平均年龄" />
      </el-table>
    </el-card>
  </div>
</template> 