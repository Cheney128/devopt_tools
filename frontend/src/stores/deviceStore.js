import { defineStore } from 'pinia'
import deviceApi from '../api/device'

export const useDeviceStore = defineStore('device', {
  state: () => ({
    devices: [],
    loading: false,
    error: null,
    currentDevice: null
  }),

  getters: {
    deviceCount: (state) => state.devices.length,
    activeDevices: (state) => state.devices.filter(device => device.status === 'active'),
    inactiveDevices: (state) => state.devices.filter(device => device.status !== 'active')
  },

  actions: {
    async fetchDevices() {
      this.loading = true
      this.error = null
      try {
        this.devices = await deviceApi.getDevices()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async fetchDeviceById(id) {
      this.loading = true
      this.error = null
      try {
        this.currentDevice = await deviceApi.getDevice(id)
        return this.currentDevice
      } catch (err) {
        this.error = err.message
        return null
      } finally {
        this.loading = false
      }
    },

    async createDevice(deviceData) {
      this.loading = true
      this.error = null
      try {
        const newDevice = await deviceApi.createDevice(deviceData)
        this.devices.push(newDevice)
        return newDevice
      } catch (err) {
        this.error = err.message
        return null
      } finally {
        this.loading = false
      }
    },

    async updateDevice(id, deviceData) {
      this.loading = true
      this.error = null
      try {
        const updatedDevice = await deviceApi.updateDevice(id, deviceData)
        const index = this.devices.findIndex(device => device.id === id)
        if (index !== -1) {
          this.devices[index] = updatedDevice
        }
        return updatedDevice
      } catch (err) {
        this.error = err.message
        return null
      } finally {
        this.loading = false
      }
    },

    async deleteDevice(id) {
      this.loading = true
      this.error = null
      try {
        await deviceApi.deleteDevice(id)
        this.devices = this.devices.filter(device => device.id !== id)
        return true
      } catch (err) {
        this.error = err.message
        return false
      } finally {
        this.loading = false
      }
    },

    async batchDeleteDevices(ids) {
      this.loading = true
      this.error = null
      try {
        const result = await deviceApi.batchDeleteDevices(ids)
        if (result.success) {
          this.devices = this.devices.filter(device => !ids.includes(device.id))
        }
        return result
      } catch (err) {
        this.error = err.message
        return { success: false, message: err.message }
      } finally {
        this.loading = false
      }
    },

    async batchUpdateStatus(ids, status) {
      this.loading = true
      this.error = null
      try {
        const result = await deviceApi.batchUpdateStatus(ids, status)
        if (result.success) {
          this.devices.forEach(device => {
            if (ids.includes(device.id)) {
              device.status = status
            }
          })
        }
        return result
      } catch (err) {
        this.error = err.message
        return { success: false, message: err.message }
      } finally {
        this.loading = false
      }
    }
  }
})