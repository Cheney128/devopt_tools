<script setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { 
  DataBoard, 
  Calendar, 
  Monitor, 
  FolderOpened,
  Refresh,
  InfoFilled
} from '@element-plus/icons-vue'
import { monitoringApi } from '../../api/index'
import * as echarts from 'echarts'

const emit = defineEmits(['switchTab'])

const loading = ref(false)
const statistics = ref({})
const dashboard = ref({})
const recentLogs = ref([])
const trendData = ref([])

const trendChartRef = ref(null)
const statusChartRef = ref(null)
let trendChart = null
let statusChart = null

const quickActions = [
  { 
    name: 'schedules', 
    label: '管理备份计划', 
    icon: Calendar, 
    description: '创建、编辑、删除备份计划',
    color: '#409EFF'
  },
  { 
    name: 'monitoring', 
    label: '查看监控面板', 
    icon: Monitor, 
    description: '查看备份执行状态和趋势',
    color: '#67C23A'
  },
  { 
    name: 'git-configs', 
    label: '配置Git仓库', 
    icon: FolderOpened, 
    description: '管理Git仓库配置',
    color: '#E6A23C'
  }
]

const handleQuickAction = (tabName) => {
  emit('switchTab', tabName)
}

const refreshData = async () => {
  loading.value = true
  try {
    const [statsRes, dashboardRes, trendsRes] = await Promise.all([
      monitoringApi.getStatistics(),
      monitoringApi.getDashboard(),
      monitoringApi.getTrends(7)
    ])
    statistics.value = statsRes || {}
    dashboard.value = dashboardRes || {}
    recentLogs.value = dashboardRes?.recent_executions || []
    trendData.value = trendsRes || []
    
    nextTick(() => {
      initTrendChart()
      initStatusChart()
    })
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  
  if (trendChart) {
    trendChart.dispose()
  }
  
  trendChart = echarts.init(trendChartRef.value)
  
  const dates = trendData.value.map(item => item.date)
  const successData = trendData.value.map(item => item.success)
  const failedData = trendData.value.map(item => item.failed)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['成功', '失败']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        data: successData,
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        data: failedData,
        itemStyle: { color: '#f56c6c' }
      }
    ]
  }
  
  trendChart.setOption(option)
}

const initStatusChart = () => {
  if (!statusChartRef.value) return
  
  if (statusChart) {
    statusChart.dispose()
  }
  
  statusChart = echarts.init(statusChartRef.value)
  
  const stats = statistics.value
  const data = [
    { value: stats.successful_executions || 0, name: '成功', itemStyle: { color: '#67c23a' } },
    { value: stats.failed_executions || 0, name: '失败', itemStyle: { color: '#f56c6c' } }
  ]
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  statusChart.setOption(option)
}

const getStatusType = (status) => {
  const statusMap = {
    success: 'success',
    failed: 'danger',
    timeout: 'warning',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    success: '成功',
    failed: '失败',
    timeout: '超时',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const handleResize = () => {
  trendChart?.resize()
  statusChart?.resize()
}

onMounted(() => {
  refreshData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  statusChart?.dispose()
})
</script>

<template>
  <div class="backup-overview" v-loading="loading">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="设备总数" :value="statistics.total_devices || 0" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="备份计划" :value="statistics.active_schedules || 0" suffix="个" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="成功率" :value="statistics.success_rate || 0" suffix="%" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="今日备份" :value="dashboard.devices_backup_today || 0" suffix="台" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="quick-actions-card">
      <template #header>
        <span>快捷操作</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8" v-for="action in quickActions" :key="action.name">
          <el-card 
            shadow="hover" 
            class="quick-action-card"
            @click="handleQuickAction(action.name)"
          >
            <div class="action-icon" :style="{ color: action.color }">
              <el-icon :size="32"><component :is="action.icon" /></el-icon>
            </div>
            <div class="action-title">{{ action.label }}</div>
            <div class="action-desc">{{ action.description }}</div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>最近备份趋势 (7天)</span>
              <el-button type="primary" size="small" @click="refreshData" :loading="loading">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <div ref="trendChartRef" class="trend-chart"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>执行状态分布</span>
          </template>
          <div ref="statusChartRef" class="status-chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="log-card">
      <template #header>
        <span>最近执行日志</span>
      </template>
      <el-table :data="recentLogs" style="width: 100%" stripe size="small">
        <el-table-column prop="device_name" label="设备" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_type" label="触发类型" width="100">
          <template #default="{ row }">
            {{ row.trigger_type === 'scheduled' ? '计划' : '手动' }}
          </template>
        </el-table-column>
        <el-table-column prop="execution_time" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.execution_time ? `${row.execution_time.toFixed(2)}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="执行时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="备注" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" :class="{ 'no-change': row.error_message.includes('配置无变化') }">
              {{ row.error_message }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.backup-overview {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.quick-actions-card {
  margin-bottom: 20px;
}

.quick-action-card {
  cursor: pointer;
  text-align: center;
  padding: 20px;
  transition: all 0.3s ease;
}

.quick-action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-icon {
  margin-bottom: 10px;
}

.action-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 5px;
}

.action-desc {
  font-size: 12px;
  color: #909399;
}

.chart-row {
  margin-bottom: 20px;
}

.trend-chart {
  height: 300px;
}

.status-chart {
  height: 300px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-card {
  margin-top: 20px;
}

.no-change {
  color: #67c23a;
}
</style>
