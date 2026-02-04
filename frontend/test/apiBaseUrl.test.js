import { describe, it, expect } from 'vitest'
import { resolveApiBaseUrl } from '../src/api/index'

describe('resolveApiBaseUrl', () => {
  it('优先使用 VITE_API_BASE_URL', () => {
    expect(resolveApiBaseUrl({ VITE_API_BASE_URL: 'http://example.com/api/v1' })).toBe('http://example.com/api/v1')
  })

  it('缺省回退到 /api/v1', () => {
    expect(resolveApiBaseUrl({})).toBe('/api/v1')
  })
})
