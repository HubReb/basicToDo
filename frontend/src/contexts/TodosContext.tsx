import React, { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { todoApi } from '../services/api/todoApi'
import { ApiClientError } from '../services/api/client'
import type { Todo } from '../types/todo'

interface TodoContextType {
  todos: Todo[]
  fetchTodos: (page?: number, limit?: number) => void
  total: number
  setPage: React.Dispatch<React.SetStateAction<number>>
  page: number
  limit: number
}

export const TodosContext = createContext<TodoContextType | undefined>(undefined)

export const useTodos = () => {
  const context = useContext(TodosContext)
  if (!context) {
    throw new Error('useTodos must be used within a TodosProvider')
  }
  return context
}

export const TodosProvider = ({ children }: { children: ReactNode }) => {
  const [todos, setTodos] = useState<Todo[]>([])
  const [page, setPage] = useState(1)
  const [limit] = useState(10)
  const [total, setTotal] = useState(0)

  const fetchTodos = useCallback(async (currentPage = page, currentLimit = limit) => {
    try {
      const result = await todoApi.list(currentLimit, currentPage)
      if (Array.isArray(result.todo_entries)) {
        setTodos(result.todo_entries)
      }
      setTotal(result.results || 0)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error("Error fetching todos:", error.detail)
      } else {
        console.error("Error fetching todos:", error)
      }
      setTodos([])
    }
  }, [page, limit])

  return (
    <TodosContext.Provider value={{ todos, fetchTodos, total, setPage, page, limit }}>
      {children}
    </TodosContext.Provider>
  )
}
