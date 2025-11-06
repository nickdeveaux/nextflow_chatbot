'use client'

import { useState, useRef, useEffect } from 'react'
import { 
  API_URL, 
  LOADING_MESSAGES, 
  SYSTEM_PROMPT, 
  getGeminiApiUrl 
} from '../config'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: string[]
}

interface CitationRef {
  index: number
  url: string
}

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

  const callGeminiDirect = async (query: string, conversationHistory: Message[] = []): Promise<string> => {
    const messages = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...conversationHistory.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      })),
      { role: 'user', content: query }
    ]

    const response = await fetch(getGeminiApiUrl(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: messages.filter(m => m.role !== 'system').map(m => ({
          role: m.role === 'user' ? 'user' : 'model',
          parts: [{ text: m.content }]
        })),
        systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] }
      }),
    })

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`)
    }

    const data = await response.json()
    return data.candidates[0].content.parts[0].text
  }

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
      // If backend is down, try calling Gemini directly
      try {
        console.log('Backend unavailable, calling Gemini directly...')
        const geminiResponse = await callGeminiDirect(userMessage, messages)
        setMessages([
          ...newMessages,
          {
            role: 'assistant',
            content: geminiResponse,
            citations: ['https://www.nextflow.io/docs/latest/'],
          },
        ])
        setError(null)
      } catch (geminiErr) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred'
        setError(`Failed to send message: ${errorMessage}. Backend and Gemini fallback both unavailable.`)
        // Remove the user message on error
        setMessages(messages)
      }
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

        {messages.map((message, index) => {
          const citations = message.citations || []
          const citationRefs: CitationRef[] = []
          const urlToIndex = new Map<string, number>()
          
          // Build citation map
          citations.forEach((url) => {
            if (!urlToIndex.has(url)) {
              const refNum = urlToIndex.size + 1
              urlToIndex.set(url, refNum)
              citationRefs.push({ index: refNum, url })
            }
          })
          
          return (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-content">
                <div style={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                  {citationRefs.length > 0 && (
                    <span className="citation-inline">
                      {citationRefs.map((ref) => (
                        <a
                          key={ref.index}
                          href={ref.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="citation-link"
                          title={ref.url}
                        >
                          <sup>{ref.index}</sup>
                        </a>
                      ))}
                    </span>
                  )}
                </div>
                {citationRefs.length > 0 && (
                  <div className="message-citations">
                    <div className="citation-list">
                      {citationRefs.map((ref) => (
                        <div key={ref.index} className="citation-item">
                          <sup className="citation-number">{ref.index}</sup>
                          <a
                            href={ref.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="citation-url"
                          >
                            {ref.url}
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}

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

