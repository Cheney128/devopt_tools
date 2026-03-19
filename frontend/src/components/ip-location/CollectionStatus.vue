<script setup>
import { computed } from 'vue'
import { ElButton, ElTag, ElTooltip } from 'element-plus'
import { Refresh, RefreshRight, Warning, SuccessFilled } from '@element-plus/icons-vue'

const props = defineProps({
  status: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['refresh', 'trigger'])

const isRunning = computed(() => props.status?.is_running || false)
const lastRunSuccess = computed(() => props.status?.last_run_success !== false)
const lastRunAt = computed(() => props.status?.last_run_at || null)

const progressPercent = computed(() => {
  if (!props.status || props.status.devices_total === 0) return 0
  return Math.round((props.status.devices_completed / props.status.devices_total) * 100)
})

const statusType = computed(() => {
  if (isRunning.value) return 'primary'
  if (!lastRunSuccess.value) return 'danger'
  return 'success'
})

const statusText = computed(() => {
  if (isRunning.value) return '收集中'
  if (!lastRunSuccess.value) return '上次失败'
  return '就绪'
})

const handleRefresh = () => {
  emit('refresh')
}

const handleTrigger = () => {
  emit('trigger')
}
</script>

<template>
  <div class="collection-status">
    <div class="status-left">
      <el-tag :type="statusType" size="small" effect="dark">
        <component :is="isRunning ? Refresh : (lastRunSuccess ? SuccessFilled : Warning)" class="tag-icon" />
        {{ statusText }}
      </el-tag>

      <div v-if="isRunning" class="progress-info">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <span class="progress-text">
          {{ status?.devices_completed || 0 }} / {{ status?.devices_total || 0 }}
        </span>
      </div>

      <div v-else-if="lastRunAt" class="last-run">
        <span class="last-run-label">上次收集:</span>
        <span class="last-run-time">{{ new Date(lastRunAt).toLocaleString('zh-CN') }}</span>
      </div>
    </div>

    <div class="status-right">
      <div v-if="status" class="stats">
        <el-tooltip content="ARP 条目">
          <div class="stat-item">
            <span class="stat-label">ARP:</span>
            <span class="stat-value">{{ status.arp_entries_collected || 0 }}</span>
          </div>
        </el-tooltip>
        <el-tooltip content="MAC 条目">
          <div class="stat-item">
            <span class="stat-label">MAC:</span>
            <span class="stat-value">{{ status.mac_entries_collected || 0 }}</span>
          </div>
        </el-tooltip>
      </div>

      <el-button
        size="small"
        :icon="Refresh"
        :loading="loading"
        @click="handleRefresh"
      >
        刷新
      </el-button>
      <el-button
        type="primary"
        size="small"
        :icon="RefreshRight"
        :loading="loading"
        :disabled="isRunning"
        @click="handleTrigger"
      >
        立即收集
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.collection-status {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.status-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.tag-icon {
  margin-right: 4px;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  width: 120px;
  height: 8px;
  background: #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #409eff;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #606266;
  min-width: 50px;
}

.last-run {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
}

.last-run-label {
  color: #606266;
}

.last-run-time {
  color: #303133;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stats {
  display: flex;
  gap: 16px;
  margin-right: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.stat-label {
  color: #909399;
}

.stat-value {
  color: #303133;
  font-weight: 600;
}
</style>
