'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: string[]
}

const LOADING_MESSAGES = [
  'Thinking',
  'Pondering',
  'Noodling',
  'Considering',
  'Examining',
  'Researching',
  'Reflecting',
  'Evaluating',
  'Deliberating',
]

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [darkMode, setDarkMode] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    // Check for saved theme preference or default to system preference
    const savedTheme = localStorage.getItem('darkMode')
    if (savedTheme !== null) {
      setDarkMode(savedTheme === 'true')
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setDarkMode(prefersDark)
    }
  }, [])

  useEffect(() => {
    // Apply dark mode class to document
    if (darkMode) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('darkMode', 'true')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('darkMode', 'false')
    }
  }, [darkMode])

  useEffect(() => {
    if (!loading) {
      // Reset to first message when not loading
      setLoadingMessage(LOADING_MESSAGES[0])
      return
    }

    // Track which indexes we've already used
    const usedIndexes = new Set<number>()
    
    // Get a random unused index
    const getRandomUnusedIndex = (): number => {
      // If we've used all messages, reset
      if (usedIndexes.size >= LOADING_MESSAGES.length) {
        usedIndexes.clear()
      }
      
      // Get available indexes
      const availableIndexes = LOADING_MESSAGES
        .map((_, index) => index)
        .filter(index => !usedIndexes.has(index))
      
      // Randomly select from available
      const randomIndex = availableIndexes[Math.floor(Math.random() * availableIndexes.length)]
      usedIndexes.add(randomIndex)
      
      return randomIndex
    }

    // Start with a random message
    const initialIndex = getRandomUnusedIndex()
    setLoadingMessage(LOADING_MESSAGES[initialIndex])

    // Change message every 2 seconds with random unused selection
    const interval = setInterval(() => {
      const nextIndex = getRandomUnusedIndex()
      setLoadingMessage(LOADING_MESSAGES[nextIndex])
    }, 2000)

    return () => clearInterval(interval)
  }, [loading])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setError(null)
    setLoading(true)

    // Add user message to UI
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }]
    setMessages(newMessages)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Update session ID if this is the first message
      if (!sessionId) {
        setSessionId(data.session_id)
      }

      // Add assistant response
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: data.reply,
          citations: data.citations,
        },
      ])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(`Failed to send message: ${errorMessage}. Please check if the backend is running.`)
      // Remove the user message on error
      setMessages(messages)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Nextflow Chat Assistant</h1>
        <button
          className="theme-toggle"
          onClick={() => setDarkMode(!darkMode)}
          aria-label="Toggle dark mode"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <h2>Welcome to Nextflow Chat Assistant</h2>
            <p>Ask me anything about Nextflow documentation or troubleshooting</p>
            <p style={{ marginTop: '1rem', fontSize: '0.85rem' }}>
              Try: &quot;What is the latest version of Nextflow?&quot; or &quot;Are from and into parts of DSL2 syntax?&quot;
            </p>
          </div>
        )}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-content">
              <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
              {message.citations && message.citations.length > 0 && (
                <div className="message-citations">
                  <strong>Citations:</strong>
                  {message.citations.map((citation, i) => (
                    <a key={i} href={citation} target="_blank" rel="noopener noreferrer">
                      {citation}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="loading">
                <span>{loadingMessage}</span>
                <div className="loading-dots">
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            rows={1}
            disabled={loading}
          />
          <button
            className="send-button"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

