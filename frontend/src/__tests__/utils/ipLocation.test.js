import { describe, it, expect } from 'vitest'
import {
  getConfidenceType,
  getConfidenceText,
  getConfidenceColor,
  getInterfaceTypeTag,
  formatLastSeen
} from '../../utils/ipLocation'

describe('ipLocation utils', () =&gt; {
  describe('getConfidenceType', () =&gt; {
    it('should return success for confidence &gt;= 0.9', () =&gt; {
      expect(getConfidenceType(0.9)).toBe('success')
      expect(getConfidenceType(1.0)).toBe('success')
      expect(getConfidenceType(0.95)).toBe('success')
    })

    it('should return warning for confidence &gt;= 0.6 and &lt; 0.9', () =&gt; {
      expect(getConfidenceType(0.6)).toBe('warning')
      expect(getConfidenceType(0.75)).toBe('warning')
      expect(getConfidenceType(0.89)).toBe('warning')
    })

    it('should return danger for confidence &lt; 0.6', () =&gt; {
      expect(getConfidenceType(0.59)).toBe('danger')
      expect(getConfidenceType(0.5)).toBe('danger')
      expect(getConfidenceType(0)).toBe('danger')
    })
  })

  describe('getConfidenceText', () =&gt; {
    it('should return 高 for confidence &gt;= 0.9', () =&gt; {
      expect(getConfidenceText(0.9)).toBe('高')
      expect(getConfidenceText(1.0)).toBe('高')
    })

    it('should return 中 for confidence &gt;= 0.6 and &lt; 0.9', () =&gt; {
      expect(getConfidenceText(0.6)).toBe('中')
      expect(getConfidenceText(0.75)).toBe('中')
    })

    it('should return 低 for confidence &lt; 0.6', () =&gt; {
      expect(getConfidenceText(0.5)).toBe('低')
      expect(getConfidenceText(0)).toBe('低')
    })
  })

  describe('getConfidenceColor', () =&gt; {
    it('should return green for high confidence', () =&gt; {
      expect(getConfidenceColor(0.9)).toBe('#67C23A')
    })

    it('should return orange for medium confidence', () =&gt; {
      expect(getConfidenceColor(0.7)).toBe('#E6A23C')
    })

    it('should return red for low confidence', () =&gt; {
      expect(getConfidenceColor(0.5)).toBe('#F56C6C')
    })
  })

  describe('getInterfaceTypeTag', () =&gt; {
    it('should return uplink tag for isUplink=true', () =&gt; {
      const result = getInterfaceTypeTag(true)
      expect(result.type).toBe('danger')
      expect(result.text).toBe('上联')
    })

    it('should return access tag for isUplink=false', () =&gt; {
      const result = getInterfaceTypeTag(false)
      expect(result.type).toBe('success')
      expect(result.text).toBe('接入')
    })
  })

  describe('formatLastSeen', () =&gt; {
    it('should return - for empty date', () =&gt; {
      expect(formatLastSeen(null)).toBe('-')
      expect(formatLastSeen('')).toBe('-')
      expect(formatLastSeen(undefined)).toBe('-')
    })

    it('should format date string to locale string', () =&gt; {
      const dateStr = '2026-03-20T10:30:00Z'
      const result = formatLastSeen(dateStr)
      expect(result).not.toBe('-')
      expect(typeof result).toBe('string')
    })
  })
})
