import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const isLoading = ref(false)
  const isInitialized = ref(false)  // 新增：初始化状态标记
  const captchaId = ref('')
  const captchaImage = ref('')

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => {
    if (!user.value || !user.value.roles) return false
    return user.value.roles.some(role => role.name === 'admin') || user.value.is_superuser
  })
  const username = computed(() => user.value?.username || '')
  const nickname = computed(() => user.value?.nickname || user.value?.username || '')
  const avatar = computed(() => user.value?.avatar || '')

  // Actions
  
  // 获取验证码
  const fetchCaptcha = async () => {
    try {
      const response = await authApi.getCaptcha()
      captchaId.value = response.captcha_id
      captchaImage.value = response.captcha_image
      return response
    } catch (error) {
      console.error('获取验证码失败:', error)
      throw error
    }
  }

  // 登录
  const login = async (credentials) => {
    isLoading.value = true
    try {
      const response = await authApi.login(credentials)
      
      // 保存 token
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      
      // 保存用户信息
      user.value = response.user
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 获取当前用户信息
  const fetchCurrentUser = async () => {
    if (!token.value) return null
    
    try {
      const response = await authApi.getCurrentUser()
      user.value = response
      return response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error  // 抛出错误让调用者处理
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地状态
      token.value = ''
      user.value = null
      isInitialized.value = false  // 重置初始化状态
      localStorage.removeItem('token')
    }
  }

  // 更新用户信息
  const updateUserInfo = (newUserInfo) => {
    user.value = { ...user.value, ...newUserInfo }
  }

  // 初始化（页面刷新时调用）
  const init = async () => {
    // 避免重复初始化
    if (!token.value || isInitialized.value) return
    
    isLoading.value = true
    try {
      await fetchCurrentUser()
    } catch (error) {
      console.error('初始化用户信息失败:', error)
      // 只有 401 错误才清除登录状态
      if (error.response?.status === 401) {
        token.value = ''
        user.value = null
        localStorage.removeItem('token')
      }
      // 其他错误（网络错误等）保持当前状态，让用户可以继续尝试
    } finally {
      isInitialized.value = true
      isLoading.value = false
    }
  }

  return {
    // State
    token,
    user,
    isLoading,
    isInitialized,  // 导出
    captchaId,
    captchaImage,
    // Getters
    isLoggedIn,
    isAdmin,
    username,
    nickname,
    avatar,
    // Actions
    fetchCaptcha,
    login,
    fetchCurrentUser,
    logout,
    updateUserInfo,
    init
  }
})
