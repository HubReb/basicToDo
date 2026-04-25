import { useState } from 'react'
import { Container, Stack, Text, Button, Box, Flex } from '@chakra-ui/react'
import { useTodoList } from '@/hooks/queries/useTodoList'
import { useDeletedTodoList } from '@/hooks/queries/useDeletedTodoList'
import { TodoForm } from './TodoForm'
import { TodoItem } from './TodoItem'
import { TodoRestoreButton } from './TodoRestoreButton'
import { Spinner } from '../common/Spinner'
import { Pagination } from '../common/Pagination'
import { ErrorMessage } from '../errors/ErrorMessage'

const PAGE_SIZE = 10

export const TodoList = () => {
  const [page, setPage] = useState(1)
  const { data, isLoading, error, refetch } = useTodoList(PAGE_SIZE, page)
  const [showDeleted, setShowDeleted] = useState(false)
  const deletedQuery = useDeletedTodoList(PAGE_SIZE, 1)

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
  const totalCount = data?.total_count || 0
  const totalPages = Math.ceil(totalCount / PAGE_SIZE)
  const deletedTodos = deletedQuery.data?.todo_entries || []
  const deletedCount = deletedQuery.data?.total_count || 0

  return (
    <Container maxW="container.xl" pt="100px">
      <TodoForm />
      {todos.length === 0 ? (
        <Text textAlign="center" color="gray.500" mt={8}>
          No todos yet. Add one above!
        </Text>
      ) : (
        <Stack gap={5} mt={4}>
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
        currentPage={page}
        totalPages={totalPages}
        onPageChange={setPage}
      />

      {/* Deleted items section */}
      <Box mt={8} borderTopWidth="1px" pt={4}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowDeleted(!showDeleted)}
          color="gray.500"
        >
          {showDeleted ? '▼' : '▶'} Deleted Items ({deletedCount})
        </Button>
        {showDeleted && (
          <Box mt={2}>
            {deletedQuery.isLoading ? (
              <Spinner size="sm" />
            ) : deletedTodos.length === 0 ? (
              <Text color="gray.500" fontSize="sm" ml={4}>
                No deleted items
              </Text>
            ) : (
              <Stack gap={3} ml={4}>
                {deletedTodos.map((todo) => (
                  <Flex key={todo.id} justify="space-between" align="center" p={2} opacity={0.7}>
                    <Box>
                      <Text textDecoration="line-through">{todo.title}</Text>
                      {todo.description && (
                        <Text fontSize="sm" color="gray.500">
                          {todo.description}
                        </Text>
                      )}
                    </Box>
                    <TodoRestoreButton id={todo.id} />
                  </Flex>
                ))}
              </Stack>
            )}
          </Box>
        )}
      </Box>
    </Container>
  )
}
