<script setup>
import { ref, onMounted } from 'vue'

const message = ref('欢迎使用交换机管理系统')

onMounted(() => {
  console.log('HomeView mounted')
  console.log('Message:', message.value)
})
</script>

<template>
  <div class="home-view" style="padding: 20px;">
    <h1>{{ message }}</h1>
    <p>系统状态：正常运行</p>
    <p>如果您看到这个内容，说明Vue正确渲染</p>
  </div>
</template>

<style scoped>
.home-view {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
}

h1 {
  color: #1890ff;
  margin-bottom: 20px;
}
</style>
