import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加 Authorization Header
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 如果是 blob 类型的响应，直接返回 response，不要返回 response.data
    if (response.config.responseType === 'blob') {
      return response
    }
    return response.data
  },
  error => {
    console.error('API Error:', error)
    
    const { response } = error
    
    if (response) {
      const { status, data } = response
      const detail = data?.detail || '操作失败'
      
      switch (status) {
        case 401:
          // 未登录或 Token 过期
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          router.push('/login')
          break
        case 403:
          // 无权限
          ElMessage.error('权限不足，无法执行此操作')
          break
        case 404:
          // 资源不存在
          ElMessage.error('请求的资源不存在')
          break
        case 409:
          // 冲突（如用户名已存在）
          ElMessage.error(detail)
          break
        case 422:
          // 参数校验错误
          ElMessage.error(detail || '请求参数错误')
          break
        case 500:
          // 服务器错误
          ElMessage.error('服务器内部错误，请稍后重试')
          break
        default:
          ElMessage.error(detail || '操作失败')
      }
    } else {
      // 网络错误
      ElMessage.error('网络连接失败，请检查网络')
    }
    
    return Promise.reject(error)
  }
)

// 设备API
export const deviceApi = {
  getDevices: (params) => api.get('/devices', { params }),
  getDevice: (id) => api.get(`/devices/${id}`),
  createDevice: (data) => api.post('/devices', data),
  updateDevice: (id, data) => api.put(`/devices/${id}`, data),
  deleteDevice: (id) => api.delete(`/devices/${id}`),
  batchDeleteDevices: (ids) => api.post('/devices/batch/delete', ids),
  batchUpdateStatus: (ids, status) => api.post('/devices/batch/update-status', ids, { params: { status } }),
  testConnectivity: (id) => api.post(`/devices/${id}/test-connectivity`),
  // 执行设备命令
  executeCommand: (id, command, variables = {}, templateId = null) => api.post(`/devices/${id}/execute-command`, { command, variables, template_id: templateId }),
  // 批量执行设备命令
  batchExecuteCommand: (ids, command, variables = {}, templateId = null) => api.post('/devices/batch/execute-command', { device_ids: ids, command, variables, template_id: templateId }),
  
  // 命令模板API
  getCommandTemplates: (params = {}) => api.get('/command-templates', { params }),
  getCommandTemplate: (id) => api.get(`/command-templates/${id}`),
  createCommandTemplate: (data) => api.post('/command-templates', data),
  updateCommandTemplate: (id, data) => api.put(`/command-templates/${id}`, data),
  deleteCommandTemplate: (id) => api.delete(`/command-templates/${id}`),
  
  // 命令历史API
  getCommandHistory: (params = {}) => api.get('/command-history', { params }),
  getDeviceCommandHistory: (deviceId, params = {}) => api.get(`/command-history/device/${deviceId}`, { params }),
  deleteCommandHistory: (id) => api.delete(`/command-history/${id}`),
  deleteDeviceCommandHistory: (deviceId) => api.delete(`/command-history/device/${deviceId}`),
  deleteOldCommandHistory: (days = 30) => api.delete('/command-history', { params: { days } }),
  // 批量导入设备
  batchImportDevices: (file, skipExisting = false) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/devices/batch/import', formData, {
      params: { skip_existing: skipExisting },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  // 下载设备模板
  downloadTemplate: () => api.get('/devices/template', { responseType: 'blob' })
}

// 端口API
export const portApi = {
  getPorts: (params) => api.get('/ports', { params }),
  getPort: (id) => api.get(`/ports/${id}`),
  createPort: (data) => api.post('/ports', data),
  updatePort: (id, data) => api.put(`/ports/${id}`, data),
  deletePort: (id) => api.delete(`/ports/${id}`),
  batchDeletePorts: (ids) => api.post('/ports/batch/delete', ids)
}

// VLAN API
export const vlanApi = {
  getVlans: (params) => api.get('/vlans', { params }),
  getVlan: (id) => api.get(`/vlans/${id}`),
  createVlan: (data) => api.post('/vlans', data),
  updateVlan: (id, data) => api.put(`/vlans/${id}`, data),
  deleteVlan: (id) => api.delete(`/vlans/${id}`),
  batchDeleteVlans: (ids) => api.post('/vlans/batch/delete', ids)
}

// 巡检API
export const inspectionApi = {
  getInspections: (params) => api.get('/inspections', { params }),
  getInspection: (id) => api.get(`/inspections/${id}`),
  createInspection: (data) => api.post('/inspections', data),
  runInspection: (deviceId) => api.post(`/inspections/run/${deviceId}`),
  batchRunInspections: (deviceIds) => api.post('/inspections/batch/run', deviceIds)
}

// 配置API
export const configurationApi = {
  getConfigurations: (params) => api.get('/configurations', { params }),
  getConfiguration: (id) => api.get(`/configurations/${id}`),
  getLatestConfiguration: (deviceId) => api.get(`/configurations/device/${deviceId}/latest`),
  createConfiguration: (data) => api.post('/configurations', data),
  deleteConfiguration: (id) => api.delete(`/configurations/${id}`),
  batchDeleteConfigurations: (ids) => api.post('/configurations/batch/delete', ids),
  collectConfigFromDevice: (deviceId) => api.post(`/configurations/device/${deviceId}/collect`),
  getConfigDiff: (configId1, configId2) => api.get(`/configurations/diff/${configId1}/${configId2}`),
  commitConfigToGit: (id) => api.post(`/configurations/${id}/commit-git`),
  // 备份相关API
    createBackupSchedule: (data) => api.post('/configurations/backup-schedules', data),
    getBackupSchedules: (params) => api.get('/configurations/backup-schedules', { params }),
    updateBackupSchedule: (id, data) => api.put(`/configurations/backup-schedules/${id}`, data),
    deleteBackupSchedule: (id) => api.delete(`/configurations/backup-schedules/${id}`),
    batchCreateBackupSchedules: (deviceIds, data) => api.post('/configurations/backup-schedules/batch', { device_ids: deviceIds, ...data }),
    backupNow: (deviceId) => api.post(`/configurations/device/${deviceId}/backup-now`)
}

// Git配置API
export const gitConfigApi = {
  getGitConfigs: (params) => api.get('/git-configs', { params }),
  getGitConfig: (id) => api.get(`/git-configs/${id}`),
  createGitConfig: (data) => api.post('/git-configs', data),
  updateGitConfig: (id, data) => api.put(`/git-configs/${id}`, data),
  deleteGitConfig: (id) => api.delete(`/git-configs/${id}`),
  testGitConnection: (id) => api.post(`/git-configs/${id}/test`),
  setActiveGitConfig: (id) => api.post(`/git-configs/active/${id}`)
}

// 设备采集API
export const deviceCollectionApi = {
  // 采集设备版本信息
  collectDeviceVersion: (deviceId) => api.post(`/device-collection/${deviceId}/collect/version`),
  // 采集设备序列号
  collectDeviceSerial: (deviceId) => api.post(`/device-collection/${deviceId}/collect/serial`),
  // 采集接口信息
  collectInterfacesInfo: (deviceId) => api.post(`/device-collection/${deviceId}/collect/interfaces`),
  // 采集MAC地址表
  collectMacTable: (deviceId) => api.post(`/device-collection/${deviceId}/collect/mac-table`),
  // 批量采集设备信息
  batchCollectDeviceInfo: (data) => api.post('/device-collection/batch/collect', data),
  // 获取MAC地址表
  getMacAddresses: (params = {}) => api.get('/device-collection/mac-addresses', { params }),
  // 搜索MAC地址
  searchMacAddresses: (macAddress) => api.post('/device-collection/mac-addresses/search', { mac_address: macAddress }),
  // 获取指定设备的MAC地址表
  getDeviceMacAddresses: (deviceId, params = {}) => api.get(`/device-collection/${deviceId}/mac-addresses`, { params })
}

export default api
