<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ipLocationApi } from '../../api/index'
import CollectionStatus from '../../components/ip-location/CollectionStatus.vue'

const router = useRouter()
const route = useRoute()

const activeTab = ref('search')
const collectionStatus = ref(null)
const loadingStatus = ref(false)

const tabs = [
  { label: 'IP 搜索', name: 'search', path: '/ip-location/search' },
  { label: 'IP 列表', name: 'list', path: '/ip-location/list' }
]

const fetchCollectionStatus = async () => {
  try {
    loadingStatus.value = true
    const response = await ipLocationApi.getCollectionStatus()
    collectionStatus.value = response
  } catch (error) {
    console.error('获取收集状态失败:', error)
  } finally {
    loadingStatus.value = false
  }
}

const triggerCollection = async () => {
  try {
    loadingStatus.value = true
    const response = await ipLocationApi.triggerCollection()
    if (response.success) {
      ElMessage.success(response.message)
      // 刷新状态
      await fetchCollectionStatus()
    } else {
      ElMessage.warning(response.message)
    }
  } catch (error) {
    console.error('触发收集失败:', error)
    ElMessage.error('触发收集失败')
  } finally {
    loadingStatus.value = false
  }
}

const handleTabChange = (tabName) => {
  const tab = tabs.find(t => t.name === tabName)
  if (tab) {
    router.push(tab.path)
  }
}

// 初始化
fetchCollectionStatus()
</script>

<template>
  <div class="ip-location-index">
    <div class="header">
      <h2>IP 地址定位</h2>
      <div class="header-actions">
        <CollectionStatus
          :status="collectionStatus"
          :loading="loadingStatus"
          @refresh="fetchCollectionStatus"
          @trigger="triggerCollection"
        />
      </div>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="main-tabs">
      <el-tab-pane
        v-for="tab in tabs"
        :key="tab.name"
        :label="tab.label"
        :name="tab.name"
      />
    </el-tabs>

    <div class="tab-content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.ip-location-index {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.main-tabs {
  margin-bottom: 20px;
}

.tab-content {
  min-height: 400px;
}
</style>
