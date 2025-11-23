import { useEffect } from 'react'
import { Container, Stack } from '@chakra-ui/react'
import { useTodos } from '../../contexts/TodosContext'
import { TodoForm } from './TodoForm'
import { TodoItem } from './TodoItem'
import type { Todo } from '../../types/todo'

export const TodoList = () => {
  const { todos, fetchTodos, page, limit } = useTodos()

  useEffect(() => {
    if (todos.length === 0) {
      fetchTodos(page, limit)
    }
  }, [page, limit, fetchTodos, todos.length])

  return (
    <Container maxW="container.xl" pt="100px">
      <TodoForm onSuccess={fetchTodos} />
      <Stack gap={5}>
        {todos.map((todo: Todo) => (
          <TodoItem
            key={todo.id}
            id={todo.id}
            title={todo.title}
            onUpdate={fetchTodos}
          />
        ))}
      </Stack>
    </Container>
  )
}
