import { Container, Stack, Text, Button, Box } from '@chakra-ui/react'
import { useTodoList } from '@/hooks/queries/useTodoList'
import { TodoForm } from './TodoForm'
import { TodoItem } from './TodoItem'
import { Spinner } from '../common/Spinner'
import { ErrorMessage } from '../errors/ErrorMessage'

export const TodoList = () => {
  const { data, isLoading, error, refetch } = useTodoList(10, 1)

  if (isLoading) return <Spinner />

  if (error) {
    return (
      <Container maxW="container.xl" pt="100px">
        <Box mt={4}>
          <ErrorMessage message={error instanceof Error ? error.message : 'Failed to load todos'} />
          <Button mt={4} onClick={() => refetch()} colorScheme="blue">
            Retry
          </Button>
        </Box>
      </Container>
    )
  }

  const todos = data?.todo_entries || []

  return (
    <Container maxW="container.xl" pt="100px">
      <TodoForm />
      {todos.length === 0 ? (
        <Text textAlign="center" color="gray.500" mt={8}>
          No todos yet. Add one above!
        </Text>
      ) : (
        <Stack gap={5}>
          {todos.map((todo) => (
            <TodoItem
              key={todo.id}
              id={todo.id}
              title={todo.title}
            />
          ))}
        </Stack>
      )}
    </Container>
  )
}
