/**
 * Tests for the Nextflow Chat Assistant frontend.
 * Run with: npm test
 */
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import Home from '../app/page'

// Mock fetch
global.fetch = jest.fn()

describe('Nextflow Chat Assistant', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear()
    // Mock localStorage
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

    // Type a message
    input.setAttribute('value', 'Test message')
    ;(input as HTMLTextAreaElement).value = 'Test message'

    // Click send
    sendButton.click()

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled()
    })
  })

  it('handles API errors gracefully', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    render(<Home />)
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    input.setAttribute('value', 'Test message')
    ;(input as HTMLTextAreaElement).value = 'Test message'

    sendButton.click()

    await waitFor(() => {
      // Should show error or attempt fallback
      expect(fetch).toHaveBeenCalled()
    })
  })

  it('renders theme toggle button', () => {
    render(<Home />)
    const themeToggle = screen.getByLabelText('Toggle dark mode')
    expect(themeToggle).toBeInTheDocument()
  })
})

