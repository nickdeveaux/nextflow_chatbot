import { Message } from '../types'
import { EmptyState } from './EmptyState'
import { ErrorMessage } from './ErrorMessage'
import { LoadingIndicator } from './LoadingIndicator'
import { ChatMessage } from './ChatMessage'

interface ChatMessagesProps {
  messages: Message[]
  loading: boolean
  loadingMessage: string
  error: string | null
  messagesEndRef: React.RefObject<HTMLDivElement>
}

export function ChatMessages({
  messages,
  loading,
  loadingMessage,
  error,
  messagesEndRef,
}: ChatMessagesProps) {
  return (
    <div className="chat-messages">
      {messages.length === 0 && <EmptyState />}
      {error && <ErrorMessage error={error} />}
      {messages.map((message, index) => (
        <ChatMessage key={index} message={message} />
      ))}
      {loading && <LoadingIndicator message={loadingMessage} />}
      <div ref={messagesEndRef} />
    </div>
  )
}

