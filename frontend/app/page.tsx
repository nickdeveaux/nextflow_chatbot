'use client'

import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { 
  API_URL, 
  LOADING_MESSAGES
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
  const [backendAvailable, setBackendAvailable] = useState(true)
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

  // Backend health check polling
  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 3000) // 3 second timeout
        
        const response = await fetch(`${API_URL}/health`, {
          method: 'GET',
          signal: controller.signal,
        })
        
        clearTimeout(timeoutId)
        setBackendAvailable(response.ok)
      } catch (err) {
        setBackendAvailable(false)
      }
    }

    // Check immediately
    checkBackendHealth()

    // Then check every 5 seconds
    const interval = setInterval(checkBackendHealth, 5000)

    return () => clearInterval(interval)
  }, [])

  const handleSend = async () => {
    if (!input.trim() || loading || !backendAvailable) return

    const userMessage = input.trim()
    setInput('')
    setError(null)
    setLoading(true)

    // Add user message to UI immediately (preserve in history even if backend fails)
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
      setError(null)
    } catch (err) {
      // Backend failed - keep user message in history, show error
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(`Failed to send message: ${errorMessage}. The backend is currently unavailable.`)
      // User message is already in messages, so we keep it
      // Mark backend as unavailable
      setBackendAvailable(false)
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

  const downloadChatHistory = () => {
    if (messages.length === 0) return

    // Format chat history as readable text
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    const filename = `nextflow-chat-history-${timestamp}.txt`
    
    let content = `Nextflow Chat Assistant - Chat History\n`
    content += `Exported: ${new Date().toLocaleString()}\n`
    content += `Session ID: ${sessionId || 'N/A'}\n`
    content += `Total Messages: ${messages.length}\n`
    content += `\n${'='.repeat(60)}\n\n`

    messages.forEach((message, index) => {
      const role = message.role === 'user' ? 'User' : 'Assistant'
      content += `[${index + 1}] ${role}:\n`
      content += `${message.content}\n`
      
      if (message.citations && message.citations.length > 0) {
        content += `\nCitations:\n`
        message.citations.forEach((url, i) => {
          content += `  ${i + 1}. ${url}\n`
        })
      }
      
      content += `\n${'-'.repeat(60)}\n\n`
    })

    // Create blob and download
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="container">
      {/* Backend unavailable modal */}
      {!backendAvailable && (
        <div className="modal-overlay" onClick={() => {}}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon">😢</div>
            <h2>Backend Unavailable</h2>
            <p>The backend service is currently unavailable. Please try again later.</p>
            <p className="modal-subtext">The chat history can be downloaded for this session.</p>
            {messages.length > 0 && (
              <button
                className="modal-download-button"
                onClick={downloadChatHistory}
                aria-label="Download chat history"
              >
                📥 Download Chat History
              </button>
            )}
          </div>
        </div>
      )}

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
                <div className="markdown-content">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                    components={{
                      // Style code blocks
                      code: ({ className, children, ...props }: any) => {
                        const match = /language-(\w+)/.exec(className || '')
                        const isInline = !match
                        return isInline ? (
                          <code className="markdown-inline-code" {...props}>
                            {children}
                          </code>
                        ) : (
                          <pre className="markdown-code-block">
                            <code className={className} {...props}>
                              {children}
                            </code>
                          </pre>
                        )
                      },
                      // Style links
                      a: ({ href, children, ...props }: any) => (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="markdown-link"
                          {...props}
                        >
                          {children}
                        </a>
                      ),
                      // Style lists
                      ul: ({ children, ...props }: any) => (
                        <ul className="markdown-list" {...props}>
                          {children}
                        </ul>
                      ),
                      ol: ({ children, ...props }: any) => (
                        <ol className="markdown-list" {...props}>
                          {children}
                        </ol>
                      ),
                      // Style blockquotes
                      blockquote: ({ children, ...props }: any) => (
                        <blockquote className="markdown-blockquote" {...props}>
                          {children}
                        </blockquote>
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
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
            placeholder={backendAvailable ? "Type your message..." : "Backend unavailable..."}
            rows={1}
            disabled={loading || !backendAvailable}
          />
          <button
            className="send-button"
            onClick={handleSend}
            disabled={loading || !input.trim() || !backendAvailable}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

