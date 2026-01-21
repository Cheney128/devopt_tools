<script setup>
import { ref } from 'vue'

const message = ref('欢迎测试页面')
</script>

<template>
  <div style="padding: 20px;">
    <h1>{{ message }}</h1>
    <p>如果您能看到这个内容，说明Vue正确渲染</p>
    <p>页面状态：正常运行</p>
  </div>
</template>

<style scoped>
h1 {
  color: #1890ff;
}
</style>
