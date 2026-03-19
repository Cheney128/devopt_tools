<script setup>
import { ref } from 'vue'
import { ElMessage, ElInput, ElButton, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { ipLocationApi } from '../../api/index'

const searchIP = ref('')
const loading = ref(false)
const searchResults = ref([])
const searched = ref(false)

const handleSearch = async () => {
  if (!searchIP.value || !searchIP.value.trim()) {
    ElMessage.warning('请输入要搜索的 IP 地址')
    return
  }

  // 简单的 IP 格式验证
  const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/
  if (!ipPattern.test(searchIP.value)) {
    ElMessage.warning('请输入有效的 IP 地址格式')
    return
  }

  try {
    loading.value = true
    searched.value = true
    const response = await ipLocationApi.searchIP(searchIP.value.trim())

    if (response.success) {
      searchResults.value = response.locations || []
      if (searchResults.value.length === 0) {
        ElMessage.info('未找到该 IP 的定位信息')
      } else {
        ElMessage.success(`找到 ${searchResults.value.length} 条记录`)
      }
    } else {
      ElMessage.error(response.message || '搜索失败')
      searchResults.value = []
    }
  } catch (error) {
    console.error('搜索 IP 失败:', error)
    ElMessage.error('搜索失败，请稍后重试')
    searchResults.value = []
  } finally {
    loading.value = false
  }
}

const handleKeyPress = (event) => {
  if (event.key === 'Enter') {
    handleSearch()
  }
}

const getConfidenceType = (confidence) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.5) return 'warning'
  return 'danger'
}

const getConfidenceText = (confidence) => {
  if (confidence >= 0.8) return '高'
  if (confidence >= 0.5) return '中'
  return '低'
}

const formatLastSeen = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="ip-location-search">
    <div class="search-section">
      <el-input
        v-model="searchIP"
        placeholder="请输入要搜索的 IP 地址，例如: 10.23.2.74"
        size="large"
        clearable
        @keyup.enter="handleKeyPress"
        class="search-input"
      >
        <template #append>
          <el-button
            :icon="Search"
            :loading="loading"
            type="primary"
            @click="handleSearch"
          >
            搜索
          </el-button>
        </template>
      </el-input>
    </div>

    <div v-if="searched" class="results-section">
      <div class="results-header">
        <h3>搜索结果</h3>
        <span class="results-count">共 {{ searchResults.length }} 条记录</span>
      </div>

      <el-table
        v-loading="loading"
        :data="searchResults"
        stripe
        style="width: 100%"
        empty-text="未找到相关记录"
      >
        <el-table-column prop="ip_address" label="IP 地址" width="150" />
        <el-table-column prop="mac_address" label="MAC 地址" width="170" />
        <el-table-column prop="device_hostname" label="设备主机名" min-width="150" />
        <el-table-column prop="device_ip" label="设备 IP" width="140" />
        <el-table-column prop="interface" label="接口" width="140" />
        <el-table-column prop="vlan_id" label="VLAN" width="80">
          <template #default="{ row }">
            {{ row.vlan_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="100">
          <template #default="{ row }">
            <el-tag :type="getConfidenceType(row.confidence)" size="small">
              {{ getConfidenceText(row.confidence) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后发现时间" width="180">
          <template #default="{ row }">
            {{ formatLastSeen(row.last_seen) }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">🔍</div>
      <div class="empty-text">输入 IP 地址开始搜索</div>
      <div class="empty-hint">支持搜索活跃设备的 IP 接入位置</div>
    </div>
  </div>
</template>

<style scoped>
.ip-location-search {
  padding: 0;
}

.search-section {
  margin-bottom: 30px;
}

.search-input {
  max-width: 600px;
}

.results-section {
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.results-header h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.results-count {
  color: #909399;
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 18px;
  margin-bottom: 8px;
  color: #606266;
}

.empty-hint {
  font-size: 14px;
  color: #909399;
}
</style>
