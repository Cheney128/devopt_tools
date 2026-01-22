import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 35000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
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
  testConnectivity: (id) => api.post(`/devices/${id}/test-connectivity`)
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
  getConfigDiff: (configId1, configId2) => api.get(`/configurations/diff/${configId1}/${configId2}`)
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

export default api