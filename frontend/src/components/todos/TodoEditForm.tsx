import { useState } from 'react'
import { Box, Button, Flex, Input } from '@chakra-ui/react'
import { todoApi } from '../../services/api/todoApi'
import { ApiClientError } from '../../services/api/client'

interface TodoEditFormProps {
  id: string
  initialTitle: string
  onSuccess: () => void
  onCancel: () => void
}

export const TodoEditForm = ({ id, initialTitle, onSuccess, onCancel }: TodoEditFormProps) => {
  const [title, setTitle] = useState(initialTitle)

  const handleUpdate = async () => {
    try {
      await todoApi.update(id, {
        title,
        description: "not implemented yet",
      })
      await onSuccess()
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error("Error updating todo:", error.detail)
      } else {
        console.error("Error updating todo:", error)
      }
    }
  }

  return (
    <Box mt={2} p={2} borderWidth="1px" borderRadius="md">
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Edit todo"
      />
      <Flex gap={2} mt={2}>
        <Button size="sm" onClick={handleUpdate} colorScheme="blue">
          Save
        </Button>
        <Button size="sm" onClick={onCancel} variant="outline">
          Cancel
        </Button>
      </Flex>
    </Box>
  )
}
