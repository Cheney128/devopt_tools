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
          v-model="selectedDeviceIds"
          placeholder="选择设备获取配置"
          style="width: 300px"
          multiple
          filterable
          @change="handleSelectChange"
        >
          <!-- 全选选项 -->
          <el-option
            v-if="deviceList.length > 0"
            :key="'select-all'"
            :label="'全选'"
            :value="'select-all'"
          />
          <!-- 设备列表选项 -->
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
          :disabled="selectedDeviceIds.length === 0"
          :loading="loading"
        >
          <el-icon><Document /></el-icon>
          获取配置
        </el-button>
        <el-button
          type="primary"
          @click="handleBackupNow"
          :disabled="selectedDeviceIds.length === 0"
          :loading="loading"
        >
          <el-icon><Upload /></el-icon>
          备份配置
        </el-button>
        <el-button
          type="warning"
          @click="handleOpenBackupDialog"
          :disabled="selectedDeviceIds.length === 0"
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
      :title="`备份配置设置 (${selectedDeviceIds.length}台设备)`"
      width="600px"
    >
      <el-form label-width="120px">
        <el-form-item label="设备数量">
          <el-input :value="selectedDeviceIds.length" readonly />
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
      
      <!-- 备份进度显示 -->
      <div v-if="showBackupProgress" class="backup-progress">
        <el-progress
          :percentage="backupProgress"
          :status="backupProgressStatus"
          :stroke-width="20"
          text-inside
          class="progress-bar"
        />
        <div class="progress-text">
          {{ backupProgressText }}
        </div>
        
        <!-- 备份结果列表 -->
        <div v-if="backupResults.length > 0" class="backup-results">
          <el-divider content-position="left">备份结果</el-divider>
          <el-scrollbar height="200px">
            <div v-for="result in backupResults" :key="result.deviceId" class="result-item">
              <el-tag :type="result.success ? 'success' : 'danger'" size="small">
                {{ result.success ? '成功' : '失败' }}
              </el-tag>
              <span class="device-name">设备 {{ result.deviceId }}</span>
              <span class="result-message">{{ result.message }}</span>
            </div>
          </el-scrollbar>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="handleCancelBackup">取消</el-button>
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
    const selectedDeviceIds = ref([])
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalCount = ref(0)
    const showBackupDialog = ref(false)
    
    // 备份进度相关
    const showBackupProgress = ref(false)
    const backupProgress = ref(0)
    const backupProgressStatus = ref('')
    const backupProgressText = ref('')
    const backupResults = ref([])
    const cancelBackup = ref(false)

    const backupForm = reactive({
      scheduleType: 'daily',
      time: null,
      day: 1,
      isActive: true
    })

    const formatTime = (time) => {
      if (!time) return ''
      return new Date(time).toLocaleString()
    }

    // 处理选择变化
    const handleSelectChange = (values) => {
      // 检查是否选择了"全选"选项
      if (values.includes('select-all')) {
        // 选择所有设备，并移除"select-all"值
        selectedDeviceIds.value = deviceList.value.map(device => device.id)
      }
    }
    
    // 取消备份
    const handleCancelBackup = () => {
      if (backupLoading.value) {
        cancelBackup.value = true
        backupProgressText.value = '正在取消备份...'
      } else {
        showBackupDialog.value = false
        resetBackupProgress()
      }
    }
    
    // 重置备份进度
    const resetBackupProgress = () => {
      showBackupProgress.value = false
      backupProgress.value = 0
      backupProgressStatus.value = ''
      backupProgressText.value = ''
      backupResults.value = []
      cancelBackup.value = false
    }

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
        deviceList.value = response.devices || []
      } catch (error) {
        ElMessage.error('获取设备列表失败')
      }
    }

    const handleGetConfig = async () => {
      if (selectedDeviceIds.value.length === 0) {
        ElMessage.warning('请选择设备')
        return
      }
      loading.value = true
      try {
        // 逐个设备获取配置
        for (const deviceId of selectedDeviceIds.value) {
          await configurationApi.collectConfigFromDevice(deviceId)
        }
        ElMessage.success('所有设备配置获取完成')
        loadConfigs()
      } catch (error) {
        ElMessage.error('获取配置失败')
      } finally {
        loading.value = false
      }
    }

    const handleBackupNow = async () => {
      if (selectedDeviceIds.value.length === 0) {
        ElMessage.warning('请选择设备')
        return
      }
      loading.value = true
      try {
        // 逐个设备执行备份
        for (const deviceId of selectedDeviceIds.value) {
          await configurationApi.backupNow(deviceId)
        }
        ElMessage.success('所有设备备份完成')
        loadConfigs()
      } catch (error) {
        ElMessage.error('执行备份失败')
      } finally {
        loading.value = false
      }
    }

    const handleOpenBackupDialog = () => {
      if (selectedDeviceIds.value.length === 0) {
        ElMessage.warning('请选择设备')
        return
      }
      showBackupDialog.value = true
    }

    const handleSaveBackup = async () => {
      if (selectedDeviceIds.value.length === 0) {
        ElMessage.warning('请选择设备')
        return
      }
      
      // 显示备份进度
      showBackupProgress.value = true
      backupProgress.value = 0
      backupProgressStatus.value = ''
      backupProgressText.value = '正在创建备份任务...'
      backupResults.value = []
      backupLoading.value = true
      
      try {
        // 如果是单个设备，使用普通API；如果是多个设备，使用批量API
        let response
        if (selectedDeviceIds.value.length === 1) {
          // 单个设备处理
          const singleForm = {
            ...backupForm,
            deviceId: selectedDeviceIds.value[0]
          }
          response = await configurationApi.createBackupSchedule(singleForm)
          
          // 更新进度
          backupProgress.value = 50
          backupProgressText.value = '正在执行备份...'
          
          if (response.backup_result) {
            // 添加备份结果
            backupResults.value.push({
              deviceId: selectedDeviceIds.value[0],
              success: response.backup_result.success,
              message: response.backup_result.message
            })
          }
        } else {
          // 多个设备批量处理
          response = await configurationApi.batchCreateBackupSchedules(selectedDeviceIds.value, backupForm)
          
          // 更新进度
          backupProgress.value = 50
          backupProgressText.value = '正在执行批量备份...'
        }
        
        // 完成备份，更新进度
        backupProgress.value = 100
        backupProgressStatus.value = 'success'
        backupProgressText.value = '备份设置完成！'
        
        // 显示结果
        if (response.success) {
          ElMessage.success(response.message)
          // 如果是批量备份，显示详细结果
          if (selectedDeviceIds.value.length > 1) {
            // 模拟添加备份结果（实际应该从后端返回更详细的结果）
            backupResults.value.push({
              deviceId: '批量',
              success: true,
              message: `${response.backup_success_count}台设备备份成功，${response.backup_failed_count}台设备备份失败`
            })
          }
          
          // 延迟关闭对话框，让用户看到结果
          setTimeout(() => {
            showBackupDialog.value = false
            resetBackupProgress()
            // 刷新配置列表，显示最新的备份结果
            loadConfigs()
          }, 2000)
        } else {
          backupProgressStatus.value = 'exception'
          ElMessage.error(response.message)
        }
      } catch (error) {
        backupProgress.value = 100
        backupProgressStatus.value = 'exception'
        backupProgressText.value = '备份设置失败！'
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
      selectedDeviceIds,
      currentPage,
      pageSize,
      totalCount,
      showBackupDialog,
      backupForm,
      // 备份进度相关
      showBackupProgress,
      backupProgress,
      backupProgressStatus,
      backupProgressText,
      backupResults,
      formatTime,
      handleSelectChange,
      handleGetConfig,
      handleBackupNow,
      handleOpenBackupDialog,
      handleSaveBackup,
      handleCancelBackup,
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

/* 备份进度样式 */
.backup-progress {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.progress-bar {
  margin-bottom: 15px;
}

.progress-text {
  text-align: center;
  margin-bottom: 15px;
  color: #606266;
  font-size: 14px;
}

.backup-results {
  margin-top: 20px;
}

.result-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  padding: 8px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.device-name {
  margin-left: 10px;
  font-weight: 500;
  color: #303133;
}

.result-message {
  margin-left: 15px;
  flex: 1;
  color: #606266;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
