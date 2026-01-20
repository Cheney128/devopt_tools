<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('添加端口')
const form = ref({
  device_id: '',
  port_name: '',
  status: 'up',
  speed: '',
  description: '',
  vlan_id: ''
})
const ports = ref([])
const devices = ref([])

// 状态选项
const statusOptions = [
  { label: '启用', value: 'up' },
  { label: '禁用', value: 'down' }
]

// 方法
const fetchPorts = async () => {
  loading.value = true
  try {
    // 这里应该调用API获取端口列表
    // 暂时使用模拟数据
    ports.value = [
      {
        id: 1,
        device_id: 1,
        device_name: 'SW-001',
        port_name: 'GigabitEthernet1/0/1',
        status: 'up',
        speed: '1000Mbps',
        description: '连接服务器',
        vlan_id: 100
      },
      {
        id: 2,
        device_id: 1,
        device_name: 'SW-001',
        port_name: 'GigabitEthernet1/0/2',
        status: 'up',
        speed: '1000Mbps',
        description: '连接打印机',
        vlan_id: 200
      }
    ]
  } catch (error) {
    ElMessage.error('获取端口列表失败')
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

const handleAddPort = () => {
  dialogTitle.value = '添加端口'
  form.value = {
    device_id: '',
    port_name: '',
    status: 'up',
    speed: '',
    description: '',
    vlan_id: ''
  }
  dialogVisible.value = true
}

const handleEditPort = (port) => {
  dialogTitle.value = '编辑端口'
  form.value = { ...port }
  dialogVisible.value = true
}

const handleDeletePort = (port) => {
  ElMessage.success('删除端口成功')
  ports.value = ports.value.filter(p => p.id !== port.id)
}

const handleSubmit = () => {
  ElMessage.success('操作成功')
  dialogVisible.value = false
}

// 生命周期钩子
onMounted(() => {
  fetchPorts()
  fetchDevices()
})
</script>

<template>
  <div class="port-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>端口管理</span>
          <div class="header-buttons">
            <el-button type="primary" @click="handleAddPort">
              <el-icon><Plus /></el-icon>
              添加端口
            </el-button>
          </div>
        </div>
      </template>

      <!-- 端口列表 -->
      <el-table
        v-loading="loading"
        :data="ports"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_name" label="设备名称" min-width="120" />
        <el-table-column prop="port_name" label="端口名称" min-width="150" />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'up' ? 'success' : 'danger'">
              {{ statusOptions.find(opt => opt.value === scope.row.status)?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="speed" label="速率" min-width="100" />
        <el-table-column prop="description" label="描述" min-width="150" />
        <el-table-column prop="vlan_id" label="VLAN ID" min-width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEditPort(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeletePort(scope.row)">删除</el-button>
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
          :total="ports.length"
        />
      </div>
    </el-card>

    <!-- 端口表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="设备" required>
          <el-select v-model="form.device_id" placeholder="请选择设备">
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="device.hostname"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="端口名称" required>
          <el-input v-model="form.port_name" placeholder="请输入端口名称" />
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
        <el-form-item label="速率">
          <el-input v-model="form.speed" placeholder="请输入速率" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="请输入描述" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="VLAN ID">
          <el-input v-model="form.vlan_id" placeholder="请输入VLAN ID" type="number" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.port-management {
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

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>