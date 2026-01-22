<template>
  <div class="configuration-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>配置管理</span>
        </div>
      </template>

      <div class="device-selection">
        <el-select
          v-model="selectedDeviceId"
          placeholder="选择设备获取配置"
          style="width: 300px"
        >
          <el-option
            v-for="device in deviceList"
            :key="device.id"
            :label="device.hostname"
            :value="device.id"
          />
        </el-select>
        <el-button
          type="success"
          @click="handleGetConfig"
          :disabled="!selectedDeviceId"
          :loading="loading"
        >
          <el-icon><Document /></el-icon>
          获取配置
        </el-button>
        <el-button
          type="primary"
          @click="handleBackupNow"
          :disabled="!selectedDeviceId"
          :loading="loading"
        >
          <el-icon><Upload /></el-icon>
          备份配置
        </el-button>
        <el-button
          type="warning"
          @click="handleOpenBackupDialog"
          :disabled="!selectedDeviceId"
        >
          <el-icon><Clock /></el-icon>
          备份设置
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="configList"
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_name" label="设备名称" min-width="120" />
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="config_time" label="配置时间" min-width="180">
          <template #default="scope">
            {{ formatTime(scope.row.config_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="change_description" label="变更描述" min-width="200" />
        <el-table-column prop="git_commit_id" label="Git提交ID" min-width="150">
          <template #default="scope">
            <span v-if="scope.row.git_commit_id" class="commit-id">{{ scope.row.git_commit_id.substring(0, 8) }}</span>
            <span v-else class="no-commit">无</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              @click="handleDownload(scope.row)"
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click="handleCommitToGit(scope.row)"
              :disabled="scope.row.git_commit_id"
              :loading="loading"
            >
              <el-icon><Upload /></el-icon>
              提交Git
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="showBackupDialog"
      title="备份配置设置"
      width="500px"
    >
      <el-form label-width="120px">
        <el-form-item label="设备名称">
          <el-input :value="currentDeviceName" readonly />
        </el-form-item>
        <el-form-item label="备份周期">
          <el-radio-group v-model="backupForm.scheduleType">
            <el-radio label="hourly">每小时</el-radio>
            <el-radio label="daily">每天</el-radio>
            <el-radio label="monthly">每月</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备份时间" v-if="backupForm.scheduleType === 'daily' || backupForm.scheduleType === 'monthly'">
          <el-time-picker
            v-model="backupForm.time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择时间"
            style="width: 100%"
            type="time"
          />
        </el-form-item>
        <el-form-item label="每月日期" v-if="backupForm.scheduleType === 'monthly'">
          <el-input-number
            v-model="backupForm.day"
            :min="1"
            :max="31"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="backupForm.isActive" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBackupDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveBackup" :loading="backupLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Download, Upload, Clock } from '@element-plus/icons-vue'
import { configurationApi, deviceApi } from '../api/index'

export default {
  name: 'ConfigurationManagement',
  components: {
    Document,
    Download,
    Upload,
    Clock
  },
  setup() {
    const loading = ref(false)
    const backupLoading = ref(false)
    const configList = ref([])
    const deviceList = ref([])
    const selectedDeviceId = ref('')
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalCount = ref(0)
    const showBackupDialog = ref(false)

    const backupForm = reactive({
      deviceId: null,
      scheduleType: 'daily',
      time: null,
      day: 1,
      isActive: true
    })

    const formatTime = (time) => {
      if (!time) return ''
      return new Date(time).toLocaleString()
    }

    const currentDeviceName = computed(() => {
      const device = deviceList.value.find(d => d.id === backupForm.deviceId)
      return device ? device.hostname : ''
    })

    const loadConfigs = async () => {
      loading.value = true
      try {
        const response = await configurationApi.getConfigurations()
        configList.value = response || []
        totalCount.value = configList.value.length
      } catch (error) {
        ElMessage.error('获取配置列表失败')
      } finally {
        loading.value = false
      }
    }

    const loadDevices = async () => {
      try {
        const response = await deviceApi.getDevices()
        deviceList.value = response || []
      } catch (error) {
        ElMessage.error('获取设备列表失败')
      }
    }

    const handleGetConfig = async () => {
      if (!selectedDeviceId.value) {
        ElMessage.warning('请选择设备')
        return
      }
      loading.value = true
      try {
        const response = await configurationApi.collectConfigFromDevice(selectedDeviceId.value)
        if (response.success) {
          ElMessage.success(response.message)
          loadConfigs()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        ElMessage.error('获取配置失败')
      } finally {
        loading.value = false
      }
    }

    const handleBackupNow = async () => {
      if (!selectedDeviceId.value) {
        ElMessage.warning('请选择设备')
        return
      }
      loading.value = true
      try {
        const response = await configurationApi.backupNow(selectedDeviceId.value)
        if (response.success) {
          ElMessage.success(response.message)
          loadConfigs()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        ElMessage.error('执行备份失败')
      } finally {
        loading.value = false
      }
    }

    const handleOpenBackupDialog = () => {
      if (!selectedDeviceId.value) {
        ElMessage.warning('请选择设备')
        return
      }
      backupForm.deviceId = parseInt(selectedDeviceId.value)
      showBackupDialog.value = true
    }

    const handleSaveBackup = async () => {
      backupLoading.value = true
      try {
        const response = await configurationApi.createBackupSchedule(backupForm)
        if (response.success) {
          ElMessage.success(response.message)
          showBackupDialog.value = false
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        ElMessage.error('保存备份设置失败')
      } finally {
        backupLoading.value = false
      }
    }

    const handleDownload = (config) => {
      try {
        const blob = new Blob([config.config_content], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${config.device_name}-config-${new Date(config.config_time).toISOString().slice(0, 10)}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        ElMessage.success('配置文件下载成功')
      } catch (error) {
        ElMessage.error('配置文件下载失败')
      }
    }

    const handleCommitToGit = async (config) => {
      loading.value = true
      try {
        const response = await configurationApi.commitConfigToGit(config.id)
        if (response.success) {
          ElMessage.success('配置已成功提交到Git')
          loadConfigs()
        } else {
          ElMessage.error(response.message || 'Git提交失败')
        }
      } catch (error) {
        ElMessage.error('Git提交失败')
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadConfigs()
      loadDevices()
    })

    return {
      loading,
      backupLoading,
      configList,
      deviceList,
      selectedDeviceId,
      currentPage,
      pageSize,
      totalCount,
      showBackupDialog,
      backupForm,
      currentDeviceName,
      formatTime,
      handleGetConfig,
      handleBackupNow,
      handleOpenBackupDialog,
      handleSaveBackup,
      handleDownload,
      handleCommitToGit
    }
  }
}
</script>

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

.commit-id {
  color: #1890ff;
  font-family: monospace;
}

.no-commit {
  color: #999;
  font-style: italic;
}
</style>
