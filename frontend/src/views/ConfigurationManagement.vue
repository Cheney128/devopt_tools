<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Download, Refresh } from '@element-plus/icons-vue'
import api from '../api/index'

// 响应式数据
const loading = ref(false)
const configurations = ref([])
const devices = ref([])
const selectedDeviceId = ref('')

// 方法
const fetchConfigurations = async () => {
  loading.value = true
  try {
    // 这里应该调用API获取配置列表
    // 暂时使用模拟数据
    configurations.value = [
      {
        id: 1,
        device_id: 1,
        device_name: 'SW-001',
        config_time: new Date('2026-01-15 08:00:00'),
        config_content: 'interface GigabitEthernet1/0/1\n description Server\n switchport access vlan 100\n!\ninterface GigabitEthernet1/0/2\n description Printer\n switchport access vlan 200\n!'
      },
      {
        id: 2,
        device_id: 2,
        device_name: 'SW-002',
        config_time: new Date('2026-01-14 18:00:00'),
        config_content: 'interface GigabitEthernet1/0/1\n description Uplink\n switchport mode trunk\n!'
      }
    ]
  } catch (error) {
    ElMessage.error('获取配置列表失败')
  } finally {
    loading.value = false
  }
}

const fetchDevices = async () => {
  try {
    // 这里应该调用API获取设备列表
    // 暂时使用模拟数据
    devices.value = [
      { id: 1, hostname: 'SW-001', ip_address: '192.168.1.1' },
      { id: 2, hostname: 'SW-002', ip_address: '192.168.1.2' }
    ]
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  }
}

const syncWithOxidized = async () => {
  loading.value = true
  try {
    // 调用API与Oxidized同步
    const response = await api.post('/configurations/oxidized/sync')
    if (response.success) {
      ElMessage.success(response.message)
      // 刷新配置列表
      fetchConfigurations()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('同步失败')
  } finally {
    loading.value = false
  }
}

const getDeviceConfiguration = async (deviceId) => {
  loading.value = true
  try {
    // 调用API从Oxidized获取设备配置
    const response = await api.get(`/configurations/oxidized/${deviceId}`)
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

const downloadConfiguration = (config) => {
  // 这里应该实现下载配置文件的功能
  ElMessage.success('配置文件下载成功')
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
          <div class="header-buttons">
            <el-button type="primary" @click="syncWithOxidized" :loading="loading">
              <el-icon><Refresh /></el-icon>
              与Oxidized同步
            </el-button>
          </div>
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
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_name" label="设备名称" min-width="120" />
        <el-table-column prop="config_time" label="配置时间" min-width="180">
          <template #default="scope">
            {{ scope.row.config_time.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="配置内容" min-width="300">
          <template #default="scope">
            <el-button size="small" @click="() => {}">查看</el-button>
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
</style>