import { useQuery } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'

export const useDeletedTodoList = (limit: number = 10, page: number = 1) => {
  return useQuery({
    queryKey: ['todos', 'deleted', { limit, page }],
    queryFn: () => todoApi.listDeleted(limit, page),
  })
}
