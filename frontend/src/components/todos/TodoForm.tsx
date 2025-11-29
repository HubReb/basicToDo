import React, { useState } from 'react'
import { Input } from '@chakra-ui/react'
import { v4 as uuid } from 'uuid'
import { useCreateTodo } from '@/hooks/queries/useCreateTodo'

export const TodoForm = () => {
  const [item, setItem] = useState("")
  const createTodo = useCreateTodo()

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!item.trim()) return

    createTodo.mutate({
      id: uuid(),
      title: item.trim(),
      description: "not implemented yet",
    })

    setItem("")
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
