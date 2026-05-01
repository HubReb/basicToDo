import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import { useAppToast } from '@/hooks/useToast'
import type { TodoListResponse } from '@/types/todo'

export const useDeleteTodo = () => {
  const queryClient = useQueryClient()
  const { showToast } = useAppToast()

  return useMutation({
    mutationFn: (id: string) => todoApi.delete(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['todos'] })
      const previousTodos = queryClient.getQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }])
      queryClient.setQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }], (old) => {
        if (!old) return old
        return {
          ...old,
          todo_entries: old.todo_entries.filter((todo) => todo.id !== id),
          results: old.results - 1,
        }
      })
      return { previousTodos }
    },
    onSuccess: () => {
      showToast({
        title: 'Todo deleted',
        description: 'Your todo has been deleted successfully',
        status: 'success',
      })
    },
    onError: (error, _id, context) => {
      if (context?.previousTodos) {
        queryClient.setQueryData(['todos', { limit: 10, page: 1 }], context.previousTodos)
      }
      showToast({
        title: 'Failed to delete todo',
        description: error instanceof Error ? error.message : 'An error occurred',
        status: 'error',
      })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })
}
