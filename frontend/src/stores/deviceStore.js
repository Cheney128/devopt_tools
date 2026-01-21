import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import deviceApi from '../api/device'

export const useDeviceStore = defineStore('device', () => {
  // State
  const devices = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentDevice = ref(null)

  // Getters
  const deviceCount = computed(() => devices.value.length)
  const activeDevices = computed(() => devices.value.filter(device => device.status === 'active'))
  const inactiveDevices = computed(() => devices.value.filter(device => device.status !== 'active'))

  // Actions
  async function fetchDevices() {
    loading.value = true
    error.value = null
    try {
      devices.value = await deviceApi.getDevices()
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
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
    deviceCount,
    activeDevices,
    inactiveDevices,
    fetchDevices,
    fetchDeviceById,
    createDevice,
    updateDevice,
    deleteDevice,
    batchDeleteDevices,
    batchUpdateStatus
  }
})