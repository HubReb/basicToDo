import { useState } from 'react'
import { Box, Button, Flex, Text } from '@chakra-ui/react'
import { TodoEditForm } from './TodoEditForm'
import { TodoDeleteButton } from './TodoDeleteButton'

interface TodoItemProps {
  id: string
  title: string
}

export const TodoItem = ({ id, title }: TodoItemProps) => {
  const [isEditing, setIsEditing] = useState(false)

  return (
    <Box p={1} shadow="sm">
      <Flex justify="space-between" gap="2rem" rowGap="2rem">
        <Text mt={4} as="div">
          {title}
          {!isEditing && (
            <Flex align="end" gap="1rem">
              <Button size="sm" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
              <TodoDeleteButton id={id} />
            </Flex>
          )}
        </Text>
      </Flex>
      {isEditing && (
        <TodoEditForm
          id={id}
          initialTitle={title}
          onCancel={() => setIsEditing(false)}
        />
      )}
    </Box>
  )
}
