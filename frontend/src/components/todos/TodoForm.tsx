import React, { useState } from 'react'
import { Input } from '@chakra-ui/react'
import { v4 as uuid } from 'uuid'
import { todoApi } from '../../services/api/todoApi'
import { ApiClientError } from '../../services/api/client'

interface TodoFormProps {
  onSuccess: () => void
}

export const TodoForm = ({ onSuccess }: TodoFormProps) => {
  const [item, setItem] = useState("")

  const handleInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    setItem(event.target.value)
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!item.trim()) return

    try {
      await todoApi.create({
        id: uuid(),
        title: item.trim(),
        description: "not implemented yet",
      })

      await onSuccess()
      setItem("")
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error("Error adding todo:", error.detail)
      } else {
        console.error("Error adding todo:", error)
      }
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Input
        value={item}
        pr="4.5rem"
        type="text"
        placeholder="Add a todo item"
        aria-label="Add a todo item"
        onChange={handleInput}
      />
    </form>
  )
}
