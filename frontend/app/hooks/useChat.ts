import { useState, useRef, useEffect } from 'react'
import { API_URL } from '../../config'
import { Message } from '../types'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (
    userMessage: string,
    backendAvailable: boolean,
    setBackendAvailable: (available: boolean) => void
  ) => {
    if (!userMessage.trim() || loading || !backendAvailable) return

    setError(null)
    setLoading(true)

    // Add user message to UI immediately (preserve in history even if backend fails)
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage.trim() }]
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
      // Mark backend as unavailable
      setBackendAvailable(false)
    } finally {
      setLoading(false)
    }
  }

  return {
    messages,
    sessionId,
    loading,
    error,
    messagesEndRef,
    sendMessage,
  }
}

