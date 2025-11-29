import { useState } from 'react'
import { Box, Button, Flex, Input, Text } from '@chakra-ui/react'
import { useUpdateTodo } from '@/hooks/queries/useUpdateTodo'
import { useAppToast } from '@/hooks/useToast'

const MAX_TITLE_LENGTH = 255

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

    if (trimmed.length > MAX_TITLE_LENGTH) {
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

    const updateData = { id, data: { title: title.trim(), description: "not implemented yet" } }

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

  const remainingChars = MAX_TITLE_LENGTH - title.length
  const isNearLimit = remainingChars < 50

  return (
    <Box mt={2} p={2} borderWidth="1px" borderRadius="md">
      <Input
        value={title}
        onChange={handleChange}
        placeholder="Edit todo"
        borderColor={error ? "red.500" : undefined}
        maxLength={MAX_TITLE_LENGTH}
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
