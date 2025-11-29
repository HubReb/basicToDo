import { Button } from '@chakra-ui/react'
import { useDeleteTodo } from '@/hooks/queries/useDeleteTodo'

interface TodoDeleteButtonProps {
  id: string
}

export const TodoDeleteButton = ({ id }: TodoDeleteButtonProps) => {
  const deleteTodo = useDeleteTodo()

  const handleDelete = () => {
    if (window.confirm("Do you really want to delete this item?")) {
      deleteTodo.mutate(id)
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
