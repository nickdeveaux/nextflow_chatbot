import { MAX_INPUT_LENGTH } from '../../config'

interface ChatInputProps {
  input: string
  setInput: (value: string) => void
  textareaRef: React.RefObject<HTMLTextAreaElement>
  charCount: number
  isNearLimit: boolean
  remainingChars: number
  loading: boolean
  backendAvailable: boolean
  onSend: () => void
  onKeyPress: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void
}

export function ChatInput({
  input,
  setInput,
  textareaRef,
  charCount,
  isNearLimit,
  remainingChars,
  loading,
  backendAvailable,
  onSend,
  onKeyPress,
}: ChatInputProps) {
  return (
    <div className="chat-input-container">
      <div className="chat-input-wrapper">
        <div className="chat-input-row">
          <textarea
            ref={textareaRef}
            className={`chat-input ${isNearLimit ? 'input-near-limit' : ''}`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={onKeyPress}
            placeholder={backendAvailable ? "Type your message..." : "Backend unavailable..."}
            rows={1}
            disabled={loading || !backendAvailable}
            maxLength={MAX_INPUT_LENGTH}
          />
          <button
            className="send-button"
            onClick={onSend}
            disabled={loading || !input.trim() || !backendAvailable}
          >
            Ask
          </button>
        </div>
        {charCount > 1000 && (
          <div className="input-footer">
            <div className={`char-counter ${isNearLimit ? 'char-counter-warning' : ''}`}>
              {isNearLimit ? (
                <span className="char-counter-warning-text">
                  {charCount.toLocaleString()} / {MAX_INPUT_LENGTH.toLocaleString()} ({remainingChars.toLocaleString()} remaining)
                </span>
              ) : (
                <span className="char-counter-normal">
                  {charCount.toLocaleString()} / {MAX_INPUT_LENGTH.toLocaleString()}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

