import { useState, useEffect } from 'react'
import { LOADING_MESSAGES } from '../../config'

export function useLoadingMessage(loading: boolean) {
  const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0])

  useEffect(() => {
    if (!loading) {
      // Reset to first message when not loading
      setLoadingMessage(LOADING_MESSAGES[0])
      return
    }

    // Track which indexes we've already used
    const usedIndexes = new Set<number>()
    
    // Get a random unused index
    const getRandomUnusedIndex = (): number => {
      // If we've used all messages, reset
      if (usedIndexes.size >= LOADING_MESSAGES.length) {
        usedIndexes.clear()
      }
      
      // Get available indexes
      const availableIndexes = LOADING_MESSAGES
        .map((_, index) => index)
        .filter(index => !usedIndexes.has(index))
      
      // Randomly select from available
      const randomIndex = availableIndexes[Math.floor(Math.random() * availableIndexes.length)]
      usedIndexes.add(randomIndex)
      
      return randomIndex
    }

    // Start with a random message
    const initialIndex = getRandomUnusedIndex()
    setLoadingMessage(LOADING_MESSAGES[initialIndex])

    // Change message every 2 seconds with random unused selection
    const interval = setInterval(() => {
      const nextIndex = getRandomUnusedIndex()
      setLoadingMessage(LOADING_MESSAGES[nextIndex])
    }, 2000)

    return () => clearInterval(interval)
  }, [loading])

  return loadingMessage
}

