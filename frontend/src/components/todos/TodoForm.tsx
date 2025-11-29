import React, { useState } from 'react'
import { Input } from '@chakra-ui/react'
import { v4 as uuid } from 'uuid'
import { useCreateTodo } from '@/hooks/queries/useCreateTodo'
import { useAppToast } from '@/hooks/useToast'

export const TodoForm = () => {
  const [item, setItem] = useState("")
  const createTodo = useCreateTodo()
  const { showToast } = useAppToast()

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!item.trim()) return

    const todoData = {
      id: uuid(),
      title: item.trim(),
      description: "not implemented yet",
    }

    createTodo.mutate(todoData, {
      onSuccess: () => {
        setItem("")
        showToast({
          title: 'Todo created',
          description: 'Your todo has been added successfully',
          status: 'success',
        })
      },
      onError: (error) => {
        showToast({
          title: 'Failed to create todo',
          description: error instanceof Error ? error.message : 'An error occurred',
          status: 'error',
          onRetry: () => createTodo.mutate(todoData),
        })
      },
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <Input
        value={item}
        type="text"
        placeholder="Add a todo item"
        aria-label="Add a todo item"
        onChange={(e) => setItem(e.target.value)}
        disabled={createTodo.isPending}
      />
    </form>
  )
}
