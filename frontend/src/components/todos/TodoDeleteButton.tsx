import { Button } from '@chakra-ui/react'
import { useDeleteTodo } from '@/hooks/queries/useDeleteTodo'
import { useAppToast } from '@/hooks/useToast'

interface TodoDeleteButtonProps {
  id: string
}

export const TodoDeleteButton = ({ id }: TodoDeleteButtonProps) => {
  const deleteTodo = useDeleteTodo()
  const { showToast } = useAppToast()

  const handleDelete = () => {
    if (window.confirm("Do you really want to delete this item?")) {
      // Show toast immediately before mutation
      showToast({
        title: 'Todo deleted',
        description: 'Your todo has been deleted successfully',
        status: 'success',
      })

      deleteTodo.mutate(id, {
        onError: (error) => {
          showToast({
            title: 'Failed to delete todo',
            description: error instanceof Error ? error.message : 'An error occurred',
            status: 'error',
            onRetry: () => deleteTodo.mutate(id),
          })
        },
      })
    }
  }

  return (
    <Button
      size="sm"
      marginLeft={2}
      onClick={handleDelete}
      colorScheme="red"
      loading={deleteTodo.isPending}
    >
      Delete Todo
    </Button>
  )
}
