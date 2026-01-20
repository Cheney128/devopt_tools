/**
 * 设备信息采集API服务
 * 提供基于Netmiko的设备信息采集功能
 */

import request from './index'

/**
 * 采集设备版本信息
 * @param {number} deviceId - 设备ID
 * @returns {Promise} 采集结果
 */
export function collectDeviceVersion(deviceId) {
  return request({
    url: `/devices/${deviceId}/collect/version`,
    method: 'post'
  })
}

/**
 * 采集设备序列号
 * @param {number} deviceId - 设备ID
 * @returns {Promise} 采集结果
 */
export function collectDeviceSerial(deviceId) {
  return request({
    url: `/devices/${deviceId}/collect/serial`,
    method: 'post'
  })
}

/**
 * 采集接口信息
 * @param {number} deviceId - 设备ID
 * @returns {Promise} 采集结果
 */
export function collectInterfacesInfo(deviceId) {
  return request({
    url: `/devices/${deviceId}/collect/interfaces`,
    method: 'post'
  })
}

/**
 * 采集MAC地址表
 * @param {number} deviceId - 设备ID
 * @returns {Promise} 采集结果
 */
export function collectMacTable(deviceId) {
  return request({
    url: `/devices/${deviceId}/collect/mac-table`,
    method: 'post'
  })
}

/**
 * 批量采集设备信息
 * @param {Object} data - 批量采集请求数据
 * @param {number[]} data.device_ids - 设备ID列表
 * @param {string[]} data.collect_types - 采集类型列表
 * @returns {Promise} 批量采集结果
 */
export function batchCollectDeviceInfo(data) {
  return request({
    url: '/devices/batch/collect',
    method: 'post',
    data
  })
}

/**
 * 获取MAC地址表
 * @param {Object} params - 查询参数
 * @param {number} params.device_id - 设备ID（可选）
 * @param {string} params.mac_address - MAC地址（可选）
 * @param {number} params.vlan_id - VLAN ID（可选）
 * @param {string} params.interface - 接口名称（可选）
 * @param {number} params.skip - 跳过记录数
 * @param {number} params.limit - 限制记录数
 * @returns {Promise} MAC地址列表
 */
export function getMacAddresses(params = {}) {
  return request({
    url: '/devices/mac-addresses',
    method: 'get',
    params
  })
}

/**
 * 搜索MAC地址
 * @param {string} macAddress - 要搜索的MAC地址
 * @returns {Promise} 搜索结果
 */
export function searchMacAddresses(macAddress) {
  return request({
    url: '/devices/mac-addresses/search',
    method: 'post',
    data: { mac_address: macAddress }
  })
}

/**
 * 获取指定设备的MAC地址表
 * @param {number} deviceId - 设备ID
 * @param {Object} params - 查询参数
 * @param {number} params.skip - 跳过记录数
 * @param {number} params.limit - 限制记录数
 * @returns {Promise} 设备MAC地址列表
 */
export function getDeviceMacAddresses(deviceId, params = {}) {
  return request({
    url: `/devices/${deviceId}/mac-addresses`,
    method: 'get',
    params
  })
}
