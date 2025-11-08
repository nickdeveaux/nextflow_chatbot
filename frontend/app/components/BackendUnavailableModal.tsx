import { Message } from '../types'

interface BackendUnavailableModalProps {
  messages: Message[]
  sessionId: string | null
  onDownloadChatHistory: () => void
}

export function BackendUnavailableModal({
  messages,
  sessionId,
  onDownloadChatHistory,
}: BackendUnavailableModalProps) {
  return (
    <div className="modal-overlay" onClick={() => {}}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-icon">😢</div>
        <h2>Backend Unavailable</h2>
        <p>The backend service is currently unavailable. Please try again later.</p>
        {messages.length > 0 && (
          <>
            <p className="modal-subtext">The chat history can be downloaded for this session.</p>
            <button
              className="modal-download-button"
              onClick={onDownloadChatHistory}
              aria-label="Download chat history"
            >
              📥 Download Chat History
            </button>
          </>
        )}
      </div>
    </div>
  )
}

