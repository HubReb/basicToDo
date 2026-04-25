import { useState, useCallback } from 'react'

export const MAX_TITLE_LENGTH = 255
export const MAX_DESCRIPTION_LENGTH = 255

export const useTodoValidation = () => {
  const [error, setError] = useState("")

  const validateTitle = useCallback((value: string): string | null => {
    const trimmed = value.trim()

    if (!trimmed) {
      return "Todo title cannot be empty"
    }

    if (trimmed.length > MAX_TITLE_LENGTH) {
      return `Todo title cannot exceed ${MAX_TITLE_LENGTH} characters`
    }

    return null
  }, [])

  const validateDescription = useCallback((value: string): string | null => {
    if (value.length > MAX_DESCRIPTION_LENGTH) {
      return `Description cannot exceed ${MAX_DESCRIPTION_LENGTH} characters`
    }

    return null
  }, [])

  const clearError = useCallback(() => {
    setError("")
  }, [])

  return { validateTitle, validateDescription, error, setError, clearError }
}
