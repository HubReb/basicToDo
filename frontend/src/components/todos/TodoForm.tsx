import React, { useState } from 'react'
import { Input, Box, Text, Textarea } from '@chakra-ui/react'
import { v4 as uuid } from 'uuid'
import { useCreateTodo } from '@/hooks/queries/useCreateTodo'
import { useAppToast } from '@/hooks/useToast'
import { useTodoValidation } from '@/hooks/useTodoValidation'

const MAX_TITLE_LENGTH = 255

export const TodoForm = () => {
  const [item, setItem] = useState("")
  const [description, setDescription] = useState("")
  const { validateTitle, error, setError, clearError } = useTodoValidation()
  const createTodo = useCreateTodo()
  const { showToast } = useAppToast()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setItem(value)

    if (error) {
      clearError()
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
      description: description.trim() || null,
    }

    createTodo.mutate(todoData, {
      onSuccess: () => {
        setItem("")
        setDescription("")
        clearError()
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
        <Textarea
          value={description}
          placeholder="Description (optional)"
          aria-label="Todo description"
          onChange={(e) => setDescription(e.target.value)}
          disabled={createTodo.isPending}
          mt={2}
          size="sm"
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
