import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { TodoForm } from '../TodoForm'
import { TodoEditForm } from '../TodoEditForm'
import * as todoApi from '@/services/api/todoApi'

vi.mock('@/services/api/todoApi')

const renderWithProviders = (component: React.ReactElement) => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <ChakraProvider value={defaultSystem}>{component}</ChakraProvider>
    </QueryClientProvider>
  )
}

const todo = {
  id: 'a1b2c3d4-0000-4000-8000-000000000001',
  title: 'Buy milk',
  description: null,
  created_at: '2026-10-07T10:00:00Z',
  updated_at: '2026-10-07T10:00:00Z',
  deleted: false,
  done: false,
}

describe('Todo forms send no placeholder description (Q6.7)', () => {
  beforeEach(() => {
    vi.mocked(todoApi.todoApi.create).mockResolvedValue(todo)
    vi.mocked(todoApi.todoApi.update).mockResolvedValue(todo)
  })

  it('creates a todo with only id and title', async () => {
    renderWithProviders(<TodoForm />)
    const input = screen.getByPlaceholderText('Add a todo item')
    fireEvent.change(input, { target: { value: '  Buy milk  ' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => expect(todoApi.todoApi.create).toHaveBeenCalledTimes(1))
    const sent = vi.mocked(todoApi.todoApi.create).mock.calls[0][0]
    expect(Object.keys(sent).sort()).toEqual(['id', 'title'])
    expect(sent.title).toBe('Buy milk')
  })

  it('edits only the title, leaving the stored description alone', async () => {
    renderWithProviders(<TodoEditForm id={todo.id} initialTitle="Buy milk" onCancel={() => {}} />)
    fireEvent.change(screen.getByPlaceholderText('Edit todo'), { target: { value: 'Buy oat milk' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(todoApi.todoApi.update).toHaveBeenCalledTimes(1))
    expect(vi.mocked(todoApi.todoApi.update).mock.calls[0]).toEqual([todo.id, { title: 'Buy oat milk' }])
  })
})

describe('Title length in code points, as the API counts it (Q6.2)', () => {
  // U+1F600: one code point, two UTF-16 code units.
  const emoji = (count: number) => '\u{1F600}'.repeat(count)

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(todoApi.todoApi.create).mockResolvedValue(todo)
    vi.mocked(todoApi.todoApi.update).mockResolvedValue(todo)
  })

  it('sends 255 characters outside the BMP (510 UTF-16 code units)', async () => {
    renderWithProviders(<TodoForm />)
    const input = screen.getByPlaceholderText('Add a todo item')
    fireEvent.change(input, { target: { value: emoji(255) } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => expect(todoApi.todoApi.create).toHaveBeenCalledTimes(1))
    expect(vi.mocked(todoApi.todoApi.create).mock.calls[0][0].title).toBe(emoji(255))
  })

  it('refuses 256 of them without sending', () => {
    renderWithProviders(<TodoForm />)
    const input = screen.getByPlaceholderText('Add a todo item')
    fireEvent.change(input, { target: { value: emoji(256) } })
    fireEvent.submit(input.closest('form')!)

    expect(screen.getByText('Todo title cannot exceed 255 characters')).toBeInTheDocument()
    expect(todoApi.todoApi.create).not.toHaveBeenCalled()
  })

  it('counts the remaining characters in code points', () => {
    renderWithProviders(<TodoForm />)
    fireEvent.change(screen.getByPlaceholderText('Add a todo item'), { target: { value: emoji(250) } })

    expect(screen.getByText('5 characters remaining')).toBeInTheDocument()
  })

  it('edit form: sends 255 and refuses 256', async () => {
    renderWithProviders(<TodoEditForm id={todo.id} initialTitle="Buy milk" onCancel={() => {}} />)
    const input = screen.getByPlaceholderText('Edit todo')

    fireEvent.change(input, { target: { value: emoji(256) } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(screen.getByText('Todo title cannot exceed 255 characters')).toBeInTheDocument()
    expect(todoApi.todoApi.update).not.toHaveBeenCalled()

    fireEvent.change(input, { target: { value: emoji(255) } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(todoApi.todoApi.update).toHaveBeenCalledWith(todo.id, { title: emoji(255) }))
  })

  it('has no maxLength on either input, which would count code units', () => {
    renderWithProviders(
      <>
        <TodoForm />
        <TodoEditForm id={todo.id} initialTitle="Buy milk" onCancel={() => {}} />
      </>
    )

    expect(screen.getByPlaceholderText('Add a todo item')).not.toHaveAttribute('maxlength')
    expect(screen.getByPlaceholderText('Edit todo')).not.toHaveAttribute('maxlength')
  })
})
