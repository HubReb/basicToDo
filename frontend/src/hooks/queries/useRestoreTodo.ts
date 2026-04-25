import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import type { TodoListResponse } from '@/types/todo'

export const useRestoreTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => todoApi.restore(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['deletedTodos'] })

      const previousDeleted = queryClient.getQueryData<TodoListResponse>([
        'deletedTodos',
        { limit: 10, page: 1 },
      ])

      queryClient.setQueryData<TodoListResponse>(
        ['deletedTodos', { limit: 10, page: 1 }],
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

      return { previousDeleted }
    },
    onError: (_err, _id, context) => {
      if (context?.previousDeleted) {
        queryClient.setQueryData(
          ['deletedTodos', { limit: 10, page: 1 }],
          context.previousDeleted
        )
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
      queryClient.invalidateQueries({ queryKey: ['deletedTodos'] })
    },
  })
}
