import { useState } from 'react'
import { Accordion, Box, Button, Container, Flex, Stack, Text } from '@chakra-ui/react'
import { useTodoList } from '@/hooks/queries/useTodoList'
import { useDeletedTodoList } from '@/hooks/queries/useDeletedTodoList'
import { TodoForm } from './TodoForm'
import { TodoItem } from './TodoItem'
import { TodoRestoreButton } from './TodoRestoreButton'
import { Pagination } from '../common/Pagination'
import { Spinner } from '../common/Spinner'
import { ErrorMessage } from '../errors/ErrorMessage'

const LIMIT = 10

export const TodoList = () => {
  const [page, setPage] = useState(1)
  const { data, isLoading, error, refetch } = useTodoList(LIMIT, page)
  const { data: deletedData } = useDeletedTodoList(LIMIT, 1)

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
  const totalCount = data?.total_count ?? 0
  const deletedTodos = deletedData?.todo_entries || []

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
              description={todo.description}
              done={todo.done}
            />
          ))}
        </Stack>
      )}
      <Pagination
        page={page}
        totalCount={totalCount}
        limit={LIMIT}
        onNext={() => setPage((p) => p + 1)}
        onPrev={() => setPage((p) => p - 1)}
      />
      {deletedTodos.length > 0 && (
        <Accordion.Root mt={8} collapsible>
          <Accordion.Item value="deleted">
            <Accordion.ItemTrigger>
              <Text fontWeight="medium">Deleted todos ({deletedTodos.length})</Text>
            </Accordion.ItemTrigger>
            <Accordion.ItemContent>
              <Stack gap={2} mt={2}>
                {deletedTodos.map((todo) => (
                  <Flex key={todo.id} justify="space-between" align="center" p={2} borderWidth="1px" borderRadius="md">
                    <Text textDecoration="line-through" opacity={0.6}>{todo.title}</Text>
                    <TodoRestoreButton id={todo.id} />
                  </Flex>
                ))}
              </Stack>
            </Accordion.ItemContent>
          </Accordion.Item>
        </Accordion.Root>
      )}
    </Container>
  )
}
