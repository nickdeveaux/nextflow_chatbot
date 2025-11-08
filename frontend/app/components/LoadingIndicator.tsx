interface LoadingIndicatorProps {
  message: string
}

export function LoadingIndicator({ message }: LoadingIndicatorProps) {
  return (
    <div className="message assistant">
      <div className="message-content">
        <div className="loading">
          <span>{message}</span>
          <div className="loading-dots">
            <span className="loading-dot"></span>
            <span className="loading-dot"></span>
            <span className="loading-dot"></span>
          </div>
        </div>
      </div>
    </div>
  )
}

