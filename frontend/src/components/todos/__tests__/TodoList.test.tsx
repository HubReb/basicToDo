import { render, screen, waitFor } from '@testing-library/react'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TodoList } from '../TodoList'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as todoApi from '@/services/api/todoApi'

vi.mock('@/services/api/todoApi', () => ({
  todoApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithProviders = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={testQueryClient}>
      <ChakraProvider value={defaultSystem}>
        {component}
      </ChakraProvider>
    </QueryClientProvider>
  )
}

describe('TodoList', () => {
  beforeEach(() => {
    vi.mocked(todoApi.todoApi.list).mockResolvedValue({
      success: true,
      todo_entries: [],
      results: 0,
    })
  })

  it('renders todo form', async () => {
    renderWithProviders(<TodoList />)
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Add a todo item')).toBeInTheDocument()
    })
  })

  it('renders without errors', async () => {
    renderWithProviders(<TodoList />)
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Add a todo item')).toBeInTheDocument()
    })
  })
})
