import React, { useState } from 'react'
import { Input, Box, Text } from '@chakra-ui/react'
import { v4 as uuid } from 'uuid'
import { useCreateTodo } from '@/hooks/queries/useCreateTodo'
import { useAppToast } from '@/hooks/useToast'

const MAX_TITLE_LENGTH = 255

export const TodoForm = () => {
  const [item, setItem] = useState("")
  const [error, setError] = useState("")
  const createTodo = useCreateTodo()
  const { showToast } = useAppToast()

  const validateTitle = (value: string): string | null => {
    const trimmed = value.trim()

    if (!trimmed) {
      return "Todo title cannot be empty"
    }

    if (trimmed.length > MAX_TITLE_LENGTH) {
      return `Todo title cannot exceed ${MAX_TITLE_LENGTH} characters`
    }

    return null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setItem(value)

    // Clear error when user starts typing
    if (error) {
      setError("")
    }
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const validationError = validateTitle(item)
    if (validationError) {
      setError(validationError)
      return
    }

    const todoData = {
      id: uuid(),
      title: item.trim(),
      description: "not implemented yet",
    }

    createTodo.mutate(todoData, {
      onSuccess: () => {
        setItem("")
        setError("")
        showToast({
          title: 'Todo created',
          description: 'Your todo has been added successfully',
          status: 'success',
        })
      },
      onError: (error) => {
        showToast({
          title: 'Failed to create todo',
          description: error instanceof Error ? error.message : 'An error occurred',
          status: 'error',
          onRetry: () => createTodo.mutate(todoData),
        })
      },
    })
  }

  const remainingChars = MAX_TITLE_LENGTH - item.length
  const isNearLimit = remainingChars < 50

  return (
    <Box>
      <form onSubmit={handleSubmit}>
        <Input
          value={item}
          type="text"
          placeholder="Add a todo item"
          aria-label="Add a todo item"
          onChange={handleChange}
          disabled={createTodo.isPending}
          borderColor={error ? "red.500" : undefined}
          maxLength={MAX_TITLE_LENGTH}
        />
      </form>
      {error && (
        <Text color="red.500" fontSize="sm" mt={1}>
          {error}
        </Text>
      )}
      {isNearLimit && !error && item.length > 0 && (
        <Text color="gray.500" fontSize="sm" mt={1}>
          {remainingChars} characters remaining
        </Text>
      )}
    </Box>
  )
}
