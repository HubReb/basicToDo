import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import type { TodoCreateRequest, TodoListResponse, Todo } from '@/types/todo'

export const useCreateTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TodoCreateRequest) => todoApi.create(data),
    onMutate: async (newTodo) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['todos'] })

      // Snapshot previous value
      const previousTodos = queryClient.getQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }])

      // Optimistically update to the new value
      queryClient.setQueryData<TodoListResponse>(['todos', { limit: 10, page: 1 }], (old) => {
        if (!old) return old

        const optimisticTodo: Todo = {
          id: newTodo.id,
          title: newTodo.title,
          description: newTodo.description || null,
          created_at: new Date().toISOString(),
          updated_at: null,
          deleted: false,
          done: false,
        }

        return {
          ...old,
          todo_entries: [optimisticTodo, ...old.todo_entries],
          results: old.results + 1,
        }
      })

      // Return context with snapshot
      return { previousTodos }
    },
    onError: (_err, _newTodo, context) => {
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
