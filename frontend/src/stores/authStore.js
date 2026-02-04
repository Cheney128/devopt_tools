import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const isLoading = ref(false)
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
      // 如果获取失败，清除登录状态
      if (error.response?.status === 401) {
        logout()
      }
      throw error
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
      localStorage.removeItem('token')
    }
  }

  // 更新用户信息
  const updateUserInfo = (newUserInfo) => {
    user.value = { ...user.value, ...newUserInfo }
  }

  // 初始化（页面刷新时调用）
  const init = async () => {
    if (token.value) {
      await fetchCurrentUser()
    }
  }

  return {
    // State
    token,
    user,
    isLoading,
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
