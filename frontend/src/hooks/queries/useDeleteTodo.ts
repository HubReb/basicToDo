import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'

export const useDeleteTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => todoApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })
}
