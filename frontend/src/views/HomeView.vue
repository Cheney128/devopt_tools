<script setup>
import { ref, onMounted, computed } from 'vue'
import { Server, Check, Alert, DataAnalysis } from '@element-plus/icons-vue'
import { useDeviceStore } from '../stores/deviceStore'

const deviceStore = useDeviceStore()
const loading = ref(false)

// 计算属性
const totalDevices = computed(() => deviceStore.deviceCount)
const activeDevices = computed(() => deviceStore.activeDevices.length)
const inactiveDevices = computed(() => deviceStore.inactiveDevices.length)

// 方法
const fetchData = async () => {
  loading.value = true
  try {
    await deviceStore.fetchDevices()
  } catch (error) {
    console.error('Failed to fetch data:', error)
  } finally {
    loading.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="home-view">
    <el-card shadow="hover" class="welcome-card">
      <template #header>
        <div class="card-header">
          <span>欢迎使用交换机管理系统</span>
        </div>
      </template>
      <div class="welcome-content">
        <p>本系统提供交换机的批量管理和巡检功能，帮助您更高效地管理网络设备。</p>
        <p>通过左侧导航栏，您可以访问以下功能模块：</p>
        <ul>
          <li>设备管理：管理交换机基本信息、状态等</li>
          <li>端口管理：配置和监控交换机端口</li>
          <li>VLAN管理：配置和管理VLAN信息</li>
          <li>巡检管理：批量巡检设备状态和性能</li>
          <li>配置管理：管理设备配置和与Oxidized集成</li>
        </ul>
      </div>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ totalDevices }}</div>
            <div class="stat-label">总设备数</div>
          </div>
          <div class="stat-icon">
            <el-icon class="icon"><Server /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card success">
          <div class="stat-content">
            <div class="stat-number">{{ activeDevices }}</div>
            <div class="stat-label">活跃设备</div>
          </div>
          <div class="stat-icon">
            <el-icon class="icon"><Check /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card warning">
          <div class="stat-content">
            <div class="stat-number">{{ inactiveDevices }}</div>
            <div class="stat-label">非活跃设备</div>
          </div>
          <div class="stat-icon">
            <el-icon class="icon"><Alert /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card info">
          <div class="stat-content">
            <div class="stat-number">0</div>
            <div class="stat-label">今日巡检</div>
          </div>
          <div class="stat-icon">
            <el-icon class="icon"><DataAnalysis /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="recent-activities">
      <template #header>
        <div class="card-header">
          <span>最近活动</span>
        </div>
      </template>
      <el-table :data="[]" style="width: 100%" v-loading="loading">
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="user" label="操作人" width="120" />
      </el-table>
      <div class="no-data" v-if="!loading">
        <el-empty description="暂无活动记录" />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.home-view {
  padding: 0 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-content {
  line-height: 1.8;
}

.welcome-content ul {
  margin: 10px 0;
  padding-left: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 140px;
  position: relative;
  overflow: hidden;
}

.stat-content {
  position: relative;
  z-index: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-icon {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 48px;
  opacity: 0.1;
}

.stat-card.success .stat-icon {
  color: #67c23a;
}

.stat-card.warning .stat-icon {
  color: #e6a23c;
}

.stat-card.info .stat-icon {
  color: #409eff;
}

.recent-activities {
  margin-top: 20px;
}

.no-data {
  padding: 40px 0;
  text-align: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>