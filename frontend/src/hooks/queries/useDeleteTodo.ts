import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import { useAppToast } from '@/hooks/useToast'
import type { TodoListResponse } from '@/types/todo'

export const useDeleteTodo = () => {
  const queryClient = useQueryClient()
  const { showToast } = useAppToast()

  // The toasts live here, not in the button (Q6.9): a mutation's own
  // callbacks also run after the button unmounted, which the optimistic
  // removal of its row makes happen at once.
  const mutation = useMutation({
    mutationFn: (id: string) => todoApi.delete(id),
    onMutate: async (id) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['todos'] })

      // Snapshot previous value
      const previousTodos = queryClient.getQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }])

      // Optimistically update to the new value
      queryClient.setQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }], (old) => {
        if (!old) return old

        return {
          ...old,
          todo_entries: old.todo_entries.filter((todo) => todo.id !== id),
          results: old.results - 1,
          total: old.total - 1,
        }
      })

      // Return context with snapshot
      return { previousTodos }
    },
    onSuccess: () => {
      showToast({
        title: 'Todo deleted',
        description: 'Your todo has been deleted successfully',
        status: 'success',
      })
    },
    onError: (error, id, context) => {
      // Rollback to previous value on error
      if (context?.previousTodos) {
        queryClient.setQueryData(['todos', { limit: 10, page: 1 }], context.previousTodos)
      }
      showToast({
        title: 'Failed to delete todo',
        description: error instanceof Error ? error.message : 'An error occurred',
        status: 'error',
        onRetry: () => mutation.mutate(id),
      })
    },
    onSettled: () => {
      // Refetch to sync with server
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })

  return mutation
}
