import { render, screen, fireEvent } from '@testing-library/react'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TodoItem } from '../TodoItem'
import { describe, it, expect } from 'vitest'

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

describe('TodoItem', () => {
  it('renders todo title', () => {
    renderWithProviders(<TodoItem id="123" title="Test Todo" />)
    expect(screen.getByText('Test Todo')).toBeInTheDocument()
  })

  it('shows edit form when edit clicked', () => {
    renderWithProviders(<TodoItem id="123" title="Test Todo" />)
    fireEvent.click(screen.getByText('Edit'))
    expect(screen.getByPlaceholderText('Edit todo')).toBeInTheDocument()
  })

  it('shows delete button', () => {
    renderWithProviders(<TodoItem id="123" title="Test Todo" />)
    expect(screen.getByText('Delete Todo')).toBeInTheDocument()
  })

  it('hides edit and delete buttons when editing', () => {
    renderWithProviders(<TodoItem id="123" title="Test Todo" />)
    fireEvent.click(screen.getByText('Edit'))
    expect(screen.queryByText('Edit')).not.toBeInTheDocument()
    expect(screen.queryByText('Delete Todo')).not.toBeInTheDocument()
  })
})
