import { useState, useEffect } from 'react'
import { API_URL } from '../../config'

export function useBackendHealth() {
  const [backendAvailable, setBackendAvailable] = useState(true)

  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 3000) // 3 second timeout
        
        const response = await fetch(`${API_URL}/health`, {
          method: 'GET',
          signal: controller.signal,
        })
        
        clearTimeout(timeoutId)
        setBackendAvailable(response.ok)
      } catch (err) {
        setBackendAvailable(false)
      }
    }

    // Check immediately
    checkBackendHealth()

    // Then check every 5 seconds
    const interval = setInterval(checkBackendHealth, 5000)

    return () => clearInterval(interval)
  }, [])

  return { backendAvailable, setBackendAvailable }
}

