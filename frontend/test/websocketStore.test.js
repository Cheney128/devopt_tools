/**
 * WebSocket Store 单元测试
 * 
 * 测试范围:
 * - 连接状态管理
 * - 消息处理
 * - 重连机制
 * - 心跳机制
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// 模拟 WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    this.onopen = null
    this.onmessage = null
    this.onclose = null
    this.onerror = null
    
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) this.onopen({ type: 'open' })
    }, 10)
  }
  
  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
  }
  
  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) this.onclose({ code: 1000, reason: 'Normal closure' })
  }
  
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) })
    }
  }
}

describe('WebSocket Store', () => {
  let store
  let originalWebSocket
  
  beforeEach(() => {
    setActivePinia(createPinia())
    
    originalWebSocket = global.WebSocket
    global.WebSocket = MockWebSocket
  })
  
  afterEach(() => {
    if (store) {
      store.disconnect()
    }
    global.WebSocket = originalWebSocket
  })
  
  describe('连接管理', () => {
    it('应该正确初始化状态', async () => {
      const { useWebSocketStore } = await import('../src/stores/websocketStore')
      store = useWebSocketStore()
      
      expect(store.isConnected).toBe(false)
      expect(store.socket).toBe(null)
      expect(store.reconnectAttempts).toBe(0)
    })
    
    it('应该成功建立WebSocket连接', async () => {
      const { useWebSocketStore } = await import('../src/stores/websocketStore')
      store = useWebSocketStore()
      
      const onMessage = vi.fn()
      
      await new Promise(resolve => {
        store.connect(onMessage)
        setTimeout(resolve, 50)
      })
      
      expect(store.isConnected).toBe(true)
      expect(store.socket).not.toBe(null)
    })
    
    it('应该正确断开连接', async () => {
      const { useWebSocketStore } = await import('../src/stores/websocketStore')
      store = useWebSocketStore()
      
      await new Promise(resolve => {
        store.connect()
        setTimeout(resolve, 50)
      })
      
      store.disconnect()
      
      expect(store.isConnected).toBe(false)
      expect(store.socket).toBe(null)
    })
  })
  
  describe('消息处理', () => {
    it('应该正确处理延迟更新消息', async () => {
      const { useWebSocketStore } = await import('../src/stores/websocketStore')
      store = useWebSocketStore()
      
      const onMessage = vi.fn()
      const mockWs = await new Promise(resolve => {
        store.connect(onMessage)
        setTimeout(() => resolve(store.socket), 50)
      })
      
      const latencyData = {
        type: 'latency_update',
        data: {
          device_id: 1,
          latency: 25,
          last_latency_check: '2026-03-16T10:30:00',
          status: 'active'
        },
        timestamp: '2026-03-16T10:30:00.123456'
      }
      
      mockWs.simulateMessage(latencyData)
      
      expect(onMessage).toHaveBeenCalledWith(latencyData.data)
      expect(store.lastMessage).toEqual(latencyData)
    })
    
    it('应该正确处理心跳响应', async () => {
      const { useWebSocketStore } = await import('../src/stores/websocketStore')
      store = useWebSocketStore()
      
      const mockWs = await new Promise(resolve => {
        store.connect()
        setTimeout(() => resolve(store.socket), 50)
      })
      
      const consoleSpy = vi.spyOn(console, 'log')
      
      mockWs.simulateMessage({ type: 'pong', timestamp: '2026-03-16T10:30:00' })
      
      expect(consoleSpy).toHaveBeenCalledWith('[WebSocket] Heartbeat OK')
    })
  })
})
