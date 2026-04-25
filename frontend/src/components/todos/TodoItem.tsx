import { useState } from 'react'
import { Box, Button, Checkbox, Flex, Text } from '@chakra-ui/react'
import { TodoEditForm } from './TodoEditForm'
import { TodoDeleteButton } from './TodoDeleteButton'
import { useUpdateTodo } from '@/hooks/queries/useUpdateTodo'

interface TodoItemProps {
  id: string
  title: string
  description?: string | null
  done: boolean
}

export const TodoItem = ({ id, title, description, done }: TodoItemProps) => {
  const [isEditing, setIsEditing] = useState(false)
  const updateTodo = useUpdateTodo()

  const handleToggleDone = () => {
    updateTodo.mutate({ id, data: { done: !done } })
  }

  return (
    <Box p={1} shadow="sm">
      <Flex justify="space-between" gap="2rem" rowGap="2rem">
        <Box mt={4} flex="1">
          <Flex align="center" gap="0.5rem">
            <Checkbox.Root
              checked={done}
              onCheckedChange={handleToggleDone}
              disabled={updateTodo.isPending}
            >
              <Checkbox.HiddenInput />
              <Checkbox.Control />
            </Checkbox.Root>
            <Text textDecoration={done ? 'line-through' : 'none'} color={done ? 'gray.500' : undefined}>
              {title}
            </Text>
          </Flex>
          {description && (
            <Text fontSize="sm" color="gray.500" ml="1.75rem" mt={1}>
              {description}
            </Text>
          )}
          {!isEditing && (
            <Flex align="end" gap="1rem" mt={2}>
              <Button size="sm" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
              <TodoDeleteButton id={id} />
            </Flex>
          )}
        </Box>
      </Flex>
      {isEditing && (
        <TodoEditForm
          id={id}
          initialTitle={title}
          initialDescription={description || ''}
          onCancel={() => setIsEditing(false)}
        />
      )}
    </Box>
  )
}
