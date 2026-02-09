<template>
  <div class="backup-monitoring">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>备份计划监控</span>
          <div class="header-actions">
            <el-button type="primary" @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计概览 -->
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
            <el-statistic 
              title="成功率" 
              :value="statistics.success_rate || 0" 
              suffix="%" 
            />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <el-statistic title="今日备份" :value="dashboard.devices_backup_today || 0" suffix="台" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 趋势图表 -->
      <el-row :gutter="20" class="chart-row">
        <el-col :span="16">
          <el-card shadow="hover">
            <template #header>
              <span>备份趋势 (最近{{ trendDays }}天)</span>
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

      <!-- 执行日志 -->
      <el-card shadow="hover" class="log-card">
        <template #header>
          <div class="card-header">
            <span>最近执行日志</span>
            <el-button text type="primary" @click="showAllLogs">查看全部</el-button>
          </div>
        </template>
        
        <el-table :data="recentLogs" style="width: 100%" stripe>
          <el-table-column prop="device_name" label="设备" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
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
              <span v-if="row.error_message" :class="{ 'no-change-badge': row.error_message.includes('配置无变化') }">
                <el-icon v-if="row.error_message.includes('配置无变化')"><Info-Filled /></el-icon>
                {{ row.error_message }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

    </el-card>

    <!-- 全部日志对话框 -->
    <el-dialog
      v-model="showLogsDialog"
      title="执行日志"
      width="80%"
    >
      <div class="log-filters">
        <el-form :inline="true" :model="logFilters">
          <el-form-item label="状态">
            <el-select v-model="logFilters.status" placeholder="全部" clearable>
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="超时" value="timeout" />
              <el-option label="取消" value="cancelled" />
            </el-select>
          </el-form-item>
          <el-form-item label="触发类型">
            <el-select v-model="logFilters.trigger_type" placeholder="全部" clearable>
              <el-option label="计划任务" value="scheduled" />
              <el-option label="手动触发" value="manual" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadExecutionLogs">查询</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <el-table :data="executionLogs" style="width: 100%" stripe v-loading="logsLoading">
        <el-table-column prop="device_name" label="设备" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
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
            {{ row.error_message || '-' }}
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-if="logTotal > 0"
        v-model:current-page="logPage"
        v-model:page-size="logPageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="logTotal"
        layout="total, sizes, prev, pager, next"
        @size-change="loadExecutionLogs"
        @current-change="loadExecutionLogs"
        class="pagination"
      />
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { Refresh, InfoFilled } from '@element-plus/icons-vue'
import { monitoringApi } from '../api/index'
import * as echarts from 'echarts'

export default {
  name: 'BackupMonitoring',
  components: {
    Refresh,
    InfoFilled
  },
  setup() {
    const loading = ref(false)
    const logsLoading = ref(false)
    const trendChartRef = ref(null)
    const statusChartRef = ref(null)
    const showLogsDialog = ref(false)
    const trendDays = ref(7)
    
    const statistics = ref({})
    const dashboard = ref({})
    const recentLogs = ref([])
    const executionLogs = ref([])
    const trendData = ref([])
    
    const logFilters = reactive({
      status: null,
      trigger_type: null
    })
    const logPage = ref(1)
    const logPageSize = ref(20)
    const logTotal = ref(0)
    
    let trendChart = null
    let statusChart = null
    
    const getStatistics = async () => {
      try {
        const response = await monitoringApi.getStatistics()
        statistics.value = response || {}
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    }
    
    const getDashboard = async () => {
      try {
        const response = await monitoringApi.getDashboard()
        dashboard.value = response || {}
        recentLogs.value = response.recent_executions || []
      } catch (error) {
        console.error('获取仪表盘数据失败:', error)
      }
    }
    
    const getTrends = async () => {
      try {
        const response = await monitoringApi.getTrends(trendDays.value)
        trendData.value = response || []
        nextTick(() => {
          initTrendChart()
        })
      } catch (error) {
        console.error('获取趋势数据失败:', error)
      }
    }
    
    const loadExecutionLogs = async () => {
      logsLoading.value = true
      try {
        const response = await monitoringApi.getExecutionLogs({
          page: logPage.value,
          page_size: logPageSize.value,
          status: logFilters.status,
          triggerType: logFilters.trigger_type
        })
        executionLogs.value = response.logs || []
        logTotal.value = response.total || 0
      } catch (error) {
        console.error('获取执行日志失败:', error)
      } finally {
        logsLoading.value = false
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
    
    const refreshData = async () => {
      loading.value = true
      try {
        await Promise.all([
          getStatistics(),
          getDashboard(),
          getTrends()
        ])
        nextTick(() => {
          initStatusChart()
        })
      } finally {
        loading.value = false
      }
    }
    
    const showAllLogs = () => {
      showLogsDialog.value = true
      loadExecutionLogs()
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
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
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
    
    return {
      loading,
      logsLoading,
      trendChartRef,
      statusChartRef,
      showLogsDialog,
      trendDays,
      statistics,
      dashboard,
      recentLogs,
      executionLogs,
      trendData,
      logFilters,
      logPage,
      logPageSize,
      logTotal,
      refreshData,
      loadExecutionLogs,
      showAllLogs,
      getStatusType,
      getStatusText,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.backup-monitoring {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
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

.log-card {
  margin-top: 20px;
}

.log-filters {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.no-change-badge {
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
