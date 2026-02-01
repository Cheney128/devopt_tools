<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElUpload, ElButton, ElIcon, ElDialog, ElForm, ElFormItem, ElInput, ElTable, ElTableColumn, ElSelect, ElOption, ElCollapse, ElCollapseItem, ElTag, ElDropdown, ElDropdownMenu, ElDropdownItem, ElScrollbar } from 'element-plus'
import { Plus, Delete, ArrowDown, Upload, Download, Search } from '@element-plus/icons-vue'
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
  await deviceStore.fetchDevices()
  loading.value = false
}

const handleSearch = () => {
  fetchDevices()
}

const handleReset = () => {
  deviceStore.resetSearchForm()
  fetchDevices()
}

const handleSizeChange = (newSize) => {
  deviceStore.setPageSize(newSize)
  fetchDevices()
}

const handleCurrentChange = (newPage) => {
  deviceStore.setCurrentPage(newPage)
  fetchDevices()
}

// 监听搜索表单变化，自动更新设备列表
const updateSearchForm = (field, value) => {
  deviceStore.updateSearchForm({ [field]: value })
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

// 命令执行相关
const commandDialogVisible = ref(false)
const commandDialogTitle = ref('执行命令')
const command = ref('')
const commandLoading = ref(false)
const currentCommandDeviceId = ref(null)
const selectedDevicesForCommand = ref([])
const commandResultVisible = ref(false)
const commandResult = ref('')
const batchCommandResultVisible = ref(false)
const batchCommandResults = ref([])

// 命令模板相关
const commandTemplates = ref([])
const selectedTemplate = ref(null)
const templateVariables = ref({})
const showVariables = ref(false)
const activeCollapseNames = ref(['variables'])

// 命令历史相关
const commandHistory = ref([])
const maxHistoryItems = 20
const showCommandHistory = ref(false)
const historyIndex = ref(-1)
const tempCommand = ref('')

// 标签页相关
const activeTab = ref('execute')

// 模板管理相关
const templateSearchKeyword = ref('')
const templateLoading = ref(false)
const templateFormVisible = ref(false)
const templateFormTitle = ref('新建模板')
const templateForm = ref({
  name: '',
  command: '',
  vendor: '',
  description: '',
  variables: {},
  variablesStr: ''
})
const templateFormRef = ref(null)
const templateFormLoading = ref(false)
const templateFormRules = ref({
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  command: [{ required: true, message: '请输入命令内容', trigger: 'blur' }]
})

// 计算属性：过滤后的模板列表
const filteredTemplates = computed(() => {
  if (!templateSearchKeyword.value) {
    return commandTemplates.value
  }
  const keyword = templateSearchKeyword.value.toLowerCase()
  return commandTemplates.value.filter(template => {
    return template.name.toLowerCase().includes(keyword) ||
           template.command.toLowerCase().includes(keyword) ||
           (template.description && template.description.toLowerCase().includes(keyword)) ||
           (template.vendor && template.vendor.toLowerCase().includes(keyword))
  })
})

// 标签页切换处理
const handleTabChange = (tab) => {
  // 如果切换到模板管理标签页，重新加载模板列表
  if (tab === 'templates') {
    loadCommandTemplates()
  }
}

// 模板搜索处理
const handleTemplateSearch = () => {
  // 搜索逻辑通过计算属性自动处理
}

// 创建模板处理
const handleCreateTemplate = () => {
  templateFormTitle.value = '新建模板'
  templateForm.value = {
    name: '',
    command: '',
    vendor: '',
    description: '',
    variables: {},
    variablesStr: ''
  }
  templateFormVisible.value = true
}

// 编辑模板处理
const handleEditTemplate = (template) => {
  templateFormTitle.value = '编辑模板'
  templateForm.value = {
    name: template.name,
    command: template.command,
    vendor: template.vendor,
    description: template.description,
    variables: template.variables || {},
    variablesStr: JSON.stringify(template.variables || {}, null, 2)
  }
  templateFormVisible.value = true
}

// 删除模板处理
const handleDeleteTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(`确定要删除模板 ${template.name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deviceApi.deleteCommandTemplate(template.id)
    ElMessage.success('删除成功')
    
    // 重新加载模板列表
    await loadCommandTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('删除模板失败:', error)
    }
  }
}

// 提交模板表单
const handleSubmitTemplateForm = async () => {
  if (!templateFormRef.value) return
  
  try {
    templateFormLoading.value = true // 添加加载状态
    await templateFormRef.value.validate()
    
    // 验证变量定义JSON格式
    let variables = {}
    if (templateForm.value.variablesStr) {
      try {
        variables = JSON.parse(templateForm.value.variablesStr)
      } catch (e) {
        ElMessage.error('变量定义格式错误，请输入有效的JSON格式')
        return
      }
    }
    
    const templateData = {
      name: templateForm.value.name,
      command: templateForm.value.command,
      vendor: templateForm.value.vendor,
      description: templateForm.value.description,
      variables: variables
    }
    
    // 提交API请求
    if (templateForm.value.id) {
      // 更新模板
      await deviceApi.updateCommandTemplate(templateForm.value.id, templateData)
      ElMessage.success('更新成功')
    } else {
      // 创建模板
      await deviceApi.createCommandTemplate(templateData)
      ElMessage.success('创建成功')
    }
    
    // 关闭对话框并重新加载模板列表
    templateFormVisible.value = false
    await loadCommandTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交模板表单失败:', error)
      // 添加用户友好的错误提示
      let errorMsg = '操作失败，请稍后重试'
      if (error.response && error.response.data) {
        // API返回了错误信息
        const data = error.response.data
        errorMsg = data.message || data.detail || errorMsg
      } else if (error.message) {
        // 其他类型的错误
        errorMsg = error.message
      }
      ElMessage.error(errorMsg)
    }
  } finally {
    templateFormLoading.value = false // 无论成功失败都关闭加载状态
  }
}

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

// 加载命令模板
const loadCommandTemplates = async () => {
  try {
    const result = await deviceApi.getCommandTemplates()
    if (result.data && result.data.items) {
      commandTemplates.value = result.data.items
    }
  } catch (error) {
    console.error('加载命令模板失败:', error)
    ElMessage.error('加载命令模板失败')
  }
}

// 处理单个设备命令执行
const handleExecuteCommand = async (device) => {
  commandDialogTitle.value = `执行命令 - ${device.hostname}`
  currentCommandDeviceId.value = device.id
  selectedDevicesForCommand.value = []
  command.value = ''
  selectedTemplate.value = null
  templateVariables.value = {}
  showVariables.value = false
  commandResult.value = ''
  
  // 加载命令模板
  await loadCommandTemplates()
  
  commandDialogVisible.value = true
}

// 处理批量命令执行
const handleBatchExecuteCommand = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请选择要执行命令的设备')
    return
  }
  commandDialogTitle.value = `批量执行命令 - ${multipleSelection.value.length} 台设备`
  currentCommandDeviceId.value = null
  selectedDevicesForCommand.value = multipleSelection.value.map(device => device.id)
  command.value = ''
  selectedTemplate.value = null
  templateVariables.value = {}
  showVariables.value = false
  commandResult.value = ''
  batchCommandResults.value = []
  
  // 加载命令模板
  await loadCommandTemplates()
  
  commandDialogVisible.value = true
}

// 处理模板选择变化
const handleTemplateChange = (template) => {
  selectedTemplate.value = template
  if (template) {
    command.value = template.command
    // 初始化模板变量
    templateVariables.value = {}
    if (template.variables) {
      for (const [varName, varInfo] of Object.entries(template.variables)) {
        templateVariables.value[varName] = varInfo.default || ''
      }
      showVariables.value = Object.keys(template.variables).length > 0
    } else {
      showVariables.value = false
    }
  } else {
    command.value = ''
    templateVariables.value = {}
    showVariables.value = false
  }
}

// 重置模板选择
const resetTemplateSelection = () => {
  selectedTemplate.value = null
  command.value = ''
  templateVariables.value = {}
  showVariables.value = false
}

// 添加命令到历史记录
const addCommandToHistory = (cmd) => {
  if (!cmd.trim()) return
  
  // 移除重复的命令
  const existingIndex = commandHistory.value.indexOf(cmd)
  if (existingIndex > -1) {
    commandHistory.value.splice(existingIndex, 1)
  }
  
  // 添加到历史记录开头
  commandHistory.value.unshift(cmd)
  
  // 限制历史记录数量
  if (commandHistory.value.length > maxHistoryItems) {
    commandHistory.value.pop()
  }
  
  // 保存到本地存储
  localStorage.setItem('commandHistory', JSON.stringify(commandHistory.value))
}

// 从本地存储加载命令历史
const loadCommandHistory = () => {
  const savedHistory = localStorage.getItem('commandHistory')
  if (savedHistory) {
    commandHistory.value = JSON.parse(savedHistory)
  }
}

// 处理命令输入框的键盘事件
const handleCommandKeyDown = (event) => {
  if (event.key === 'ArrowUp') {
    event.preventDefault()
    if (commandHistory.value.length > 0) {
      if (historyIndex.value === -1) {
        tempCommand.value = command.value
        historyIndex.value = 0
      } else if (historyIndex.value < commandHistory.value.length - 1) {
        historyIndex.value++
      }
      command.value = commandHistory.value[historyIndex.value]
    }
  } else if (event.key === 'ArrowDown') {
    event.preventDefault()
    if (historyIndex.value > 0) {
      historyIndex.value--
      command.value = commandHistory.value[historyIndex.value]
    } else if (historyIndex.value === 0) {
      historyIndex.value = -1
      command.value = tempCommand.value
    }
  } else if (event.key === 'Enter') {
    historyIndex.value = -1
  }
}

// 执行命令
const executeCommand = async () => {
  if (!command.value.trim()) {
    ElMessage.warning('请输入要执行的命令')
    return
  }
  
  commandLoading.value = true
  try {
    // 准备命令执行参数
    const commandParams = {
      command: command.value,
      variables: templateVariables.value,
      template_id: selectedTemplate.value?.id || null
    }
    
    if (currentCommandDeviceId.value) {
      // 单个设备命令执行
      const result = await deviceApi.executeCommand(currentCommandDeviceId.value, commandParams.command, commandParams.variables, commandParams.template_id)
      
      if (result.success) {
        // 添加命令到历史记录
        addCommandToHistory(command.value)
        
        commandResult.value = result.output
        commandResultVisible.value = true
        commandDialogVisible.value = false
      } else {
        ElMessage.error(result.message || '命令执行失败')
      }
    } else {
      // 批量设备命令执行
      const result = await deviceApi.batchExecuteCommand(selectedDevicesForCommand.value, commandParams.command, commandParams.variables, commandParams.template_id)
      
      // 添加命令到历史记录
      addCommandToHistory(command.value)
      
      batchCommandResults.value = result.results
      batchCommandResultVisible.value = true
      commandDialogVisible.value = false
      
      ElMessage.success(`${result.success_count} 台设备命令执行成功，${result.failed_count} 台设备命令执行失败`)
    }
  } catch (error) {
    ElMessage.error('命令执行失败：' + (error.message || '未知错误'))
  } finally {
    commandLoading.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  fetchDevices()
  loadCommandHistory()
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
                  <el-dropdown-item @click="handleBatchExecuteCommand" divided>
                    <el-icon><Plus /></el-icon>
                    批量执行命令
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
      <el-form :inline="true" :model="deviceStore.searchForm" class="search-form" @submit.prevent>
        <el-form-item label="状态">
          <el-select 
            v-model="deviceStore.searchForm.status" 
            placeholder="选择状态" 
            clearable
            @change="updateSearchForm('status', deviceStore.searchForm.status)"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="厂商">
          <el-select 
            v-model="deviceStore.searchForm.vendor" 
            placeholder="选择厂商" 
            clearable
            @change="updateSearchForm('vendor', deviceStore.searchForm.vendor)"
          >
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
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEditDevice(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteDevice(scope.row)">删除</el-button>
            <el-button size="small" type="warning" @click="handleTestConnectivity(scope.row)">连接性测试</el-button>
            <el-button size="small" type="primary" @click="handleExecuteCommand(scope.row)">命令执行</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="deviceStore.currentPage"
          v-model:page-size="deviceStore.pageSize"
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

    <!-- 命令执行对话框 -->
    <el-dialog
      v-model="commandDialogVisible"
      :title="commandDialogTitle"
      width="800px"
    >
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 执行命令标签页 -->
        <el-tab-pane label="执行命令" name="execute">
          <el-form>
            <!-- 命令模板选择 -->
            <el-form-item label="命令模板">
              <div class="template-select-container">
                <el-select
                  v-model="selectedTemplate"
                  placeholder="选择命令模板（可选）"
                  filterable
                  :clearable="true"
                  @change="handleTemplateChange"
                  style="width: 100%"
                >
                  <el-option
                    v-for="template in commandTemplates"
                    :key="template.id"
                    :label="template.name"
                    :value="template"
                  >
                    <div class="template-option">
                      <div class="template-name">{{ template.name }}</div>
                      <div class="template-desc">{{ template.description || '无描述' }}</div>
                      <div class="template-vendor" v-if="template.vendor">
                        <el-tag size="small">{{ template.vendor }}</el-tag>
                      </div>
                    </div>
                  </el-option>
                </el-select>
                <el-button type="text" @click="resetTemplateSelection" size="small">
                  清除选择
                </el-button>
              </div>
            </el-form-item>

            <!-- 模板变量输入区域 -->
            <el-form-item label="模板变量" v-if="showVariables">
              <el-collapse v-model="activeCollapseNames">
                <el-collapse-item title="配置模板变量" name="variables">
                  <el-form :model="templateVariables" label-width="120px">
                    <el-form-item
                      v-for="(value, key) in selectedTemplate.variables"
                      :key="key"
                      :label="key"
                    >
                      <el-input
                        v-model="templateVariables[key]"
                        :placeholder="value.description || `请输入${key}`"
                        :type="value.type === 'password' ? 'password' : 'text'"
                        show-password
                      />
                    </el-form-item>
                  </el-form>
                </el-collapse-item>
              </el-collapse>
            </el-form-item>

            <!-- 命令输入区域 -->
            <el-form-item label="命令">
              <div class="command-input-container">
                <el-input
                  v-model="command"
                  type="textarea"
                  :rows="10"
                  placeholder="请输入要执行的命令（支持上下箭头浏览历史命令）"
                  @keydown="handleCommandKeyDown"
                  class="command-textarea"
                />
                <!-- 命令历史下拉列表 -->
                <el-dropdown
                  v-if="commandHistory.length > 0"
                  placement="bottom-start"
                  @visible-change="showCommandHistory = $event"
                >
                  <el-button type="text" class="history-button">
                    历史命令 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        v-for="(cmd, index) in commandHistory"
                        :key="index"
                        @click="command = cmd"
                        class="history-item"
                      >
                        <pre>{{ cmd }}</pre>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 模板管理标签页 -->
        <el-tab-pane label="模板管理" name="templates">
          <!-- 模板管理功能 -->
          <div class="template-management">
            <div class="template-header">
              <el-input
                v-model="templateSearchKeyword"
                placeholder="搜索模板"
                clearable
                style="width: 200px; margin-right: 10px"
                @input="handleTemplateSearch"
              >
                <template #append>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button type="primary" @click="handleCreateTemplate">
                <el-icon><Plus /></el-icon>
                新建模板
              </el-button>
            </div>
            
            <!-- 模板列表 -->
            <el-table
              :data="filteredTemplates"
              style="width: 100%"
              border
              v-loading="templateLoading"
            >
              <el-table-column prop="name" label="模板名称" min-width="150" />
              <el-table-column prop="command" label="命令内容" min-width="200" show-overflow-tooltip />
              <el-table-column prop="vendor" label="厂商" width="100" />
              <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
              <el-table-column prop="created_at" label="创建时间" width="180" />
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="handleEditTemplate(scope.row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="handleDeleteTemplate(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <!-- 模板编辑对话框 -->
            <el-dialog
              v-model="templateFormVisible"
              :title="templateFormTitle"
              width="600px"
            >
              <el-form :model="templateForm" :rules="templateFormRules" ref="templateFormRef" label-width="120px">
                <el-form-item label="模板名称" prop="name">
                  <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
                </el-form-item>
                <el-form-item label="命令内容" prop="command">
                  <el-input
                    v-model="templateForm.command"
                    type="textarea"
                    :rows="5"
                    placeholder="请输入命令内容，支持变量定义如{{variable}}"
                  />
                </el-form-item>
                <el-form-item label="厂商">
                  <el-select v-model="templateForm.vendor" placeholder="选择厂商" clearable>
                    <el-option
                      v-for="option in vendorOptions"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="描述">
                  <el-input
                    v-model="templateForm.description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入模板描述"
                  />
                </el-form-item>
                <el-form-item label="变量定义">
                  <el-input
                    v-model="templateForm.variablesStr"
                    type="textarea"
                    :rows="4"
                    placeholder='请输入变量定义，JSON格式如：{"variable": {"type": "string", "description": "描述"}}'
                  />
                  <div class="el-form-item__help">变量定义为JSON格式，支持type（string/password）和description字段</div>
                </el-form-item>
              </el-form>
              <template #footer>
                <span class="dialog-footer">
                  <el-button @click="templateFormVisible = false">取消</el-button>
                  <el-button type="primary" @click="handleSubmitTemplateForm" :loading="templateFormLoading">确定</el-button>
                </span>
              </template>
            </el-dialog>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <!-- 只在执行命令标签页显示执行按钮 -->
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="commandDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="executeCommand" 
            :loading="commandLoading"
            v-if="activeTab === 'execute'"
          >
            执行命令
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 命令执行结果对话框 -->
    <el-dialog
      v-model="commandResultVisible"
      title="命令执行结果"
      width="900px"
    >
      <el-scrollbar height="600px">
        <pre class="command-result" v-highlight><code>{{ commandResult }}</code></pre>
      </el-scrollbar>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="commandResultVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 批量命令执行结果对话框 -->
    <el-dialog
      v-model="batchCommandResultVisible"
      title="批量命令执行结果"
      width="900px"
    >
      <el-table
        :data="batchCommandResults"
        style="width: 100%"
        border
      >
        <el-table-column prop="hostname" label="设备名称" width="200" />
        <el-table-column prop="success" label="执行结果" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.success ? 'success' : 'danger'">
              {{ scope.row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" width="200" />
        <el-table-column prop="output" label="输出结果" min-width="400">
          <template #default="scope">
            <div v-if="scope.row.output" class="output-preview" @click="scope.row.showFullOutput = !scope.row.showFullOutput">
              <el-scrollbar :height="scope.row.showFullOutput ? '400px' : '100px'">
                <pre v-highlight><code>{{ scope.row.output }}</code></pre>
              </el-scrollbar>
              <div class="show-more">{{ scope.row.showFullOutput ? '收起' : '展开' }}</div>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchCommandResultVisible = false">关闭</el-button>
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

/* 命令执行结果样式 */
.command-result {
  white-space: pre-wrap;
  font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  margin: 0;
}

/* 批量命令执行结果样式 */
.output-preview {
  cursor: pointer;
}

.output-preview pre {
  margin: 0;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
  font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.4;
  white-space: pre-wrap;
}

.show-more {
  text-align: center;
  color: #409eff;
  font-size: 12px;
  margin-top: 5px;
  cursor: pointer;
}

.show-more:hover {
  text-decoration: underline;
}

/* 命令模板选择样式 */
.template-select-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.template-option {
  padding: 5px 0;
}

.template-name {
  font-weight: bold;
  margin-bottom: 3px;
}

.template-desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 3px;
}

.template-vendor {
  margin-top: 5px;
}

.template-vendor .el-tag {
  margin-right: 5px;
}

/* 命令输入容器样式 */
.command-input-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 折叠面板样式 */
.el-collapse-item__header {
  font-weight: bold;
}

.el-collapse-item__content {
  padding: 15px;
}

/* 历史命令样式 */
.history-item pre {
  white-space: pre-wrap;
  font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
  font-size: 13px;
  margin: 0;
  padding: 5px;
  background-color: #f5f5f5;
  border-radius: 3px;
}

/* 模板管理样式 */
.template-management {
  padding: 10px 0;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.template-table {
  margin-top: 15px;
}

.el-form-item__help {
  margin-top: 5px;
  color: #909399;
  font-size: 12px;
}
</style>