import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import router from '../src/router'
import DeviceManagement from '../src/views/DeviceManagement.vue'
import { deviceApi } from '../src/api'

// 模拟设备数据
const mockDevices = [
  {
    id: 27,
    hostname: '模块33-R06-业务接入',
    ip_address: '10.23.2.95',
    vendor: 'Huawei',
    model: 'S5735S-L24',
    status: 'active',
    login_method: 'ssh',
    login_port: 22,
    username: 'admin',
    password: 'password'
  },
  {
    id: 26,
    hostname: '模块33-R05-业务接入',
    ip_address: '10.23.2.94',
    vendor: 'Huawei',
    model: 'S5735S-L24',
    status: 'active',
    login_method: 'ssh',
    login_port: 22,
    username: 'admin',
    password: 'password'
  }
]

// 模拟设备API
vi.mock('../src/api', () => ({
  deviceApi: {
    getDevices: vi.fn(() => Promise.resolve({ devices: mockDevices, total: 2 })),
    executeCommand: vi.fn(),
    batchExecuteCommand: vi.fn()
  }
}))

// 模拟设备Store
vi.mock('../src/stores/deviceStore', () => ({
  useDeviceStore: vi.fn(() => ({
    devices: mockDevices,
    deviceCount: 2,
    currentPage: 1,
    pageSize: 10,
    searchForm: {},
    fetchDevices: vi.fn(),
    resetSearchForm: vi.fn(),
    setPageSize: vi.fn(),
    setCurrentPage: vi.fn(),
    updateSearchForm: vi.fn(),
    deleteDevice: vi.fn(),
    batchDeleteDevices: vi.fn(),
    batchUpdateStatus: vi.fn(),
    createDevice: vi.fn(),
    updateDevice: vi.fn()
  }))
}))

describe('DeviceManagement.vue', () => {
  let wrapper

  beforeEach(() => {
    // 重置所有模拟函数
    vi.clearAllMocks()
    
    // 创建包装器
    wrapper = mount(DeviceManagement, {
      global: {
        plugins: [createPinia(), router, ElementPlus],
        stubs: ['el-upload', 'el-icon', 'el-scrollbar']
      }
    })
  })

  it('渲染设备列表', () => {
    expect(wrapper.find('.device-management').exists()).toBe(true)
    expect(wrapper.find('.el-table').exists()).toBe(true)
  })

  it('检查命令执行对话框相关数据属性是否存在', () => {
    // 检查组件是否有命令执行相关的数据属性
    expect(wrapper.vm.commandDialogVisible).toBe(false)
    expect(wrapper.vm.command).toBe('')
    expect(wrapper.vm.commandLoading).toBe(false)
    expect(wrapper.vm.currentCommandDeviceId).toBe(null)
  })

  it('检查命令执行方法是否存在', () => {
    // 检查组件是否有命令执行相关的方法
    expect(typeof wrapper.vm.handleExecuteCommand).toBe('function')
    expect(typeof wrapper.vm.handleBatchExecuteCommand).toBe('function')
    expect(typeof wrapper.vm.executeCommand).toBe('function')
  })

  it('调用handleExecuteCommand方法应设置currentCommandDeviceId', async () => {
    // 调用handleExecuteCommand方法
    await wrapper.vm.handleExecuteCommand(mockDevices[0])
    
    // 检查currentCommandDeviceId是否被正确设置
    expect(wrapper.vm.currentCommandDeviceId).toBe(27)
    expect(wrapper.vm.commandDialogTitle).toBe('执行命令 - 模块33-R06-业务接入')
  })

  it('调用handleBatchExecuteCommand方法应设置selectedDevicesForCommand', async () => {
    // 设置multipleSelection为mockDevices
    wrapper.vm.multipleSelection = mockDevices
    
    // 调用handleBatchExecuteCommand方法
    await wrapper.vm.handleBatchExecuteCommand()
    
    // 检查selectedDevicesForCommand是否被正确设置
    expect(wrapper.vm.selectedDevicesForCommand).toEqual([27, 26])
    expect(wrapper.vm.commandDialogTitle).toContain('批量执行命令')
  })

  it('执行命令方法应调用deviceApi.executeCommand', async () => {
    // 模拟executeCommand API调用
    const mockResponse = {
      success: true,
      message: '命令执行成功',
      device_id: 27,
      hostname: '模块33-R06-业务接入',
      command: 'system-view\nsysname NX-SW-33-R06-YW-test',
      output: 'Command executed successfully'
    }
    deviceApi.executeCommand.mockResolvedValue(mockResponse)
    
    // 设置currentCommandDeviceId和command
    wrapper.vm.currentCommandDeviceId = 27
    wrapper.vm.command = 'system-view\nsysname NX-SW-33-R06-YW-test'
    
    // 调用executeCommand方法
    await wrapper.vm.executeCommand()
    
    // 检查API是否被调用
    expect(deviceApi.executeCommand).toHaveBeenCalledWith(27, 'system-view\nsysname NX-SW-33-R06-YW-test')
  })

  it('执行批量命令方法应调用deviceApi.batchExecuteCommand', async () => {
    // 模拟batchExecuteCommand API调用
    const mockResponse = {
      total: 2,
      success_count: 2,
      failed_count: 0,
      results: [
        {
          device_id: 27,
          hostname: '模块33-R06-业务接入',
          success: true,
          message: '命令执行成功',
          output: 'Command executed successfully'
        },
        {
          device_id: 26,
          hostname: '模块33-R05-业务接入',
          success: true,
          message: '命令执行成功',
          output: 'Command executed successfully'
        }
      ]
    }
    deviceApi.batchExecuteCommand.mockResolvedValue(mockResponse)
    
    // 设置selectedDevicesForCommand和command
    wrapper.vm.selectedDevicesForCommand = [27, 26]
    wrapper.vm.command = 'display version'
    wrapper.vm.currentCommandDeviceId = null
    
    // 调用executeCommand方法
    await wrapper.vm.executeCommand()
    
    // 检查API是否被调用
    expect(deviceApi.batchExecuteCommand).toHaveBeenCalledWith([27, 26], 'display version')
  })
})
