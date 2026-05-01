import { useState } from 'react'
import { Box, Button, Checkbox, Flex, Text } from '@chakra-ui/react'
import { TodoEditForm } from './TodoEditForm'
import { TodoDeleteButton } from './TodoDeleteButton'
import { useUpdateTodo } from '@/hooks/queries/useUpdateTodo'

interface TodoItemProps {
  id: string
  title: string
  description?: string | null
  done?: boolean
}

export const TodoItem = ({ id, title, description, done = false }: TodoItemProps) => {
  const [isEditing, setIsEditing] = useState(false)
  const updateTodo = useUpdateTodo()

  const handleDoneChange = () => {
    updateTodo.mutate({ id, data: { done: !done } })
  }

  return (
    <Box p={1} shadow="sm">
      <Flex justify="space-between" gap="2rem" rowGap="2rem">
        <Flex align="start" gap={2} flex={1}>
          <Checkbox.Root
            checked={done}
            onCheckedChange={handleDoneChange}
            mt={4}
          >
            <Checkbox.Control />
          </Checkbox.Root>
          <Box mt={4}>
            <Text
              as="span"
              textDecoration={done ? 'line-through' : undefined}
              opacity={done ? 0.6 : 1}
            >
              {title}
            </Text>
            {description && (
              <Text fontSize="sm" color="gray.600" mt={1}>
                {description}
              </Text>
            )}
          </Box>
        </Flex>
        {!isEditing && (
          <Flex align="end" gap="1rem" mt={4}>
            <Button size="sm" onClick={() => setIsEditing(true)}>
              Edit
            </Button>
            <TodoDeleteButton id={id} />
          </Flex>
        )}
      </Flex>
      {isEditing && (
        <TodoEditForm
          id={id}
          initialTitle={title}
          initialDescription={description}
          onCancel={() => setIsEditing(false)}
        />
      )}
    </Box>
  )
}
