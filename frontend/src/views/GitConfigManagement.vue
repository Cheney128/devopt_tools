<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElSwitch, ElButton, ElTable, ElTableColumn, ElSpace } from 'element-plus'
import { Plus, Edit, Delete, Check, Close, Refresh } from '@element-plus/icons-vue'
import { gitConfigApi } from '../api/index'

// 响应式数据
const loading = ref(false)
const gitConfigs = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const currentConfig = ref(null)
const activeConfig = ref(null)
const formRef = ref(null)

// 表单数据
const form = reactive({
  repo_url: '',
  username: '',
  password: '',
  branch: 'main',
  ssh_key_path: '',
  is_active: true
})

// 表单验证规则
const rules = {
  repo_url: [
    { required: true, message: '请输入Git仓库URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  branch: [
    { required: true, message: '请输入Git分支名', trigger: 'blur' }
  ]
}

// 方法
const fetchGitConfigs = async () => {
  loading.value = true
  try {
    const response = await gitConfigApi.getGitConfigs()
    gitConfigs.value = response || []
    // 找到活跃的配置
    activeConfig.value = gitConfigs.value.find(config => config.is_active)
  } catch (error) {
    ElMessage.error('获取Git配置列表失败')
  } finally {
    loading.value = false
  }
}

const openForm = (config = null) => {
  // 重置表单
  Object.assign(form, {
    repo_url: '',
    username: '',
    password: '',
    branch: 'main',
    ssh_key_path: '',
    is_active: true
  })
  
  // 检查config是否为有效的Git配置对象（具有id属性）
  const isEditMode = config && typeof config === 'object' && config.id !== undefined && config.id !== null
  
  if (isEditMode) {
    // 编辑模式
    isEdit.value = true
    currentConfig.value = config
    Object.assign(form, {
      repo_url: config.repo_url,
      username: config.username || '',
      password: '', // 不显示密码
      branch: config.branch,
      ssh_key_path: config.ssh_key_path || '',
      is_active: config.is_active
    })
  } else {
    // 新增模式
    isEdit.value = false
    currentConfig.value = null
  }
  
  showForm.value = true
}

const closeForm = () => {
  showForm.value = false
  isEdit.value = false
  currentConfig.value = null
}

const saveGitConfig = async () => {
  // 表单验证
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch (error) {
    ElMessage.error('表单验证失败，请检查输入内容')
    return
  }
  
  loading.value = true
  try {
    if (isEdit.value) {
      // 更新配置
      if (!currentConfig.value || !currentConfig.value.id) {
        throw new Error('当前编辑的配置ID无效')
      }
      await gitConfigApi.updateGitConfig(currentConfig.value.id, form)
      ElMessage.success('Git配置更新成功')
    } else {
      // 新增配置
      await gitConfigApi.createGitConfig(form)
      ElMessage.success('Git配置创建成功')
    }
    closeForm()
    fetchGitConfigs()
  } catch (error) {
    console.error('Save Git Config Error:', error)
    ElMessage.error(isEdit.value ? 'Git配置更新失败' : 'Git配置创建失败')
  } finally {
    loading.value = false
  }
}

const deleteGitConfig = async (config) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除Git配置"${config.repo_url}"吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    await gitConfigApi.deleteGitConfig(config.id)
    ElMessage.success('Git配置删除成功')
    fetchGitConfigs()
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    ElMessage.error('Git配置删除失败')
  } finally {
    loading.value = false
  }
}

const testGitConnection = async (config) => {
  loading.value = true
  try {
    const response = await gitConfigApi.testGitConnection(config.id)
    if (response && response.success) {
      ElMessage.success('Git连接测试成功')
    } else {
      ElMessage.error(`Git连接测试失败: ${response?.message || '未知错误'}`)
    }
  } catch (error) {
    ElMessage.error('Git连接测试失败')
  } finally {
    loading.value = false
  }
}

const setActiveConfig = async (config) => {
  if (config.is_active) {
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要将"${config.repo_url}"设为活跃的Git配置吗？这将使当前活跃的配置变为非活跃。`,
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    loading.value = true
    await gitConfigApi.setActiveGitConfig(config.id)
    ElMessage.success('Git配置已设为活跃')
    fetchGitConfigs()
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    ElMessage.error('设置活跃配置失败')
  } finally {
    loading.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  fetchGitConfigs()
})
</script>

<template>
  <div class="git-config-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>Git配置管理</span>
          <div class="header-buttons">
            <el-button type="primary" @click="openForm(null)" :loading="loading">
              <el-icon><Plus /></el-icon>
              新增Git配置
            </el-button>
          </div>
        </div>
      </template>

      <!-- Git配置列表 -->
      <el-table
        v-loading="loading"
        :data="gitConfigs"
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="repo_url" label="仓库URL" min-width="300" />
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column prop="branch" label="分支" width="120" />
        <el-table-column prop="ssh_key_path" label="SSH密钥路径" min-width="200">
          <template #default="scope">
            <span v-if="scope.row.ssh_key_path">{{ scope.row.ssh_key_path }}</span>
            <span v-else class="no-value">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-tag type="success" v-if="scope.row.is_active">活跃</el-tag>
            <el-tag type="info" v-else>非活跃</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="scope">
            {{ new Date(scope.row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" min-width="180">
          <template #default="scope">
            {{ new Date(scope.row.updated_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-space>
              <el-button size="small" type="primary" @click="setActiveConfig(scope.row)" :disabled="scope.row.is_active">
                <el-icon><Check /></el-icon>
                设为活跃
              </el-button>
              <el-button size="small" type="success" @click="testGitConnection(scope.row)">
                <el-icon><Refresh /></el-icon>
                测试连接
              </el-button>
              <el-button size="small" type="warning" @click="openForm(scope.row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteGitConfig(scope.row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <!-- 活跃配置提示 -->
      <div class="active-config-tip" v-if="activeConfig">
        <el-alert
          title="当前活跃的Git配置"
          type="success"
          :closable="false"
          style="margin-top: 20px"
        >
          <div>{{ activeConfig.repo_url }}</div>
          <div style="margin-top: 5px; font-size: 12px; color: #606266;">
            分支: {{ activeConfig.branch }} | 用户名: {{ activeConfig.username || '无' }}
          </div>
        </el-alert>
      </div>
    </el-card>

    <!-- Git配置表单对话框 -->
    <el-dialog
      v-model="showForm"
      :title="isEdit ? '编辑Git配置' : '新增Git配置'"
      width="600px"
      :before-close="closeForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="仓库URL" prop="repo_url">
          <el-input v-model="form.repo_url" placeholder="https://github.com/username/repo.git" />
        </el-form-item>
        
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="Git用户名" />
        </el-form-item>
        
        <el-form-item label="密码/Token">
          <el-input v-model="form.password" type="password" placeholder="Git密码或Token" />
        </el-form-item>
        
        <el-form-item label="分支" prop="branch">
          <el-input v-model="form.branch" placeholder="main" />
        </el-form-item>
        
        <el-form-item label="SSH密钥路径">
          <el-input v-model="form.ssh_key_path" placeholder="/path/to/ssh/key" />
        </el-form-item>
        
        <el-form-item label="设为活跃">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-space>
          <el-button @click="closeForm">
            <el-icon><Close /></el-icon>
            取消
          </el-button>
          <el-button type="primary" @click="saveGitConfig" :loading="loading">
            <el-icon><Check /></el-icon>
            保存
          </el-button>
        </el-space>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.git-config-management {
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

.no-value {
  color: #999;
  font-style: italic;
}

.active-config-tip {
  margin-top: 20px;
}
</style>