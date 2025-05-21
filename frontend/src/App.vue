<script setup>
// App.vue - 应用程序入口点
</script>

<template>
  <router-view />
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: #ece3e6; /* 确保背景色应用于整个应用 */
  color: #ffffff;
}

#app {
  width: 100%;
  height: 100vh;
  background-color: #ece3e6; /* 应用背景色 */
}

/* 确保html和body元素也具有相同的背景色 */
html {
  background-color: #ece3e6;
}
</style>
