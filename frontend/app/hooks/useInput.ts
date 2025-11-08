import { useState, useRef, useEffect } from 'react'
import { MAX_INPUT_LENGTH } from '../../config'

export function useInput() {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const charCount = input.length
  const isNearLimit = charCount > MAX_INPUT_LENGTH * 0.9
  const remainingChars = MAX_INPUT_LENGTH - charCount

  return {
    input,
    setInput,
    textareaRef,
    charCount,
    isNearLimit,
    remainingChars,
  }
}

