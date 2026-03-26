import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import IPLocationSearch from '../src/views/ip-location/IPLocationSearch.vue'
import IPLocationList from '../src/views/ip-location/IPLocationList.vue'

const { searchIP, getIPList } = vi.hoisted(() => ({
  searchIP: vi.fn(),
  getIPList: vi.fn()
}))

vi.mock('../src/api/index', () => ({
  ipLocationApi: {
    searchIP,
    getIPList
  }
}))

describe('IPLocation Views', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('搜索页默认使用快照模式', async () => {
    searchIP.mockResolvedValue({
      success: true,
      locations: []
    })
    const wrapper = mount(IPLocationSearch, {
      global: {
        plugins: [ElementPlus]
      }
    })
    await wrapper.find('input').setValue('10.0.0.1')
    await wrapper.vm.handleSearch()
    expect(searchIP).toHaveBeenCalledWith('10.0.0.1', true, true, 'snapshot')
  })

  it('列表页默认请求快照模式参数', async () => {
    getIPList.mockResolvedValue({
      total: 0,
      items: []
    })
    mount(IPLocationList, {
      global: {
        plugins: [ElementPlus]
      }
    })
    await Promise.resolve()
    expect(getIPList).toHaveBeenCalled()
    const firstCall = getIPList.mock.calls[0][0]
    expect(firstCall.mode).toBe('snapshot')
  })
})
