interface ChatHeaderProps {
  darkMode: boolean
  onToggleDarkMode: () => void
}

export function ChatHeader({ darkMode, onToggleDarkMode }: ChatHeaderProps) {
  return (
    <div className="header">
      <h1>Nextflow Chat Assistant</h1>
      <button
        className="theme-toggle"
        onClick={onToggleDarkMode}
        aria-label="Toggle dark mode"
      >
        {darkMode ? '☀️' : '🌙'}
      </button>
    </div>
  )
}

