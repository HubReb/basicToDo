import { useState } from 'react'
import { Box, Button, Flex, Input } from '@chakra-ui/react'
import { useUpdateTodo } from '@/hooks/queries/useUpdateTodo'
import { useAppToast } from '@/hooks/useToast'

interface TodoEditFormProps {
  id: string
  initialTitle: string
  onCancel: () => void
}

export const TodoEditForm = ({ id, initialTitle, onCancel }: TodoEditFormProps) => {
  const [title, setTitle] = useState(initialTitle)
  const updateTodo = useUpdateTodo()
  const { showToast } = useAppToast()

  const handleUpdate = () => {
    const updateData = { id, data: { title, description: "not implemented yet" } }

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

  return (
    <Box mt={2} p={2} borderWidth="1px" borderRadius="md">
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Edit todo"
      />
      <Flex gap={2} mt={2}>
        <Button
          size="sm"
          onClick={handleUpdate}
          colorScheme="blue"
          loading={updateTodo.isPending}
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
