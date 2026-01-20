<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('添加VLAN')
const form = ref({
  device_id: '',
  vlan_name: '',
  vlan_description: ''
})
const vlans = ref([])
const devices = ref([])

// 方法
const fetchVlans = async () => {
  loading.value = true
  try {
    // 这里应该调用API获取VLAN列表
    // 暂时使用模拟数据
    vlans.value = [
      {
        id: 1,
        device_id: 1,
        device_name: 'SW-001',
        vlan_name: 'VLAN100',
        vlan_description: '业务VLAN'
      },
      {
        id: 2,
        device_id: 1,
        device_name: 'SW-001',
        vlan_name: 'VLAN200',
        vlan_description: '管理VLAN'
      }
    ]
  } catch (error) {
    ElMessage.error('获取VLAN列表失败')
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

const handleAddVLAN = () => {
  dialogTitle.value = '添加VLAN'
  form.value = {
    device_id: '',
    vlan_name: '',
    vlan_description: ''
  }
  dialogVisible.value = true
}

const handleEditVLAN = (vlan) => {
  dialogTitle.value = '编辑VLAN'
  form.value = { ...vlan }
  dialogVisible.value = true
}

const handleDeleteVLAN = (vlan) => {
  ElMessage.success('删除VLAN成功')
  vlans.value = vlans.value.filter(v => v.id !== vlan.id)
}

const handleSubmit = () => {
  ElMessage.success('操作成功')
  dialogVisible.value = false
}

// 生命周期钩子
onMounted(() => {
  fetchVlans()
  fetchDevices()
})
</script>

<template>
  <div class="vlan-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>VLAN管理</span>
          <div class="header-buttons">
            <el-button type="primary" @click="handleAddVLAN">
              <el-icon><Plus /></el-icon>
              添加VLAN
            </el-button>
          </div>
        </div>
      </template>

      <!-- VLAN列表 -->
      <el-table
        v-loading="loading"
        :data="vlans"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_name" label="设备名称" min-width="120" />
        <el-table-column prop="vlan_name" label="VLAN名称" min-width="120" />
        <el-table-column prop="vlan_description" label="VLAN描述" min-width="200" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEditVLAN(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteVLAN(scope.row)">删除</el-button>
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
          :total="vlans.length"
        />
      </div>
    </el-card>

    <!-- VLAN表单对话框 -->
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
        <el-form-item label="VLAN名称" required>
          <el-input v-model="form.vlan_name" placeholder="请输入VLAN名称" />
        </el-form-item>
        <el-form-item label="VLAN描述">
          <el-input v-model="form.vlan_description" placeholder="请输入VLAN描述" type="textarea" :rows="2" />
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
.vlan-management {
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