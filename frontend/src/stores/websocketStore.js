import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWebSocketStore = defineStore('websocket', () => {
  const socket = ref(null)
  const isConnected = ref(false)
  const lastMessage = ref(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000
  
  const heartbeatInterval = ref(null)
  const heartbeatTimeout = 30000
  
  const connectionStatus = computed(() => {
    if (isConnected.value) return 'connected'
    if (reconnectAttempts.value >= maxReconnectAttempts) return 'failed'
    return 'disconnected'
  })
  
  function getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}/api/v1/ws/latency`
  }
  
  function connect(onMessage) {
    if (socket.value && isConnected.value) {
      console.log('[WebSocket] Already connected')
      return
    }
    
    const url = getWebSocketUrl()
    console.log('[WebSocket] Connecting to:', url)
    
    socket.value = new WebSocket(url)
    
    socket.value.onopen = () => {
      console.log('[WebSocket] Connected')
      isConnected.value = true
      reconnectAttempts.value = 0
      startHeartbeat()
    }
    
    socket.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        lastMessage.value = message
        
        if (message.type === 'latency_update' && onMessage) {
          onMessage(message.data)
        } else if (message.type === 'pong') {
          console.log('[WebSocket] Heartbeat OK')
        } else if (message.type === 'connected') {
          console.log('[WebSocket] Server confirmed connection')
        }
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error)
      }
    }
    
    socket.value.onclose = (event) => {
      console.log('[WebSocket] Disconnected:', event.code, event.reason)
      isConnected.value = false
      stopHeartbeat()
      
      if (reconnectAttempts.value < maxReconnectAttempts) {
        reconnectAttempts.value++
        console.log(`[WebSocket] Reconnecting... Attempt ${reconnectAttempts.value}/${maxReconnectAttempts}`)
        setTimeout(() => connect(onMessage), reconnectDelay)
      }
    }
    
    socket.value.onerror = (error) => {
      console.error('[WebSocket] Error:', error)
    }
  }
  
  function disconnect() {
    stopHeartbeat()
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    isConnected.value = false
    reconnectAttempts.value = 0
    console.log('[WebSocket] Disconnected manually')
  }
  
  function send(message) {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify(message))
    }
  }
  
  function startHeartbeat() {
    stopHeartbeat()
    heartbeatInterval.value = setInterval(() => {
      if (isConnected.value) {
        send({ type: 'ping' })
      }
    }, heartbeatTimeout)
  }
  
  function stopHeartbeat() {
    if (heartbeatInterval.value) {
      clearInterval(heartbeatInterval.value)
      heartbeatInterval.value = null
    }
  }
  
  return {
    socket,
    isConnected,
    lastMessage,
    reconnectAttempts,
    connectionStatus,
    connect,
    disconnect,
    send
  }
})
