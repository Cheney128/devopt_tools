<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  DataBoard, 
  Calendar, 
  Monitor, 
  FolderOpened 
} from '@element-plus/icons-vue'
import BackupOverview from './backup/BackupOverview.vue'
import BackupScheduleManagement from './backup/BackupScheduleManagement.vue'
import BackupMonitoring from './backup/BackupMonitoring.vue'
import GitConfigManagement from './backup/GitConfigManagement.vue'

const route = useRoute()
const router = useRouter()

const activeTab = ref('overview')

const tabs = [
  { name: 'overview', label: '概览', icon: DataBoard },
  { name: 'schedules', label: '备份计划', icon: Calendar },
  { name: 'monitoring', label: '备份监控', icon: Monitor },
  { name: 'git-configs', label: 'Git配置', icon: FolderOpened }
]

const handleTabClick = (tab) => {
  const tabName = tab.props.name
  if (tabName === 'overview') {
    router.push('/backup-management')
  } else {
    router.push(`/backup-management/${tabName}`)
  }
}

const handleSwitchTab = (tabName) => {
  activeTab.value = tabName
  if (tabName === 'overview') {
    router.push('/backup-management')
  } else {
    router.push(`/backup-management/${tabName}`)
  }
}

watch(() => route.path, (newPath) => {
  if (newPath === '/backup-management') {
    activeTab.value = 'overview'
  } else if (newPath.startsWith('/backup-management/')) {
    const parts = newPath.split('/')
    activeTab.value = parts[2] || 'overview'
  }
}, { immediate: true })

onMounted(() => {
  if (route.path === '/backup-management') {
    activeTab.value = 'overview'
  } else if (route.path.startsWith('/backup-management/')) {
    const parts = route.path.split('/')
    activeTab.value = parts[2] || 'overview'
  }
})
</script>

<template>
  <div class="backup-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>备份管理</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <el-tab-pane name="overview">
          <template #label>
            <span class="tab-label">
              <el-icon><DataBoard /></el-icon>
              概览
            </span>
          </template>
          <BackupOverview @switchTab="handleSwitchTab" />
        </el-tab-pane>

        <el-tab-pane name="schedules">
          <template #label>
            <span class="tab-label">
              <el-icon><Calendar /></el-icon>
              备份计划
            </span>
          </template>
          <BackupScheduleManagement />
        </el-tab-pane>

        <el-tab-pane name="monitoring">
          <template #label>
            <span class="tab-label">
              <el-icon><Monitor /></el-icon>
              备份监控
            </span>
          </template>
          <BackupMonitoring />
        </el-tab-pane>

        <el-tab-pane name="git-configs">
          <template #label>
            <span class="tab-label">
              <el-icon><FolderOpened /></el-icon>
              Git配置
            </span>
          </template>
          <GitConfigManagement />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.backup-management {
  padding: 0 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 5px;
}
</style>
