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
  SYSTEM_PROMPT: 'Test system prompt',
  getGeminiApiUrl: jest.fn(() => 'https://test-api-url.com'),
}))

describe('Nextflow Chat Assistant', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear()
    Storage.prototype.getItem = jest.fn(() => null)
    Storage.prototype.setItem = jest.fn()
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

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled()
    })

    const fetchCall = (fetch as jest.Mock).mock.calls[0]
    expect(fetchCall[0]).toContain('/chat')
    expect(fetchCall[1].method).toBe('POST')
  })

  it('displays user message after sending', async () => {
    const mockResponse = {
      reply: 'Test response',
      session_id: 'test-session-id',
      citations: null
    }

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
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

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
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

  it('handles API errors gracefully', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled()
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

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
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

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')

    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled()
    })
  })

  it('does not send on Shift+Enter', () => {
    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')

    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.keyPress(input, { key: 'Enter', shiftKey: true })

    expect(fetch).not.toHaveBeenCalled()
  })
})
