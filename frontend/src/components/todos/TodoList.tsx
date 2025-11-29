import { Container, Stack } from '@chakra-ui/react'
import { useTodoList } from '@/hooks/queries/useTodoList'
import { TodoForm } from './TodoForm'
import { TodoItem } from './TodoItem'

export const TodoList = () => {
  const { data, isLoading, error } = useTodoList(10, 1)

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading todos</div>

  const todos = data?.todo_entries || []

  return (
    <Container maxW="container.xl" pt="100px">
      <TodoForm />
      <Stack gap={5}>
        {todos.map((todo) => (
          <TodoItem
            key={todo.id}
            id={todo.id}
            title={todo.title}
          />
        ))}
      </Stack>
    </Container>
  )
}
