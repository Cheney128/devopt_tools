<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElInput, ElButton, ElTable, ElTableColumn, ElPagination } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ipLocationApi } from '../../api/index'

const loading = ref(false)
const ipList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const searchKeyword = ref('')

const fetchIPList = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchKeyword.value && searchKeyword.value.trim()) {
      params.search = searchKeyword.value.trim()
    }

    const response = await ipLocationApi.getIPList(params)
    ipList.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取 IP 列表失败:', error)
    ElMessage.error('获取 IP 列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchIPList()
}

const handleRefresh = () => {
  searchKeyword.value = ''
  currentPage.value = 1
  fetchIPList()
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  fetchIPList()
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
  fetchIPList()
}

const formatLastSeen = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchIPList()
})
</script>

<template>
  <div class="ip-location-list">
    <div class="filter-section">
      <div class="filter-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索 IP 地址"
          clearable
          style="width: 300px"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch">搜索</el-button>
          </template>
        </el-input>
      </div>
      <div class="filter-right">
        <el-button :icon="Refresh" @click="handleRefresh">刷新</el-button>
      </div>
    </div>

    <div class="table-section">
      <el-table
        v-loading="loading"
        :data="ipList"
        stripe
        style="width: 100%"
        empty-text="暂无数据"
      >
        <el-table-column prop="ip_address" label="IP 地址" width="150" />
        <el-table-column prop="mac_address" label="MAC 地址" width="170" />
        <el-table-column prop="device_hostname" label="设备主机名" min-width="150" />
        <el-table-column prop="interface" label="接口" width="140" />
        <el-table-column prop="vlan_id" label="VLAN" width="80">
          <template #default="{ row }">
            {{ row.vlan_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="最后发现时间" width="180">
          <template #default="{ row }">
            {{ formatLastSeen(row.last_seen) }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-section">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<style scoped>
.ip-location-list {
  padding: 0;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-left,
.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.table-section {
  margin-bottom: 20px;
}

.pagination-section {
  display: flex;
  justify-content: flex-end;
}
</style>
