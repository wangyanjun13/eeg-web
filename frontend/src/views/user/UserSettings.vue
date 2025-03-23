<script setup>
import AppLayout from '../../components/AppLayout.vue';
</script>

<template>
  <AppLayout>
    <div class="settings-container">
      <h1 class="page-title">用户设置</h1>
      <p class="page-description">此页面正在开发中，敬请期待！</p>
    </div>
  </AppLayout>
</template>

<style scoped>
.settings-container {
  padding: 20px; /* 容器内边距 */
  max-width: 1200px; /* 最大宽度 */
  margin: 0 auto; /* 居中显示 */
}

.page-title {
  font-size: 24px; /* 标题字体大小 */
  font-weight: 600; /* 标题字体粗细 */
  margin-bottom: 20px; /* 标题下方间距 */
  color: #333; /* 标题颜色 */
}

.page-description {
  font-size: 16px; /* 描述文字大小 */
  color: #666; /* 描述文字颜色 */
}
</style> 