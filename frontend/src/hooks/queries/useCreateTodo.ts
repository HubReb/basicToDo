import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'
import type { TodoCreateRequest } from '@/types/todo'

export const useCreateTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TodoCreateRequest) => todoApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })
}
