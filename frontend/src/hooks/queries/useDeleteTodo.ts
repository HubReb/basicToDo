import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import type { TodoListResponse } from '@/types/todo'

export const useDeleteTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
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
        }
      })

      // Return context with snapshot
      return { previousTodos }
    },
    onError: (_err, _id, context) => {
      // Rollback to previous value on error
      if (context?.previousTodos) {
        queryClient.setQueryData(['todos', { limit: 10, page: 1 }], context.previousTodos)
      }
    },
    onSettled: () => {
      // Refetch to sync with server
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })
}
