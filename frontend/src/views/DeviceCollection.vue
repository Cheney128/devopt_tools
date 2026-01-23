<template>
  <div class="device-collection">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备信息采集</span>
          <el-button type="primary" @click="showBatchCollectionDialog = true">
            批量采集
          </el-button>
        </div>
      </template>

      <!-- 设备选择区域 -->
      <div class="device-selection">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="选择设备">
            <el-select
              v-model="selectedDeviceId"
              placeholder="请选择设备"
              clearable
              style="width: 300px"
            >
              <el-option
                v-for="device in devices"
                :key="device.id"
                :label="`${device.hostname} (${device.ip_address})`"
                :value="device.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadDevices">刷新设备列表</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 采集操作区域 -->
      <div v-if="selectedDevice" class="collection-actions">
        <el-card>
          <template #header>
            <span>设备: {{ selectedDevice.hostname }} ({{ selectedDevice.ip_address }})</span>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="6">
              <el-card shadow="hover" class="action-card">
                <div class="action-content">
                  <h4>版本信息</h4>
                  <p>采集设备版本、固件信息</p>
                  <el-button 
                    type="primary" 
                    @click="collectVersion"
                    :loading="loading.version"
                    :disabled="!selectedDeviceId"
                  >
                    采集版本
                  </el-button>
                </div>
              </el-card>
            </el-col>
            
            <el-col :span="6">
              <el-card shadow="hover" class="action-card">
                <div class="action-content">
                  <h4>序列号</h4>
                  <p>采集设备硬件序列号</p>
                  <el-button 
                    type="primary" 
                    @click="collectSerial"
                    :loading="loading.serial"
                    :disabled="!selectedDeviceId"
                  >
                    采集序列号
                  </el-button>
                </div>
              </el-card>
            </el-col>
            
            <el-col :span="6">
              <el-card shadow="hover" class="action-card">
                <div class="action-content">
                  <h4>接口信息</h4>
                  <p>采集所有接口状态信息</p>
                  <el-button 
                    type="primary" 
                    @click="collectInterfaces"
                    :loading="loading.interfaces"
                    :disabled="!selectedDeviceId"
                  >
                    采集接口
                  </el-button>
                </div>
              </el-card>
            </el-col>
            
            <el-col :span="6">
              <el-card shadow="hover" class="action-card">
                <div class="action-content">
                  <h4>MAC地址表</h4>
                  <p>采集设备MAC地址表</p>
                  <el-button
                    type="primary"
                    @click="collectMacTableData"
                    :loading="loading.macTable"
                    :disabled="!selectedDeviceId"
                  >
                    采集MAC表
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
      </div>

      <!-- 采集结果展示 -->
      <div v-if="collectionResults.length > 0" class="collection-results">
        <el-card>
          <template #header>
            <span>采集结果</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(result, index) in collectionResults"
              :key="index"
              :timestamp="result.timestamp"
              :type="result.success ? 'success' : 'error'"
            >
              <el-card :class="result.success ? 'success-card' : 'error-card'">
                <div class="result-content">
                  <h4>{{ result.title }}</h4>
                  <p>{{ result.message }}</p>
                  <div v-if="result.data" class="result-data">
                    <pre>{{ JSON.stringify(result.data, null, 2) }}</pre>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>

      <!-- MAC地址表展示 -->
      <div v-if="macTableData.length > 0" class="mac-table-section">
        <el-card>
          <template #header>
            <span>MAC地址表</span>
            <el-button type="text" @click="exportMacTable">导出</el-button>
          </template>
          <el-table :data="macTableData" style="width: 100%">
            <el-table-column prop="mac_address" label="MAC地址" width="180" />
            <el-table-column prop="vlan_id" label="VLAN ID" width="100" />
            <el-table-column prop="interface" label="接口" width="150" />
            <el-table-column prop="address_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.address_type === 'static' ? 'warning' : 'info'">
                  {{ row.address_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_seen" label="最后发现时间" width="180" />
          </el-table>
        </el-card>
      </div>
    </el-card>

    <!-- 批量采集对话框 -->
    <el-dialog
      v-model="showBatchCollectionDialog"
      title="批量采集设备信息"
      width="600px"
    >
      <el-form :model="batchForm" label-width="120px">
        <el-form-item label="选择设备">
          <el-select
            v-model="batchForm.deviceIds"
            multiple
            placeholder="请选择设备"
            style="width: 100%"
          >
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="`${device.hostname} (${device.ip_address})`"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="采集类型">
          <el-checkbox-group v-model="batchForm.collectTypes">
            <el-checkbox label="version">版本信息</el-checkbox>
            <el-checkbox label="serial">序列号</el-checkbox>
            <el-checkbox label="interfaces">接口信息</el-checkbox>
            <el-checkbox label="mac_table">MAC地址表</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showBatchCollectionDialog = false">取消</el-button>
        <el-button type="primary" @click="executeBatchCollection" :loading="loading.batch">
          开始采集
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { deviceApi, deviceCollectionApi } from '@/api/index'

// 数据状态
const devices = ref([])
const selectedDeviceId = ref(null)
const loading = ref({
  version: false,
  serial: false,
  interfaces: false,
  macTable: false,
  batch: false,
  devices: false
})
const collectionResults = ref([])
const macTableData = ref([])
const showBatchCollectionDialog = ref(false)
const batchForm = ref({
  deviceIds: [],
  collectTypes: ['version', 'serial', 'interfaces', 'mac_table']
})

// 计算属性
const selectedDevice = computed(() => {
  return devices.value.find(d => d.id === selectedDeviceId.value)
})

const searchForm = ref({
  deviceId: null
})

// 方法
const loadDevices = async () => {
  try {
    loading.value.devices = true
    // 调用设备列表API获取真实设备数据
    const response = await deviceApi.getDevices()
    devices.value = response || []
  } catch (error) {
    ElMessage.error('加载设备列表失败')
    console.error('加载设备列表失败:', error)
  } finally {
    loading.value.devices = false
  }
}

// 生命周期钩子
onMounted(() => {
  // 页面加载时获取设备列表
  loadDevices()
})

const addResult = (title, success, message, data = null) => {
  collectionResults.value.unshift({
    title,
    success,
    message,
    data,
    timestamp: new Date().toLocaleString()
  })
}

const collectVersion = async () => {
  loading.value.version = true
  try {
    const result = await deviceCollectionApi.collectDeviceVersion(selectedDeviceId.value)
    if (result.success) {
      addResult('版本信息采集', true, result.message, result.data)
      ElMessage.success('版本信息采集成功')
    } else {
      addResult('版本信息采集', false, result.message)
      ElMessage.error('版本信息采集失败')
    }
  } catch (error) {
    addResult('版本信息采集', false, error.message || '采集失败')
    ElMessage.error('版本信息采集失败')
  } finally {
    loading.value.version = false
  }
}

const collectSerial = async () => {
  loading.value.serial = true
  try {
    const result = await deviceCollectionApi.collectDeviceSerial(selectedDeviceId.value)
    if (result.success) {
      addResult('序列号采集', true, result.message, result.data)
      ElMessage.success('序列号采集成功')
    } else {
      addResult('序列号采集', false, result.message)
      ElMessage.error('序列号采集失败')
    }
  } catch (error) {
    addResult('序列号采集', false, error.message || '采集失败')
    ElMessage.error('序列号采集失败')
  } finally {
    loading.value.serial = false
  }
}

const collectInterfaces = async () => {
  loading.value.interfaces = true
  try {
    const result = await deviceCollectionApi.collectInterfacesInfo(selectedDeviceId.value)
    if (result.success) {
      addResult('接口信息采集', true, result.message, result.data)
      ElMessage.success('接口信息采集成功')
    } else {
      addResult('接口信息采集', false, result.message)
      ElMessage.error('接口信息采集失败')
    }
  } catch (error) {
    addResult('接口信息采集', false, error.message || '采集失败')
    ElMessage.error('接口信息采集失败')
  } finally {
    loading.value.interfaces = false
  }
}

const collectMacTableData = async () => {
  loading.value.macTable = true
  try {
    const result = await deviceCollectionApi.collectMacTable(selectedDeviceId.value)
    if (result.success) {
      addResult('MAC地址表采集', true, result.message, result.data)
      ElMessage.success('MAC地址表采集成功')
      // 加载MAC地址表数据
      await loadMacTableData()
    } else {
      addResult('MAC地址表采集', false, result.message)
      ElMessage.error('MAC地址表采集失败')
    }
  } catch (error) {
    addResult('MAC地址表采集', false, error.message || '采集失败')
    ElMessage.error('MAC地址表采集失败')
  } finally {
    loading.value.macTable = false
  }
}

const loadMacTableData = async () => {
  try {
    const data = await deviceCollectionApi.getMacAddresses({ device_id: selectedDeviceId.value })
    macTableData.value = data
  } catch (error) {
    console.error('加载MAC地址表失败:', error)
  }
}

const executeBatchCollection = async () => {
  if (batchForm.value.deviceIds.length === 0) {
    ElMessage.warning('请选择至少一个设备')
    return
  }
  
  if (batchForm.value.collectTypes.length === 0) {
    ElMessage.warning('请选择至少一种采集类型')
    return
  }

  loading.value.batch = true
  try {
    const result = await deviceCollectionApi.batchCollectDeviceInfo({
      device_ids: batchForm.value.deviceIds,
      collect_types: batchForm.value.collectTypes
    })
    
    if (result.success) {
      addResult('批量采集', true, result.message, result.data)
      ElMessage.success('批量采集执行成功')
      showBatchCollectionDialog.value = false
    } else {
      addResult('批量采集', false, result.message)
      ElMessage.error('批量采集执行失败')
    }
  } catch (error) {
    addResult('批量采集', false, error.message || '批量采集失败')
    ElMessage.error('批量采集执行失败')
  } finally {
    loading.value.batch = false
  }
}

const exportMacTable = () => {
  // 实现MAC地址表导出功能
  const csvContent = macTableData.value.map(item => 
    `${item.mac_address},${item.vlan_id},${item.interface},${item.address_type},${item.last_seen}`
  ).join('\n')
  
  const blob = new Blob([`MAC地址,VLAN ID,接口,类型,最后发现时间\n${csvContent}`], 
    { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `mac_table_${selectedDevice.value.hostname}_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
}

// 生命周期
onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.device-collection {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-selection {
  margin-bottom: 20px;
}

.collection-actions {
  margin-bottom: 20px;
}

.action-card {
  text-align: center;
}

.action-content h4 {
  margin: 10px 0;
  color: #303133;
}

.action-content p {
  margin: 10px 0;
  color: #909399;
  font-size: 14px;
}

.collection-results {
  margin-bottom: 20px;
}

.result-content h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.result-content p {
  margin: 0 0 10px 0;
  color: #606266;
}

.result-data {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

.result-data pre {
  margin: 0;
  font-size: 12px;
  color: #606266;
}

.success-card {
  border-left: 4px solid #67c23a;
}

.error-card {
  border-left: 4px solid #f56c6c;
}

.mac-table-section {
  margin-top: 20px;
}

:deep(.el-timeline-item__wrapper) {
  padding-left: 20px;
}
</style>
