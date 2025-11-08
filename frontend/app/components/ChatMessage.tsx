import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Message, CitationRef } from '../types'
import { markdownComponents } from './markdownComponents'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
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
    <div className={`message ${message.role}`}>
      <div className="message-content">
        <div className="markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={markdownComponents}
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
}

