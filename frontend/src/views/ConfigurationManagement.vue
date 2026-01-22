<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElDialog, ElTabs, ElTabPane, ElDivider, ElScrollbar } from 'element-plus'
import { Document, Download, Refresh } from '@element-plus/icons-vue'
import { configurationApi, deviceApi } from '../api/index'
import api from '../api/index'

// 响应式数据
const loading = ref(false)
const configurations = ref([])
const devices = ref([])
const selectedDeviceId = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const showConfigDialog = ref(false)
const currentConfig = ref(null)
const selectedConfigVersion = ref(null)
const showDiffDialog = ref(false)
const diffContent = ref('')
const diffConfig1 = ref(null)
const diffConfig2 = ref(null)

// 计算属性：分页后的配置列表
const paginatedConfigurations = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return configurations.value.slice(start, end)
})

// 方法
const fetchConfigurations = async () => {
  loading.value = true
  try {
    // 调用API获取配置列表
    const response = await configurationApi.getConfigurations()
    configurations.value = response || []
  } catch (error) {
    ElMessage.error('获取配置列表失败')
  } finally {
    loading.value = false
  }
}

const fetchDevices = async () => {
  try {
    // 调用API获取设备列表
    const response = await deviceApi.getDevices()
    devices.value = response || []
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  }
}

const getDeviceConfiguration = async (deviceId) => {
  if (!deviceId) {
    ElMessage.warning('请选择设备')
    return
  }
  
  loading.value = true
  try {
    // 调用API直接从设备获取配置
    const response = await configurationApi.collectConfigFromDevice(deviceId)
    if (response.success) {
      ElMessage.success(response.message)
      // 刷新配置列表
      fetchConfigurations()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const showConfiguration = (config) => {
  currentConfig.value = config
  showConfigDialog.value = true
}

const showDiff = (config) => {
  if (!selectedConfigVersion.value) {
    selectedConfigVersion.value = config
    ElMessage.info('请选择第二个版本进行比较')
    return
  }
  
  if (selectedConfigVersion.value.id === config.id) {
    ElMessage.warning('请选择不同的版本进行比较')
    return
  }
  
  // 确保config1的ID小于config2的ID，这样diff显示更直观
  if (selectedConfigVersion.value.id > config.id) {
    diffConfig1.value = config
    diffConfig2.value = selectedConfigVersion.value
  } else {
    diffConfig1.value = selectedConfigVersion.value
    diffConfig2.value = config
  }
  
  // 调用API获取diff
  fetchConfigDiff(diffConfig1.value.id, diffConfig2.value.id)
  selectedConfigVersion.value = null
}

const fetchConfigDiff = async (configId1, configId2) => {
  loading.value = true
  try {
    const response = await configurationApi.getConfigDiff(configId1, configId2)
    if (response.success) {
      diffContent.value = response.diff
      showDiffDialog.value = true
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('获取配置差异失败')
  } finally {
    loading.value = false
  }
}

const downloadConfiguration = (config) => {
  try {
    // 创建Blob对象
    const blob = new Blob([config.config_content], { type: 'text/plain' })
    // 创建下载链接
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${config.device_name}-config-${new Date(config.config_time).toISOString().slice(0, 10)}.txt`
    // 触发下载
    document.body.appendChild(a)
    a.click()
    // 清理
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    ElMessage.success('配置文件下载成功')
  } catch (error) {
    ElMessage.error('配置文件下载失败')
  }
}

// 生命周期钩子
onMounted(() => {
  fetchConfigurations()
  fetchDevices()
})
</script>

<template>
  <div class="configuration-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>配置管理</span>
        </div>
      </template>

      <!-- 设备选择 -->
      <div class="device-selection">
        <el-select
          v-model="selectedDeviceId"
          placeholder="选择设备获取配置"
          style="width: 300px"
        >
          <el-option
            v-for="device in devices"
            :key="device.id"
            :label="device.hostname"
            :value="device.id"
          />
        </el-select>
        <el-button
          type="success"
          @click="getDeviceConfiguration(selectedDeviceId)"
          :disabled="!selectedDeviceId"
          :loading="loading"
        >
          <el-icon><Document /></el-icon>
          获取配置
        </el-button>
      </div>

      <!-- 配置列表 -->
      <el-table
        v-loading="loading"
        :data="configurations"
        style="width: 100%; margin-top: 20px"
        @row-click="(row) => selectedConfigVersion = selectedConfigVersion ? null : row"
        :row-class-name="(row) => selectedConfigVersion && selectedConfigVersion.id === row.id ? 'selected-row' : ''"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_name" label="设备名称" min-width="120" />
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="config_time" label="配置时间" min-width="180">
          <template #default="scope">
            {{ new Date(scope.row.config_time).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="change_description" label="变更描述" min-width="200" />
        <el-table-column prop="git_commit_id" label="Git提交ID" min-width="150">
          <template #default="scope">
            <span v-if="scope.row.git_commit_id" class="commit-id">{{ scope.row.git_commit_id.substring(0, 8) }}</span>
            <span v-else class="no-commit">无</span>
          </template>
        </el-table-column>
        <el-table-column label="配置内容" min-width="120">
          <template #default="scope">
            <el-button size="small" @click="showConfiguration(scope.row)">查看</el-button>
          </template>
        </el-table-column>
        <el-table-column label="比较" min-width="120">
          <template #default="scope">
            <el-button size="small" type="primary" @click="showDiff(scope.row)">
              {{ selectedConfigVersion && selectedConfigVersion.id === scope.row.id ? '取消选择' : '选择比较' }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              @click="downloadConfiguration(scope.row)"
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="configurations.length"
        />
      </div>
    </el-card>

    <!-- 配置详情对话框 -->
    <el-dialog
      v-model="showConfigDialog"
      title="配置详情"
      width="80%"
      @close="() => { currentConfig.value = null }"
    >
      <template v-if="currentConfig">
        <div class="config-info">
          <p><strong>设备名称:</strong> {{ currentConfig.device_name }}</p>
          <p><strong>版本号:</strong> {{ currentConfig.version }}</p>
          <p><strong>配置时间:</strong> {{ new Date(currentConfig.config_time).toLocaleString() }}</p>
          <p><strong>变更描述:</strong> {{ currentConfig.change_description || '无' }}</p>
          <p v-if="currentConfig.git_commit_id"><strong>Git提交ID:</strong> {{ currentConfig.git_commit_id }}</p>
        </div>
        <el-divider />
        <div class="config-content">
          <h3>配置内容</h3>
          <el-scrollbar height="500px">
            <pre>{{ currentConfig.config_content }}</pre>
          </el-scrollbar>
        </div>
      </template>
    </el-dialog>

    <!-- 配置差异对话框 -->
    <el-dialog
      v-model="showDiffDialog"
      title="配置差异比较"
      width="80%"
      @close="() => { diffContent.value = ''; diffConfig1.value = null; diffConfig2.value = null }"
    >
      <template v-if="diffConfig1 && diffConfig2">
        <div class="diff-info">
          <h4>版本比较: {{ diffConfig1.version }} vs {{ diffConfig2.version }}</h4>
          <p><strong>设备名称:</strong> {{ diffConfig1.device_name }}</p>
          <p><strong>比较时间范围:</strong> {{ new Date(diffConfig1.config_time).toLocaleString() }} 至 {{ new Date(diffConfig2.config_time).toLocaleString() }}</p>
        </div>
        <el-divider />
        <div class="diff-content">
          <h3>配置差异</h3>
          <el-scrollbar height="500px">
            <pre v-if="diffContent">{{ diffContent }}</pre>
            <div v-else class="no-diff">配置无差异</div>
          </el-scrollbar>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.configuration-management {
  padding: 0 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-selection {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.selected-row {
  background-color: #e6f7ff !important;
}

.selected-row:hover {
  background-color: #bae7ff !important;
}

.commit-id {
  color: #1890ff;
  font-family: monospace;
}

.no-commit {
  color: #999;
  font-style: italic;
}

.config-info, .diff-info {
  margin-bottom: 15px;
}

.config-content h3, .diff-content h3 {
  margin-bottom: 10px;
  color: #303133;
}

.diff-content pre {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #303133;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
}

.no-diff {
  background-color: #f0f9eb;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
  padding: 15px;
  color: #52c41a;
  text-align: center;
}
</style>