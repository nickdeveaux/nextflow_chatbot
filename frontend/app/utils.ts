import { Message } from './types'

export function downloadChatHistory(messages: Message[], sessionId: string | null) {
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

