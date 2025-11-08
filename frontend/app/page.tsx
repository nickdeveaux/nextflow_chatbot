'use client'

import { useDarkMode } from './hooks/useDarkMode'
import { useBackendHealth } from './hooks/useBackendHealth'
import { useChat } from './hooks/useChat'
import { useInput } from './hooks/useInput'
import { useLoadingMessage } from './hooks/useLoadingMessage'
import { downloadChatHistory } from './utils'
import { ChatHeader } from './components/ChatHeader'
import { ChatMessages } from './components/ChatMessages'
import { ChatInput } from './components/ChatInput'
import { BackendUnavailableModal } from './components/BackendUnavailableModal'

export default function Home() {
  const { darkMode, toggleDarkMode } = useDarkMode()
  const { backendAvailable, setBackendAvailable } = useBackendHealth()
  const {
    messages,
    sessionId,
    loading,
    error,
    messagesEndRef,
    sendMessage,
  } = useChat()
  const {
    input,
    setInput,
    textareaRef,
    charCount,
    isNearLimit,
    remainingChars,
  } = useInput()
  const loadingMessage = useLoadingMessage(loading)

  const handleSend = async () => {
    if (!input.trim() || loading || !backendAvailable) return
    const messageToSend = input.trim()
    setInput('')
    await sendMessage(messageToSend, backendAvailable, setBackendAvailable)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleDownloadChatHistory = () => {
    downloadChatHistory(messages, sessionId)
  }

  return (
    <div className="container">
      {!backendAvailable && (
        <BackendUnavailableModal
          messages={messages}
          sessionId={sessionId}
          onDownloadChatHistory={handleDownloadChatHistory}
        />
      )}

      <ChatHeader darkMode={darkMode} onToggleDarkMode={toggleDarkMode} />

      <ChatMessages
        messages={messages}
        loading={loading}
        loadingMessage={loadingMessage}
        error={error}
        messagesEndRef={messagesEndRef}
      />

      <ChatInput
        input={input}
        setInput={setInput}
        textareaRef={textareaRef}
        charCount={charCount}
        isNearLimit={isNearLimit}
        remainingChars={remainingChars}
        loading={loading}
        backendAvailable={backendAvailable}
        onSend={handleSend}
        onKeyPress={handleKeyPress}
      />
    </div>
  )
}
