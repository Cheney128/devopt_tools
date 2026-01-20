import api from './index'

// 设备管理API
const deviceApi = {
  getDevices: (params) => api.get('/devices', { params }),
  getDevice: (id) => api.get(`/devices/${id}`),
  createDevice: (data) => api.post('/devices', data),
  updateDevice: (id, data) => api.put(`/devices/${id}`, data),
  deleteDevice: (id) => api.delete(`/devices/${id}`),
  batchDeleteDevices: (ids) => api.post('/devices/batch/delete', ids),
  batchUpdateStatus: (ids, status) => api.post('/devices/batch/update-status', ids, { params: { status } })
}

export default deviceApi