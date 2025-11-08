/**
 * Tests for the Nextflow Chat Assistant frontend.
 * Run with: npm test
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import Home from '../app/page'

// Mock fetch
global.fetch = jest.fn()

// Mock config
jest.mock('../config', () => ({
  API_URL: 'http://localhost:8000',
  LOADING_MESSAGES: ['Thinking', 'Pondering'],
}))

describe('Nextflow Chat Assistant', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear()
    Storage.prototype.getItem = jest.fn(() => null)
    Storage.prototype.setItem = jest.fn()
    
    // Mock health check endpoint to return success by default
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })
  })

  it('renders the header', () => {
    render(<Home />)
    expect(screen.getByText('Nextflow Chat Assistant')).toBeInTheDocument()
  })

  it('renders the welcome message when no messages', () => {
    render(<Home />)
    expect(screen.getByText(/Welcome to Nextflow Chat Assistant/i)).toBeInTheDocument()
  })

  it('renders the chat input', () => {
    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    expect(input).toBeInTheDocument()
  })

  it('renders the send button', () => {
    render(<Home />)
    const sendButton = screen.getByText('Send')
    expect(sendButton).toBeInTheDocument()
  })

  it('disables send button when input is empty', () => {
    render(<Home />)
    const sendButton = screen.getByText('Send')
    expect(sendButton).toBeDisabled()
  })

  it('enables send button when input has text', () => {
    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    expect(sendButton).not.toBeDisabled()
  })

  it('sends a message when clicking send', async () => {
    const mockResponse = {
      reply: 'Test response',
      session_id: 'test-session-id',
      citations: null
    }

    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      const chatCalls = (fetch as jest.Mock).mock.calls.filter(
        call => call[0]?.includes('/chat')
      )
      expect(chatCalls.length).toBeGreaterThan(0)
    })

    const chatCall = (fetch as jest.Mock).mock.calls.find(
      call => call[0]?.includes('/chat')
    )
    expect(chatCall[0]).toContain('/chat')
    expect(chatCall[1].method).toBe('POST')
  })

  it('displays user message after sending', async () => {
    const mockResponse = {
      reply: 'Test response',
      session_id: 'test-session-id',
      citations: null
    }

    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument()
    })
  })

  it('displays assistant response after receiving it', async () => {
    const mockResponse = {
      reply: 'Assistant reply',
      session_id: 'test-session-id',
      citations: null
    }

    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Assistant reply')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully and preserves user message', async () => {
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.reject(new Error('Network error'))
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      // User message should still be in the chat
      expect(screen.getByText('Test message')).toBeInTheDocument()
      // Error message should be shown
      expect(screen.getByText(/Failed to send message/i)).toBeInTheDocument()
    })
  })

  it('renders theme toggle button', () => {
    render(<Home />)
    const themeToggle = screen.getByLabelText('Toggle dark mode')
    expect(themeToggle).toBeInTheDocument()
  })

  it('toggles dark mode when theme button is clicked', () => {
    render(<Home />)
    const themeToggle = screen.getByLabelText('Toggle dark mode')
    
    fireEvent.click(themeToggle)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    
    fireEvent.click(themeToggle)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('displays citations when provided', async () => {
    const mockResponse = {
      reply: 'Test response',
      session_id: 'test-session-id',
      citations: ['https://example.com/doc1', 'https://example.com/doc2']
    }

    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      const citationLinks = screen.getAllByText(/https:\/\/example\.com/)
      expect(citationLinks.length).toBeGreaterThan(0)
    })
  })

  it('handles Enter key to send message', async () => {
    const mockResponse = {
      reply: 'Response',
      session_id: 'test-session-id',
      citations: null
    }

    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...') as HTMLTextAreaElement

    fireEvent.change(input, { target: { value: 'Test' } })
    // Simulate Enter key press (not Shift+Enter)
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', keyCode: 13, shiftKey: false })
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', keyCode: 13, shiftKey: false })

    await waitFor(() => {
      const chatCalls = (fetch as jest.Mock).mock.calls.filter(
        call => call[0]?.includes('/chat')
      )
      expect(chatCalls.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })

  it('does not send on Shift+Enter', () => {
    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')

    // Clear health check calls
    ;(fetch as jest.Mock).mockClear()

    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.keyPress(input, { key: 'Enter', shiftKey: true })

    // Should not have called /chat endpoint
    const chatCalls = (fetch as jest.Mock).mock.calls.filter(
      call => call[0]?.includes('/chat')
    )
    expect(chatCalls.length).toBe(0)
  })

  it('shows modal when backend is unavailable', async () => {
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.reject(new Error('Backend unavailable'))
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)

    await waitFor(() => {
      expect(screen.getByText('Backend Unavailable')).toBeInTheDocument()
      expect(screen.getByText(/The backend service is currently unavailable/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('shows download button in modal when messages exist', async () => {
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.reject(new Error('Backend unavailable'))
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            reply: 'Test response',
            session_id: 'test-session-id',
            citations: null
          }),
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    
    // First, add a message (before backend goes down)
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            reply: 'Test response',
            session_id: 'test-session-id',
            citations: null
          }),
        })
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument()
    })

    // Now simulate backend going down
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.reject(new Error('Backend unavailable'))
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    // Trigger health check by waiting a bit
    await waitFor(() => {
      expect(screen.getByText('Backend Unavailable')).toBeInTheDocument()
      expect(screen.getByText(/Download Chat History/i)).toBeInTheDocument()
    }, { timeout: 6000 })
  })

  it('disables input when backend is unavailable', async () => {
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.reject(new Error('Backend unavailable'))
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)

    await waitFor(() => {
      const input = screen.getByPlaceholderText('Backend unavailable...')
      expect(input).toBeDisabled()
      const sendButton = screen.getByText('Send')
      expect(sendButton).toBeDisabled()
    }, { timeout: 5000 })
  })

  it('preserves chat history when backend fails', async () => {
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' }),
        })
      }
      if (url.includes('/chat')) {
        return Promise.reject(new Error('Backend error'))
      }
      return Promise.reject(new Error(`Unexpected call to ${url}`))
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      // User message should be preserved even though backend failed
      expect(screen.getByText('Test message')).toBeInTheDocument()
      // Error should be shown
      expect(screen.getByText(/Failed to send message/i)).toBeInTheDocument()
    })
  })

})
