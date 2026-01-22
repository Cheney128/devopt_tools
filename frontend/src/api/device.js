import api from './index'

// 设备管理API
const deviceApi = {
  getDevices: (params) => api.get('/devices', { params }),
  getDevice: (id) => api.get(`/devices/${id}`),
  createDevice: (data) => api.post('/devices', data),
  updateDevice: (id, data) => api.put(`/devices/${id}`, data),
  deleteDevice: (id) => api.delete(`/devices/${id}`),
  batchDeleteDevices: (ids) => api.post('/devices/batch/delete', ids),
  batchUpdateStatus: (ids, status) => api.post('/devices/batch/update-status', ids, { params: { status } }),
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

export default deviceApi