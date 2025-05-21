<script setup>
import { useRouter } from 'vue-router';
import AppLayout from '../components/layout/AppLayout.vue';

const router = useRouter();

function goHome() {
  router.push('/');
}
</script>

<template>
  <AppLayout>
    <div class="not-found-container">
      <div class="not-found-content">
        <h1 class="error-code">404</h1>
        <h2 class="error-title">页面未找到</h2>
        <p class="error-message">抱歉，您访问的页面不存在或已被移除。</p>
        <button class="return-button" @click="goHome">返回首页</button>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 120px);
  padding: 20px;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: var(--button-use);
  margin: 0;
  line-height: 1;
}

.error-title {
  font-size: 30px;
  margin: 20px 0;
  color: #333;
}

.error-message {
  font-size: 16px;
  color: #666;
  margin-bottom: 30px;
}

.return-button {
  background-color: var(--button-use);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.return-button:hover {
  background-color: #66b1ff;
}
</style> 