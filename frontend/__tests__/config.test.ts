/**
 * Tests for configuration module.
 */
import { 
  API_URL, 
  LOADING_MESSAGES
} from '../config'

describe('Config', () => {
  it('should have API_URL defined', () => {
    expect(API_URL).toBeDefined()
    expect(typeof API_URL).toBe('string')
    expect(API_URL.length).toBeGreaterThan(0)
    expect(API_URL).toMatch(/^https?:\/\//)
  })

  it('should have LOADING_MESSAGES array', () => {
    expect(LOADING_MESSAGES).toBeDefined()
    expect(Array.isArray(LOADING_MESSAGES)).toBe(true)
    expect(LOADING_MESSAGES.length).toBeGreaterThan(0)
    LOADING_MESSAGES.forEach(msg => {
      expect(typeof msg).toBe('string')
      expect(msg.length).toBeGreaterThan(0)
    })
  })

  it('should have unique loading messages', () => {
    const unique = new Set(LOADING_MESSAGES)
    expect(unique.size).toBe(LOADING_MESSAGES.length)
  })
})

