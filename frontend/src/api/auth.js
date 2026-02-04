import api from './index'

export const authApi = {
  // 获取验证码
  getCaptcha: () => api.get('/auth/captcha'),
  
  // 登录
  login: (data) => api.post('/auth/login', data),
  
  // 登出
  logout: () => api.post('/auth/logout'),
  
  // 获取当前用户信息
  getCurrentUser: () => api.get('/auth/me')
}

export const userApi = {
  // 获取用户列表（管理员）
  getUsers: (params) => api.get('/users', { params }),
  
  // 创建用户（管理员）
  createUser: (data) => api.post('/users', data),
  
  // 获取指定用户信息（管理员）
  getUser: (id) => api.get(`/users/${id}`),
  
  // 更新用户信息（管理员）
  updateUser: (id, data) => api.put(`/users/${id}`, data),
  
  // 删除用户（管理员）
  deleteUser: (id) => api.delete(`/users/${id}`),
  
  // 重置用户密码（管理员）
  resetPassword: (id, data) => api.post(`/users/${id}/reset-password`, data),
  
  // 获取当前用户个人信息
  getMyProfile: () => api.get('/users/me'),
  
  // 更新当前用户个人信息
  updateMyProfile: (data) => api.put('/users/me', data),
  
  // 修改当前用户密码
  changePassword: (data) => api.put('/users/me/password', data)
}
