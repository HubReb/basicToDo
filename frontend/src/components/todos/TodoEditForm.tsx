import { useState } from 'react'
import { Box, Button, Flex, Input, Text } from '@chakra-ui/react'
import { useUpdateTodo } from '@/hooks/queries/useUpdateTodo'
import { useAppToast } from '@/hooks/useToast'
import { MAX_TITLE_LENGTH, codePointLength } from '@/lib/titleLength'

interface TodoEditFormProps {
  id: string
  initialTitle: string
  onCancel: () => void
}

export const TodoEditForm = ({ id, initialTitle, onCancel }: TodoEditFormProps) => {
  const [title, setTitle] = useState(initialTitle)
  const [error, setError] = useState("")
  const updateTodo = useUpdateTodo()
  const { showToast } = useAppToast()

  const validateTitle = (value: string): string | null => {
    const trimmed = value.trim()

    if (!trimmed) {
      return "Todo title cannot be empty"
    }

    if (codePointLength(trimmed) > MAX_TITLE_LENGTH) {
      return `Todo title cannot exceed ${MAX_TITLE_LENGTH} characters`
    }

    return null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setTitle(value)

    // Clear error when user starts typing
    if (error) {
      setError("")
    }
  }

  const handleUpdate = () => {
    const validationError = validateTitle(title)
    if (validationError) {
      setError(validationError)
      return
    }

    // Only the title: a description left out keeps the stored one (Q6.7).
    const updateData = { id, data: { title: title.trim() } }

    updateTodo.mutate(updateData, {
      onSuccess: () => {
        onCancel()
        showToast({
          title: 'Todo updated',
          description: 'Your todo has been updated successfully',
          status: 'success',
        })
      },
      onError: (error) => {
        showToast({
          title: 'Failed to update todo',
          description: error instanceof Error ? error.message : 'An error occurred',
          status: 'error',
          onRetry: () => updateTodo.mutate(updateData),
        })
      },
    })
  }

  // No maxLength on the input: it counts UTF-16 code units, not code points (Q6.2).
  const remainingChars = MAX_TITLE_LENGTH - codePointLength(title)
  const isNearLimit = remainingChars < 50

  return (
    <Box mt={2} p={2} borderWidth="1px" borderRadius="md">
      <Input
        value={title}
        onChange={handleChange}
        placeholder="Edit todo"
        borderColor={error ? "red.500" : undefined}
      />
      {error && (
        <Text color="red.500" fontSize="sm" mt={1}>
          {error}
        </Text>
      )}
      {isNearLimit && !error && title.length > 0 && (
        <Text color="gray.500" fontSize="sm" mt={1}>
          {remainingChars} characters remaining
        </Text>
      )}
      <Flex gap={2} mt={2}>
        <Button
          size="sm"
          onClick={handleUpdate}
          colorScheme="blue"
          loading={updateTodo.isPending}
          disabled={!!error}
        >
          Save
        </Button>
        <Button size="sm" onClick={onCancel} variant="outline">
          Cancel
        </Button>
      </Flex>
    </Box>
  )
}
