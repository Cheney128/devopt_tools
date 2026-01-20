<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { PlayCircle, DataAnalysis } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const inspecting = ref(false)
const inspections = ref([])
const devices = ref([])
const selectedDevices = ref([])

// 方法
const fetchInspections = async () => {
  loading.value = true
  try {
    // 这里应该调用API获取巡检结果列表
    // 暂时使用模拟数据
    inspections.value = [
      {
        id: 1,
        device_id: 1,
        device_name: 'SW-001',
        inspection_time: new Date('2026-01-15 10:00:00'),
        cpu_usage: 25.5,
        memory_usage: 45.2,
        status: 'completed',
        interface_status: {
          'GigabitEthernet1/0/1': 'up',
          'GigabitEthernet1/0/2': 'up',
          'GigabitEthernet1/0/3': 'down'
        }
      },
      {
        id: 2,
        device_id: 2,
        device_name: 'SW-002',
        inspection_time: new Date('2026-01-15 09:30:00'),
        cpu_usage: 18.3,
        memory_usage: 35.7,
        status: 'completed',
        interface_status: {
          'GigabitEthernet1/0/1': 'up',
          'GigabitEthernet1/0/2': 'up'
        }
      }
    ]
  } catch (error) {
    ElMessage.error('获取巡检结果失败')
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
      { id: 2, hostname: 'SW-002', ip_address: '192.168.1.2' },
      { id: 3, hostname: 'SW-003', ip_address: '192.168.1.3' }
    ]
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  }
}

const runInspection = async (deviceId) => {
  inspecting.value = true
  try {
    // 这里应该调用API执行巡检
    // 暂时模拟巡检过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('巡检完成')
    // 刷新巡检列表
    fetchInspections()
  } catch (error) {
    ElMessage.error('巡检失败')
  } finally {
    inspecting.value = false
  }
}

const runBatchInspection = async () => {
  if (selectedDevices.value.length === 0) {
    ElMessage.warning('请选择要巡检的设备')
    return
  }
  inspecting.value = true
  try {
    // 这里应该调用API执行批量巡检
    // 暂时模拟巡检过程
    await new Promise(resolve => setTimeout(resolve, 3000))
    ElMessage.success(`批量巡检完成，共巡检 ${selectedDevices.value.length} 台设备`)
    // 刷新巡检列表
    fetchInspections()
    selectedDevices.value = []
  } catch (error) {
    ElMessage.error('批量巡检失败')
  } finally {
    inspecting.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  fetchInspections()
  fetchDevices()
})
</script>

<template>
  <div class="inspection-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>巡检管理</span>
          <div class="header-buttons">
            <el-button type="primary" @click="runBatchInspection" :loading="inspecting">
              <el-icon><PlayCircle /></el-icon>
              批量巡检
            </el-button>
          </div>
        </div>
      </template>

      <!-- 设备选择 -->
      <el-select
        v-model="selectedDevices"
        multiple
        placeholder="选择要巡检的设备"
        style="width: 100%; margin-bottom: 20px"
      >
        <el-option
          v-for="device in devices"
          :key="device.id"
          :label="device.hostname"
          :value="device.id"
        />
      </el-select>

      <!-- 巡检结果列表 -->
      <el-table
        v-loading="loading"
        :data="inspections"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_name" label="设备名称" min-width="120" />
        <el-table-column prop="inspection_time" label="巡检时间" min-width="180">
          <template #default="scope">
            {{ scope.row.inspection_time.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="cpu_usage" label="CPU使用率" min-width="100">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.cpu_usage"
              :stroke-width="10"
              :color="
                scope.row.cpu_usage < 50 ? '#67c23a' :
                scope.row.cpu_usage < 80 ? '#e6a23c' : '#f56c6c'
              "
            />
            <span class="progress-text">{{ scope.row.cpu_usage }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="memory_usage" label="内存使用率" min-width="100">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.memory_usage"
              :stroke-width="10"
              :color="
                scope.row.memory_usage < 50 ? '#67c23a' :
                scope.row.memory_usage < 80 ? '#e6a23c' : '#f56c6c'
              "
            />
            <span class="progress-text">{{ scope.row.memory_usage }}%</span>
          </template>
        </el-table-column>
        <el-table-column label="端口状态" min-width="120">
          <template #default="scope">
            <el-button size="small" @click="() => {}">查看</el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="runInspection(scope.row.device_id)"
              :loading="inspecting"
            >
              <el-icon><PlayCircle /></el-icon>
              巡检
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
          :total="inspections.length"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.inspection-management {
  padding: 0 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.progress-text {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: #606266;
}

.el-table .cell {
  position: relative;
}
</style>