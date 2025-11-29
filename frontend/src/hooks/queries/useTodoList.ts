import { useQuery } from '@tanstack/react-query'
import { todoApi } from '@/services/api/todoApi'

export const useTodoList = (limit: number = 10, page: number = 1) => {
  return useQuery({
    queryKey: ['todos', { limit, page }],
    queryFn: () => todoApi.list(limit, page),
  })
}
