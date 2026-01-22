<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElUpload, ElButton, ElIcon, ElDialog, ElForm, ElFormItem } from 'element-plus'
import { Plus, Delete, ArrowDown, Upload, Download } from '@element-plus/icons-vue'
import { useDeviceStore } from '../stores/deviceStore'
import { deviceApi } from '../api/index'

// 设备状态选项
const statusOptions = [
  { label: '活跃', value: 'active' },
  { label: '维护', value: 'maintenance' },
  { label: '离线', value: 'offline' },
  { label: '故障', value: 'faulty' }
]

// 厂商选项
const vendorOptions = [
  { label: '华为', value: 'Huawei' },
  { label: '思科', value: 'Cisco' },
  { label: '华三', value: 'H3C' },
  { label: '锐捷', value: 'Ruijie' },
  { label: '中兴', value: 'ZTE' }
]

// 登录方式选项
const loginMethodOptions = [
  { label: 'SSH', value: 'ssh' },
  { label: 'Telnet', value: 'telnet' },
  { label: 'Console', value: 'console' }
]
const deviceStore = useDeviceStore()
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('添加设备')
const form = ref({
  hostname: '',
  ip_address: '',
  vendor: '',
  model: '',
  os_version: '',
  location: '',
  contact: '',
  status: 'active',
  login_method: 'ssh',
  login_port: 22,
  username: '',
  password: '',
  sn: ''
})
const formRules = ref({
  hostname: [{ required: true, message: '请输入主机名', trigger: 'blur' }],
  ip_address: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  vendor: [{ required: true, message: '请选择厂商', trigger: 'change' }],
  model: [{ required: true, message: '请输入型号', trigger: 'blur' }]
})
const multipleSelection = ref([])
const currentDeviceId = ref(null)
const searchForm = ref({
  status: '',
  vendor: ''
})

// 计算属性
const isAllSelected = computed(() => {
  return multipleSelection.value.length === deviceStore.devices.length && deviceStore.devices.length > 0
})

const isIndeterminate = computed(() => {
  return multipleSelection.value.length > 0 && multipleSelection.value.length < deviceStore.devices.length
})

// 方法
const fetchDevices = async () => {
  loading.value = true
  await deviceStore.fetchDevices(searchForm.value)
  loading.value = false
}

const handleSearch = () => {
  fetchDevices()
}

const handleReset = () => {
  searchForm.value = {
    status: '',
    vendor: ''
  }
  fetchDevices()
}

const handleAddDevice = () => {
  dialogTitle.value = '添加设备'
  form.value = {
    hostname: '',
    ip_address: '',
    vendor: '',
    model: '',
    os_version: '',
    location: '',
    contact: '',
    status: 'active',
    login_method: 'ssh',
    login_port: 22,
    username: '',
    password: '',
    sn: ''
  }
  currentDeviceId.value = null
  dialogVisible.value = true
}

const handleEditDevice = (device) => {
  dialogTitle.value = '编辑设备'
  form.value = { 
    ...device,
    password: '' // 清空密码字段，只允许编辑，不显示当前密码
  }
  currentDeviceId.value = device.id
  dialogVisible.value = true
}

const handleDeleteDevice = async (device) => {
  try {
    await ElMessageBox.confirm(`确定要删除设备 ${device.hostname} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const success = await deviceStore.deleteDevice(device.id)
    if (success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请选择要删除的设备')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${multipleSelection.value.length} 个设备吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const ids = multipleSelection.value.map(device => device.id)
    const result = await deviceStore.batchDeleteDevices(ids)
    if (result.success) {
      ElMessage.success('批量删除成功')
      multipleSelection.value = []
    } else {
      ElMessage.error('批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const handleBatchUpdateStatus = async (status) => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请选择要更新的设备')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要将选中的 ${multipleSelection.value.length} 个设备状态更新为 ${statusOptions.find(opt => opt.value === status).label} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const ids = multipleSelection.value.map(device => device.id)
    const result = await deviceStore.batchUpdateStatus(ids, status)
    if (result.success) {
      ElMessage.success('批量更新成功')
      multipleSelection.value = []
    } else {
      ElMessage.error('批量更新失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量更新失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    loading.value = true
    // 处理表单数据，只在密码不为空时传递password字段
    const deviceData = { ...form.value }
    if (!deviceData.password) {
      delete deviceData.password
    }
    
    if (currentDeviceId.value) {
      // 编辑设备
      const updatedDevice = await deviceStore.updateDevice(currentDeviceId.value, deviceData)
      if (updatedDevice) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
      } else {
        ElMessage.error('更新失败')
      }
    } else {
      // 添加设备
      const newDevice = await deviceStore.createDevice(deviceData)
      if (newDevice) {
        ElMessage.success('添加成功')
        dialogVisible.value = false
      } else {
        ElMessage.error('添加失败')
      }
    }
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (val) => {
  multipleSelection.value = val
}

// 测试设备连接性
const handleTestConnectivity = async (device) => {
  try {
    loading.value = true
    const result = await deviceApi.testConnectivity(device.id)
    
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('连接测试失败：' + (error.message || '未知错误'))
  } finally {
    // 无论测试成功与否，都刷新设备列表
    await fetchDevices()
    loading.value = false
  }
}

// 批量上传相关
const uploadDialogVisible = ref(false)
const uploadLoading = ref(false)
const fileList = ref([])
const skipExisting = ref(false)

// 下载模板
const handleDownloadTemplate = async () => {
  try {
    const response = await deviceApi.downloadTemplate()
    // 直接使用 response.data，因为它已经是 Blob 对象
    const blob = response.data
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '设备模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板下载成功')
  } catch (error) {
    ElMessage.error('模板下载失败：' + (error.message || '未知错误'))
  }
}

// 处理文件上传
const handleUpload = async (file) => {
  try {
    uploadLoading.value = true
    const result = await deviceApi.batchImportDevices(file.raw, skipExisting.value)
    
    // 显示上传结果
    ElMessage.success(result.message)
    
    // 刷新设备列表
    await fetchDevices()
    
    // 关闭对话框
    uploadDialogVisible.value = false
    fileList.value = []
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.detail || error.message || '未知错误'))
  } finally {
    uploadLoading.value = false
  }
}

// 上传前的文件验证
const beforeUpload = (file) => {
  const isXLSX = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || file.name.endsWith('.xlsx')
  if (!isXLSX) {
    ElMessage.error('仅支持.xlsx格式文件')
    return false
  }
  fileList.value = [file]
  return false // 阻止默认上传，使用手动上传
}

// 生命周期钩子
onMounted(() => {
  fetchDevices()
})
</script>

<template>
  <div class="device-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>设备管理</span>
          <div class="header-buttons">
            <el-button type="primary" @click="handleAddDevice">
              <el-icon><Plus /></el-icon>
              添加设备
            </el-button>
            <el-dropdown>
              <el-button type="success">
                批量操作
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleBatchDelete">
                    <el-icon><Delete /></el-icon>
                    删除选中
                  </el-dropdown-item>
                  <el-dropdown-item divided>批量更新状态</el-dropdown-item>
                  <el-dropdown-item @click="handleBatchUpdateStatus('active')">活跃</el-dropdown-item>
                  <el-dropdown-item @click="handleBatchUpdateStatus('maintenance')">维护</el-dropdown-item>
                  <el-dropdown-item @click="handleBatchUpdateStatus('offline')">离线</el-dropdown-item>
                  <el-dropdown-item @click="handleBatchUpdateStatus('faulty')">故障</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="info" @click="uploadDialogVisible = true">
              <el-icon><Upload /></el-icon>
              批量上传设备
            </el-button>
            <el-button type="warning" @click="handleDownloadTemplate">
              <el-icon><Download /></el-icon>
              下载模板
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :inline="true" :model="searchForm" class="search-form" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态" clearable>
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="厂商">
          <el-select v-model="searchForm.vendor" placeholder="选择厂商" clearable>
            <el-option
              v-for="option in vendorOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 设备列表 -->
      <el-table
        v-loading="loading"
        :data="deviceStore.devices"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="hostname" label="主机名" min-width="120" />
        <el-table-column prop="ip_address" label="IP地址" min-width="120" />
        <el-table-column prop="vendor" label="厂商" min-width="100" />
        <el-table-column prop="model" label="型号" min-width="120" />
        <el-table-column prop="location" label="位置" min-width="120" />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="scope">
            <el-tag
              :type="
                scope.row.status === 'active' ? 'success' :
                scope.row.status === 'maintenance' ? 'warning' :
                scope.row.status === 'offline' ? 'info' : 'danger'
              "
            >
              {{ statusOptions.find(opt => opt.value === scope.row.status)?.label || scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEditDevice(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteDevice(scope.row)">删除</el-button>
            <el-button size="small" type="warning" @click="handleTestConnectivity(scope.row)">连接性测试</el-button>
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
          :total="deviceStore.deviceCount"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 设备表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="主机名" required>
          <el-input v-model="form.hostname" placeholder="请输入主机名" />
        </el-form-item>
        <el-form-item label="IP地址" required>
          <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="厂商" required>
          <el-select v-model="form.vendor" placeholder="请选择厂商">
            <el-option
              v-for="option in vendorOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="型号" required>
          <el-input v-model="form.model" placeholder="请输入型号" />
        </el-form-item>
        <el-form-item label="系统版本">
          <el-input v-model="form.os_version" placeholder="请输入系统版本" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="请输入位置" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" placeholder="请选择状态">
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="登录方式">
          <el-select v-model="form.login_method" placeholder="请选择登录方式">
            <el-option
              v-for="option in loginMethodOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="登录端口">
          <el-input-number v-model="form.login_port" :min="1" :max="65535" placeholder="请输入登录端口" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码（不修改请留空）" show-password />
        </el-form-item>
        <el-form-item label="设备序列号">
          <el-input v-model="form.sn" placeholder="请输入设备序列号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 批量上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="批量上传设备"
      width="500px"
    >
      <el-form>
        <el-form-item label="上传文件">
          <el-upload
            v-model:file-list="fileList"
            :before-upload="beforeUpload"
            :auto-upload="false"
            accept=".xlsx"
            drag
            action=""
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                仅支持.xlsx格式文件，文件大小不超过10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="上传选项">
          <el-checkbox v-model="skipExisting">跳过已存在的设备</el-checkbox>
          <div class="option-tip">
            <span class="el-form-item__help">
              勾选后，系统将跳过已存在的设备（根据IP地址判断），不勾选则更新已存在设备的信息
            </span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="fileList.length > 0 && handleUpload(fileList[0])" 
            :loading="uploadLoading"
            :disabled="fileList.length === 0"
          >
            确定上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.device-management {
  padding: 0 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>