import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import type { TodoListResponse } from '@/types/todo'

export const useRestoreTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => todoApi.restore(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['todos'] })

      // Snapshot both caches
      const previousDeleted = queryClient.getQueryData<TodoListResponse>([
        'todos', 'deleted', { limit: 10, page: 1 },
      ])
      const previousActive = queryClient.getQueryData<TodoListResponse>([
        'todos', { limit: 10, page: 1 },
      ])

      // Remove from deleted list
      queryClient.setQueryData<TodoListResponse>(
        ['todos', 'deleted', { limit: 10, page: 1 }],
        (old) => {
          if (!old) return old
          return {
            ...old,
            todo_entries: old.todo_entries.filter((todo) => todo.id !== id),
            results: old.results - 1,
            total_count: old.total_count - 1,
          }
        }
      )

      // Prepend to active list
      const deletedTodo = previousDeleted?.todo_entries.find((t) => t.id === id)
      if (deletedTodo) {
        queryClient.setQueryData<TodoListResponse>(
          ['todos', { limit: 10, page: 1 }],
          (old) => {
            if (!old) return old
            return {
              ...old,
              todo_entries: [{ ...deletedTodo, deleted: false }, ...old.todo_entries],
              results: old.results + 1,
              total_count: old.total_count + 1,
            }
          }
        )
      }

      return { previousDeleted, previousActive }
    },
    onError: (_err, _id, context) => {
      if (context?.previousDeleted) {
        queryClient.setQueryData(
          ['todos', 'deleted', { limit: 10, page: 1 }],
          context.previousDeleted
        )
      }
      if (context?.previousActive) {
        queryClient.setQueryData(
          ['todos', { limit: 10, page: 1 }],
          context.previousActive
        )
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })
}
