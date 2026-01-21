/**
 * 设备信息采集状态管理
 * 使用Pinia进行状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  collectDeviceVersion,
  collectDeviceSerial,
  collectInterfacesInfo,
  collectMacTable,
  batchCollectDeviceInfo,
  getMacAddresses,
  searchMacAddresses,
  getDeviceMacAddresses
} from '@/api/deviceCollection'

export const useDeviceCollectionStore = defineStore('deviceCollection', () => {
  // 状态定义
  const loading = ref({
    version: false,
    serial: false,
    interfaces: false,
    macTable: false,
    batch: false,
    macAddresses: false
  })

  const collectionResults = ref([])
  const macTableData = ref([])
  const currentDeviceId = ref(null)

  // 计算属性
  const isLoading = computed(() => {
    return Object.values(loading.value).some(v => v)
  })

  const hasResults = computed(() => collectionResults.value.length > 0)
  const hasMacData = computed(() => macTableData.value.length > 0)

  // 方法
  const addResult = (title, success, message, data = null) => {
    collectionResults.value.unshift({
      title,
      success,
      message,
      data,
      timestamp: new Date().toLocaleString()
    })
  }

  const clearResults = () => {
    collectionResults.value = []
  }

  const clearMacData = () => {
    macTableData.value = []
  }

  // 设备信息采集操作
  const collectVersion = async (deviceId) => {
    loading.value.version = true
    try {
      const result = await collectDeviceVersion(deviceId)
      addResult('版本信息采集', result.success, result.message, result.data)
      return result
    } catch (error) {
      addResult('版本信息采集', false, error.message || '采集失败')
      throw error
    } finally {
      loading.value.version = false
    }
  }

  const collectSerial = async (deviceId) => {
    loading.value.serial = true
    try {
      const result = await collectDeviceSerial(deviceId)
      addResult('序列号采集', result.success, result.message, result.data)
      return result
    } catch (error) {
      addResult('序列号采集', false, error.message || '采集失败')
      throw error
    } finally {
      loading.value.serial = false
    }
  }

  const collectInterfaces = async (deviceId) => {
    loading.value.interfaces = true
    try {
      const result = await collectInterfacesInfo(deviceId)
      addResult('接口信息采集', result.success, result.message, result.data)
      return result
    } catch (error) {
      addResult('接口信息采集', false, error.message || '采集失败')
      throw error
    } finally {
      loading.value.interfaces = false
    }
  }

  const collectMacTable = async (deviceId) => {
    loading.value.macTable = true
    try {
      const result = await collectMacTable(deviceId)
      addResult('MAC地址表采集', result.success, result.message, result.data)
      if (result.success) {
        await loadMacTableData(deviceId)
      }
      return result
    } catch (error) {
      addResult('MAC地址表采集', false, error.message || '采集失败')
      throw error
    } finally {
      loading.value.macTable = false
    }
  }

  // 批量采集
  const batchCollect = async (deviceIds, collectTypes) => {
    loading.value.batch = true
    try {
      const result = await batchCollectDeviceInfo({
        device_ids: deviceIds,
        collect_types: collectTypes
      })
      addResult('批量采集', result.success, result.message, result.data)
      return result
    } catch (error) {
      addResult('批量采集', false, error.message || '批量采集失败')
      throw error
    } finally {
      loading.value.batch = false
    }
  }

  // MAC地址表操作
  const loadMacTableData = async (deviceId, params = {}) => {
    loading.value.macAddresses = true
    try {
      const data = await getDeviceMacAddresses(deviceId, params)
      macTableData.value = data
      currentDeviceId.value = deviceId
      return data
    } catch (error) {
      console.error('加载MAC地址表失败:', error)
      throw error
    } finally {
      loading.value.macAddresses = false
    }
  }

  const searchMacAddresses = async (macAddress) => {
    loading.value.macAddresses = true
    try {
      const data = await searchMacAddresses(macAddress)
      macTableData.value = data
      return data
    } catch (error) {
      console.error('搜索MAC地址失败:', error)
      throw error
    } finally {
      loading.value.macAddresses = false
    }
  }

  const getAllMacAddresses = async (params = {}) => {
    loading.value.macAddresses = true
    try {
      const data = await getMacAddresses(params)
      macTableData.value = data
      return data
    } catch (error) {
      console.error('获取MAC地址表失败:', error)
      throw error
    } finally {
      loading.value.macAddresses = false
    }
  }

  // 一键采集所有信息
  const collectAllInfo = async (deviceId) => {
    const results = []

    try {
      // 采集版本信息
      const versionResult = await collectVersion(deviceId)
      results.push({ type: 'version', result: versionResult })

      // 采集序列号
      const serialResult = await collectSerial(deviceId)
      results.push({ type: 'serial', result: serialResult })

      // 采集接口信息
      const interfacesResult = await collectInterfaces(deviceId)
      results.push({ type: 'interfaces', result: interfacesResult })

      // 采集MAC地址表
      const macTableResult = await collectMacTable(deviceId)
      results.push({ type: 'mac_table', result: macTableResult })

      return {
        success: results.every(r => r.result.success),
        results,
        message: '一键采集完成'
      }
    } catch (error) {
      return {
        success: false,
        results,
        message: error.message || '一键采集失败'
      }
    }
  }

  // 导出功能
  const exportMacTable = (filename = null) => {
    if (macTableData.value.length === 0) {
      throw new Error('没有MAC地址数据可导出')
    }

    const csvContent = macTableData.value.map(item =>
      `${item.mac_address},${item.vlan_id || ''},${item.interface},${item.address_type},${item.last_seen}`
    ).join('\n')

    const blob = new Blob(
      [`MAC地址,VLAN ID,接口,类型,最后发现时间\n${csvContent}`],
      { type: 'text/csv;charset=utf-8;' }
    )

    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)

    const timestamp = new Date().toISOString().slice(0, 10)
    const defaultFilename = currentDeviceId.value
      ? `mac_table_device_${currentDeviceId.value}_${timestamp}.csv`
      : `mac_table_all_${timestamp}.csv`

    link.download = filename || defaultFilename
    link.click()

    URL.revokeObjectURL(link.href)
  }

  return {
    // 状态
    loading,
    collectionResults,
    macTableData,
    currentDeviceId,

    // 计算属性
    isLoading,
    hasResults,
    hasMacData,

    // 方法
    addResult,
    clearResults,
    clearMacData,
    collectVersion,
    collectSerial,
    collectInterfaces,
    collectMacTable,
    batchCollect,
    loadMacTableData,
    searchMacAddresses,
    getAllMacAddresses,
    collectAllInfo,
    exportMacTable
  }
})
