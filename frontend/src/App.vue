<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  HomeFilled as HomeIcon,
  Cpu as ServerIcon,
  Connection as ConnectionIcon,
  Grid as GridIcon,
  DataAnalysis as DataAnalysisIcon,
  Document as DocumentIcon,
  Monitor as MonitorIcon,
  FolderOpened as GitIcon,
  UserFilled as UserIcon,
  User as UserManagementIcon,
  SwitchButton as LogoutIcon
} from '@element-plus/icons-vue'
import { useAuthStore } from './stores/authStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeIndex = computed(() => route.path)
const isLoggedIn = computed(() => authStore.isLoggedIn)
const isAdmin = computed(() => authStore.isAdmin)
const userNickname = computed(() => authStore.nickname)

const handleSelect = (key, keyPath) => {
  console.log(key, keyPath)
}

// 处理登出
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('登出失败:', error)
    }
  }
}

// 跳转到个人中心
const goToProfile = () => {
  router.push('/profile')
}

// 初始化
onMounted(() => {
  authStore.init()
})
</script>

<template>
  <div class="app-container">
    <el-container v-if="isLoggedIn">
      <!-- 顶部导航栏 -->
      <el-header height="60px" class="header">
        <div class="logo">
          <h1>交换机管理系统</h1>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="32" :icon="UserIcon" />
              <span class="username">{{ userNickname }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToProfile">
                  <el-icon><UserIcon /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><LogoutIcon /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主体内容 -->
      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="200px" class="sidebar">
          <el-menu
            :default-active="activeIndex"
            class="el-menu-vertical-demo"
            @select="handleSelect"
            router
          >
            <el-menu-item index="/">
              <el-icon><HomeIcon /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/devices">
              <el-icon><ServerIcon /></el-icon>
              <span>设备管理</span>
            </el-menu-item>
            <el-menu-item index="/ports">
              <el-icon><ConnectionIcon /></el-icon>
              <span>端口管理</span>
            </el-menu-item>
            <el-menu-item index="/vlans">
              <el-icon><GridIcon /></el-icon>
              <span>VLAN管理</span>
            </el-menu-item>
            <el-menu-item index="/inspections">
              <el-icon><DataAnalysisIcon /></el-icon>
              <span>巡检管理</span>
            </el-menu-item>
            <el-menu-item index="/configurations">
              <el-icon><DocumentIcon /></el-icon>
              <span>配置管理</span>
            </el-menu-item>
            <el-menu-item index="/device-collection">
              <el-icon><MonitorIcon /></el-icon>
              <span>设备采集</span>
            </el-menu-item>
            <el-menu-item index="/git-configs">
              <el-icon><GitIcon /></el-icon>
              <span>Git配置管理</span>
            </el-menu-item>
            <el-menu-item v-if="isAdmin" index="/users">
              <el-icon><UserManagementIcon /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 内容区域 -->
        <el-main class="main-content">
          <router-view></router-view>
        </el-main>
      </el-container>
    </el-container>

    <!-- 未登录时只显示路由内容（登录页） -->
    <template v-else>
      <router-view></router-view>
    </template>
  </div>
</template>

<style>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background-color: #1890ff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.username {
  margin-left: 8px;
  margin-right: 4px;
  font-size: 14px;
}

.sidebar {
  background-color: #f0f2f5;
  border-right: 1px solid #e8e8e8;
}

.main-content {
  background-color: #fafafa;
  padding: 20px;
  overflow-y: auto;
}

.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 200px;
  min-height: 400px;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
