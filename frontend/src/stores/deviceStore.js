import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { deviceApi } from '../api/index'

export const useDeviceStore = defineStore('device', () => {
  // 从localStorage加载保存的状态，添加错误处理
  const loadStateFromLocalStorage = () => {
    try {
      const savedState = localStorage.getItem('deviceStoreState')
      if (savedState) {
        const parsedState = JSON.parse(savedState)
        // 验证状态数据的有效性
        if (parsedState.searchForm && typeof parsedState.searchForm === 'object') {
          return parsedState
        }
      }
    } catch (err) {
      console.error('Failed to load state from localStorage:', err)
    }
    // 返回默认状态
    return {
      searchForm: { status: '', vendor: '' },
      currentPage: 1,
      pageSize: 10
    }
  }

  // 保存状态到localStorage，添加错误处理
  const saveStateToLocalStorage = (state) => {
    try {
      localStorage.setItem('deviceStoreState', JSON.stringify(state))
    } catch (err) {
      console.error('Failed to save state to localStorage:', err)
    }
  }

  // 加载初始状态
  const initialState = loadStateFromLocalStorage()

  // State
  const devices = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentDevice = ref(null)
  const total = ref(0) // 总记录数
  
  // 搜索表单状态
  const searchForm = ref(initialState.searchForm)
  // 分页状态
  const currentPage = ref(initialState.currentPage)
  const pageSize = ref(initialState.pageSize)

  // Getters
  const deviceCount = computed(() => total.value)
  const activeDevices = computed(() => devices.value.filter(device => device.status === 'active'))
  const inactiveDevices = computed(() => devices.value.filter(device => device.status !== 'active'))

  // Actions
  async function fetchDevices(filterParams = {}) {
    loading.value = true
    error.value = null
    try {
      // 合并传入的筛选参数和存储的筛选参数
      const params = {
        ...searchForm.value,
        page: currentPage.value,
        page_size: pageSize.value,
        ...filterParams
      }
      const response = await deviceApi.getDevices(params)
      devices.value = response.devices
      total.value = response.total
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  // 更新搜索表单并保存到localStorage
  function updateSearchForm(newForm) {
    searchForm.value = { ...searchForm.value, ...newForm }
    saveStateToLocalStorage({
      searchForm: searchForm.value,
      currentPage: currentPage.value,
      pageSize: pageSize.value
    })
  }

  // 重置搜索表单并保存到localStorage
  function resetSearchForm() {
    searchForm.value = { status: '', vendor: '' }
    saveStateToLocalStorage({
      searchForm: searchForm.value,
      currentPage: currentPage.value,
      pageSize: pageSize.value
    })
  }

  // 更新当前页码并保存到localStorage
  function setCurrentPage(page) {
    currentPage.value = page
    saveStateToLocalStorage({
      searchForm: searchForm.value,
      currentPage: currentPage.value,
      pageSize: pageSize.value
    })
  }

  // 更新每页条数并保存到localStorage
  function setPageSize(size) {
    pageSize.value = size
    currentPage.value = 1 // 重置到第一页
    saveStateToLocalStorage({
      searchForm: searchForm.value,
      currentPage: currentPage.value,
      pageSize: pageSize.value
    })
  }

  async function fetchDeviceById(id) {
    loading.value = true
    error.value = null
    try {
      currentDevice.value = await deviceApi.getDevice(id)
      return currentDevice.value
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function createDevice(deviceData) {
    loading.value = true
    error.value = null
    try {
      const newDevice = await deviceApi.createDevice(deviceData)
      devices.value.push(newDevice)
      return newDevice
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateDevice(id, deviceData) {
    loading.value = true
    error.value = null
    try {
      const updatedDevice = await deviceApi.updateDevice(id, deviceData)
      const index = devices.value.findIndex(device => device.id === id)
      if (index !== -1) {
        devices.value[index] = updatedDevice
      }
      return updatedDevice
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteDevice(id) {
    loading.value = true
    error.value = null
    try {
      await deviceApi.deleteDevice(id)
      devices.value = devices.value.filter(device => device.id !== id)
      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function batchDeleteDevices(ids) {
    loading.value = true
    error.value = null
    try {
      const result = await deviceApi.batchDeleteDevices(ids)
      if (result.success) {
        devices.value = devices.value.filter(device => !ids.includes(device.id))
      }
      return result
    } catch (err) {
      error.value = err.message
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  async function batchUpdateStatus(ids, status) {
    loading.value = true
    error.value = null
    try {
      const result = await deviceApi.batchUpdateStatus(ids, status)
      if (result.success) {
        devices.value.forEach(device => {
          if (ids.includes(device.id)) {
            device.status = status
          }
        })
      }
      return result
    } catch (err) {
      error.value = err.message
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  return {
    devices,
    loading,
    error,
    currentDevice,
    total,
    searchForm,
    currentPage,
    pageSize,
    deviceCount,
    activeDevices,
    inactiveDevices,
    fetchDevices,
    updateSearchForm,
    resetSearchForm,
    setCurrentPage,
    setPageSize,
    fetchDeviceById,
    createDevice,
    updateDevice,
    deleteDevice,
    batchDeleteDevices,
    batchUpdateStatus
  }
})