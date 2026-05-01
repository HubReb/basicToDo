import { useState } from 'react'

const MAX_TITLE_LENGTH = 255

interface TodoValidation {
  validateTitle: (value: string) => string | null
  validateDescription: (value: string | null | undefined) => string | null
  error: string
  setError: (error: string) => void
  clearError: () => void
}

export const useTodoValidation = (): TodoValidation => {
  const [error, setError] = useState('')

  const validateTitle = (value: string): string | null => {
    const trimmed = value.trim()

    if (!trimmed) {
      return 'Todo title cannot be empty'
    }

    if (trimmed.length > MAX_TITLE_LENGTH) {
      return `Todo title cannot exceed ${MAX_TITLE_LENGTH} characters`
    }

    return null
  }

  const validateDescription = (_value: string | null | undefined): string | null => {
    return null
  }

  const clearError = () => setError('')

  return { validateTitle, validateDescription, error, setError, clearError }
}
