import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import type { TodoUpdateRequest, TodoListResponse } from '@/types/todo'

export const useUpdateTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TodoUpdateRequest }) =>
      todoApi.update(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['todos'] })

      // Snapshot previous value
      const previousTodos = queryClient.getQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }])

      // Optimistically update to the new value
      queryClient.setQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }], (old) => {
        if (!old) return old

        return {
          ...old,
          todo_entries: old.todo_entries.map((todo) =>
            todo.id === id
              ? {
                  ...todo,
                  ...data,
                  updated_at: new Date().toISOString(),
                }
              : todo
          ),
        }
      })

      // Return context with snapshot
      return { previousTodos }
    },
    onError: (_err, _variables, context) => {
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
