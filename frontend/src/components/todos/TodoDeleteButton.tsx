import { Button } from '@chakra-ui/react'
import { todoApi } from '../../services/api/todoApi'
import { ApiClientError } from '../../services/api/client'

interface TodoDeleteButtonProps {
  id: string
  onSuccess: () => void
}

export const TodoDeleteButton = ({ id, onSuccess }: TodoDeleteButtonProps) => {
  const handleDelete = async () => {
    if (window.confirm("Do you really want to delete this item?")) {
      try {
        await todoApi.delete(id)
        await onSuccess()
      } catch (error) {
        if (error instanceof ApiClientError) {
          console.error("Error deleting todo:", error.detail)
        } else {
          console.error("Error deleting todo:", error)
        }
      }
    }
  }

  return (
    <Button
      size="sm"
      marginLeft={2}
      onClick={handleDelete}
      colorScheme="red"
    >
      Delete Todo
    </Button>
  )
}
