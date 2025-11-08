export interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: string[]
}

export interface CitationRef {
  index: number
  url: string
}

