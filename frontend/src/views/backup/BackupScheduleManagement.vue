<template>
  <div class="backup-schedule-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>备份计划管理</span>
          <el-button type="primary" @click="handleOpenCreateDialog">
            <el-icon><Plus /></el-icon>
            新建计划
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select
          v-model="filterDeviceId"
          placeholder="选择设备"
          clearable
          style="width: 200px"
        >
          <el-option
            v-for="device in deviceList"
            :key="device.id"
            :label="device.hostname"
            :value="device.id"
          />
        </el-select>
        <el-select
          v-model="filterStatus"
          placeholder="状态"
          clearable
          style="width: 120px"
        >
          <el-option label="启用" value="active" />
          <el-option label="禁用" value="inactive" />
        </el-select>
        <el-select
          v-model="filterType"
          placeholder="类型"
          clearable
          style="width: 120px"
        >
          <el-option label="每小时" value="hourly" />
          <el-option label="每天" value="daily" />
          <el-option label="每月" value="monthly" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <div class="batch-actions" v-if="selectedSchedules.length > 0">
        <el-button type="success" size="small" @click="handleBatchEnable">
          <el-icon><Check /></el-icon>
          批量启用
        </el-button>
        <el-button type="warning" size="small" @click="handleBatchDisable">
          <el-icon><Close /></el-icon>
          批量禁用
        </el-button>
        <el-button type="danger" size="small" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <span class="selected-count">已选择 {{ selectedSchedules.length }} 项</span>
      </div>

      <el-table
        v-loading="loading"
        :data="scheduleList"
        style="width: 100%; margin-top: 20px"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_name" label="设备名称" min-width="150" />
        <el-table-column prop="schedule_type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="getScheduleTypeType(scope.row.schedule_type)">
              {{ getScheduleTypeText(scope.row.schedule_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="schedule_time" label="时间" width="120">
          <template #default="scope">
            {{ formatScheduleTime(scope.row) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="(val) => handleStatusChange(scope.row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="last_run_time" label="上次执行" min-width="150">
          <template #default="scope">
            {{ scope.row.last_run_time ? formatTime(scope.row.last_run_time) : '从未执行' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="150">
          <template #default="scope">
            {{ formatTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="handleEdit(scope.row)"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              size="small"
              type="success"
              @click="handleBackupNow(scope.row)"
              :loading="scope.row.backupLoading"
            >
              <el-icon><VideoPlay /></el-icon>
              立即备份
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
            >
              <el-icon><Delete /></el-icon>
              删除
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
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="showDialog"
      :title="dialogMode === 'create' ? '新建备份计划' : '编辑备份计划'"
      width="600px"
    >
      <el-form :model="formData" label-width="120px" ref="formRef" :rules="formRules">
        <el-form-item label="选择设备" prop="device_id" v-if="dialogMode === 'create'">
          <el-select
            v-model="formData.device_id"
            placeholder="选择设备"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="device in deviceList"
              :key="device.id"
              :label="device.hostname"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备" v-else>
          <el-input :value="formData.device_name" readonly />
        </el-form-item>
        <el-form-item label="备份周期" prop="schedule_type">
          <el-radio-group v-model="formData.schedule_type">
            <el-radio label="hourly">每小时</el-radio>
            <el-radio label="daily">每天</el-radio>
            <el-radio label="monthly">每月</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item 
          label="备份时间" 
          v-if="formData.schedule_type === 'daily' || formData.schedule_type === 'monthly'"
          prop="schedule_time"
        >
          <el-time-picker
            v-model="formData.schedule_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item 
          label="每月日期" 
          v-if="formData.schedule_type === 'monthly'"
          prop="schedule_day"
        >
          <el-input-number
            v-model="formData.schedule_day"
            :min="1"
            :max="31"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saveLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Search, 
  Edit, 
  Delete, 
  Check, 
  Close, 
  VideoPlay 
} from '@element-plus/icons-vue'
import { configurationApi, deviceApi } from '../../api/index'

export default {
  name: 'BackupScheduleManagement',
  components: {
    Plus,
    Search,
    Edit,
    Delete,
    Check,
    Close,
    VideoPlay
  },
  setup() {
    const loading = ref(false)
    const saveLoading = ref(false)
    const scheduleList = ref([])
    const deviceList = ref([])
    const selectedSchedules = ref([])
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalCount = ref(0)
    const showDialog = ref(false)
    const dialogMode = ref('create')
    const formRef = ref(null)

    const filterDeviceId = ref('')
    const filterStatus = ref('')
    const filterType = ref('')

    const formData = reactive({
      id: null,
      device_id: null,
      device_name: '',
      schedule_type: 'daily',
      schedule_time: '02:00',
      schedule_day: 1,
      is_active: true
    })

    const formRules = {
      device_id: [
        { required: true, message: '请选择设备', trigger: 'change' }
      ],
      schedule_type: [
        { required: true, message: '请选择备份周期', trigger: 'change' }
      ],
      schedule_time: [
        { required: true, message: '请选择备份时间', trigger: 'change' }
      ],
      schedule_day: [
        { required: true, message: '请输入每月日期', trigger: 'change' }
      ]
    }

    const formatTime = (time) => {
      if (!time) return ''
      return new Date(time).toLocaleString()
    }

    const getScheduleTypeText = (type) => {
      const typeMap = {
        hourly: '每小时',
        daily: '每天',
        monthly: '每月'
      }
      return typeMap[type] || type
    }

    const getScheduleTypeType = (type) => {
      const typeMap = {
        hourly: 'info',
        daily: 'success',
        monthly: 'warning'
      }
      return typeMap[type] || 'info'
    }

    const formatScheduleTime = (row) => {
      if (row.schedule_type === 'hourly') {
        return '每小时执行'
      } else if (row.schedule_type === 'daily') {
        return row.schedule_time || '未设置'
      } else if (row.schedule_type === 'monthly') {
        return `${row.schedule_day || 1}号 ${row.schedule_time || '未设置'}`
      }
      return '-'
    }

    const loadSchedules = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value
        }
        if (filterDeviceId.value) {
          params.device_id = filterDeviceId.value
        }
        if (filterStatus.value) {
          params.is_active = filterStatus.value === 'active'
        }
        if (filterType.value) {
          params.schedule_type = filterType.value
        }

        const response = await configurationApi.getBackupSchedules(params)
        
        scheduleList.value = (response.schedules || []).map(schedule => ({
          ...schedule,
          backupLoading: false
        }))
        totalCount.value = response.total || 0
      } catch (error) {
        console.error('加载备份计划失败:', error)
        ElMessage.error('加载备份计划失败')
      } finally {
        loading.value = false
      }
    }

    const loadDevices = async () => {
      try {
        const response = await deviceApi.getAllDevices()
        deviceList.value = response.devices || []
      } catch (error) {
        console.error('加载设备列表失败:', error)
        ElMessage.error('加载设备列表失败')
      }
    }

    const handleSearch = () => {
      currentPage.value = 1
      loadSchedules()
    }

    const handleReset = () => {
      filterDeviceId.value = ''
      filterStatus.value = ''
      filterType.value = ''
      currentPage.value = 1
      loadSchedules()
    }

    const handleSelectionChange = (selection) => {
      selectedSchedules.value = selection
    }

    const handleOpenCreateDialog = () => {
      dialogMode.value = 'create'
      resetForm()
      showDialog.value = true
    }

    const handleEdit = (schedule) => {
      dialogMode.value = 'edit'
      resetForm()
      
      formData.id = schedule.id
      formData.device_id = schedule.device_id
      formData.device_name = schedule.device_name
      formData.schedule_type = schedule.schedule_type
      formData.schedule_time = schedule.schedule_time
      formData.schedule_day = schedule.schedule_day
      formData.is_active = schedule.is_active
      
      showDialog.value = true
    }

    const resetForm = () => {
      formData.id = null
      formData.device_id = null
      formData.device_name = ''
      formData.schedule_type = 'daily'
      formData.schedule_time = '02:00'
      formData.schedule_day = 1
      formData.is_active = true
    }

    const handleSave = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (!valid) return
        
        saveLoading.value = true
        try {
          const payload = {
            schedule_type: formData.schedule_type,
            is_active: formData.is_active
          }

          if (formData.schedule_type === 'daily' || formData.schedule_type === 'monthly') {
            payload.schedule_time = formData.schedule_time
          }
          if (formData.schedule_type === 'monthly') {
            payload.schedule_day = formData.schedule_day
          }

          if (dialogMode.value === 'create') {
            payload.device_id = formData.device_id
            await configurationApi.createBackupSchedule(payload)
            ElMessage.success('备份计划创建成功')
          } else {
            await configurationApi.updateBackupSchedule(formData.id, payload)
            ElMessage.success('备份计划更新成功')
          }
          
          showDialog.value = false
          loadSchedules()
        } catch (error) {
          console.error('保存备份计划失败:', error)
          ElMessage.error(dialogMode.value === 'create' ? '创建备份计划失败' : '更新备份计划失败')
        } finally {
          saveLoading.value = false
        }
      })
    }

    const handleDelete = async (schedule) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除设备 "${schedule.device_name}" 的备份计划吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await configurationApi.deleteBackupSchedule(schedule.id)
        ElMessage.success('删除成功')
        loadSchedules()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除备份计划失败:', error)
          ElMessage.error('删除失败')
        }
      }
    }

    const handleBatchDelete = async () => {
      if (selectedSchedules.value.length === 0) {
        ElMessage.warning('请选择要删除的备份计划')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要删除选中的 ${selectedSchedules.value.length} 个备份计划吗？`,
          '确认批量删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        for (const schedule of selectedSchedules.value) {
          await configurationApi.deleteBackupSchedule(schedule.id)
        }
        
        ElMessage.success('批量删除成功')
        selectedSchedules.value = []
        loadSchedules()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量删除失败:', error)
          ElMessage.error('批量删除失败')
        }
      }
    }

    const handleStatusChange = async (schedule, newStatus) => {
      try {
        await configurationApi.updateBackupSchedule(schedule.id, {
          schedule_type: schedule.schedule_type,
          is_active: newStatus
        })
        ElMessage.success(newStatus ? '已启用' : '已禁用')
      } catch (error) {
        console.error('更新状态失败:', error)
        ElMessage.error('更新状态失败')
        schedule.is_active = !newStatus
      }
    }

    const handleBatchEnable = async () => {
      if (selectedSchedules.value.length === 0) {
        ElMessage.warning('请选择要启用的备份计划')
        return
      }

      try {
        for (const schedule of selectedSchedules.value) {
          await configurationApi.updateBackupSchedule(schedule.id, {
            schedule_type: schedule.schedule_type,
            is_active: true
          })
        }
        ElMessage.success('批量启用成功')
        selectedSchedules.value = []
        loadSchedules()
      } catch (error) {
        console.error('批量启用失败:', error)
        ElMessage.error('批量启用失败')
      }
    }

    const handleBatchDisable = async () => {
      if (selectedSchedules.value.length === 0) {
        ElMessage.warning('请选择要禁用的备份计划')
        return
      }

      try {
        for (const schedule of selectedSchedules.value) {
          await configurationApi.updateBackupSchedule(schedule.id, {
            schedule_type: schedule.schedule_type,
            is_active: false
          })
        }
        ElMessage.success('批量禁用成功')
        selectedSchedules.value = []
        loadSchedules()
      } catch (error) {
        console.error('批量禁用失败:', error)
        ElMessage.error('批量禁用失败')
      }
    }

    const handleBackupNow = async (schedule) => {
      schedule.backupLoading = true
      try {
        await configurationApi.backupNow(schedule.device_id)
        ElMessage.success('立即备份任务已启动')
        setTimeout(() => {
          loadSchedules()
        }, 2000)
      } catch (error) {
        console.error('启动备份失败:', error)
        ElMessage.error('启动备份失败')
      } finally {
        schedule.backupLoading = false
      }
    }

    const handleSizeChange = (val) => {
      pageSize.value = val
      loadSchedules()
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadSchedules()
    }

    onMounted(() => {
      loadSchedules()
      loadDevices()
    })

    return {
      loading,
      saveLoading,
      scheduleList,
      deviceList,
      selectedSchedules,
      currentPage,
      pageSize,
      totalCount,
      showDialog,
      dialogMode,
      formRef,
      filterDeviceId,
      filterStatus,
      filterType,
      formData,
      formRules,
      formatTime,
      getScheduleTypeText,
      getScheduleTypeType,
      formatScheduleTime,
      handleSearch,
      handleReset,
      handleSelectionChange,
      handleOpenCreateDialog,
      handleEdit,
      handleSave,
      handleDelete,
      handleBatchDelete,
      handleStatusChange,
      handleBatchEnable,
      handleBatchDisable,
      handleBackupNow,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.backup-schedule-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.batch-actions {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.selected-count {
  color: #606266;
  font-size: 14px;
  margin-left: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
