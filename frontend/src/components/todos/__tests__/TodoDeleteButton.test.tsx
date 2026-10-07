import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TodoDeleteButton } from '../TodoDeleteButton'
import * as todoApi from '@/services/api/todoApi'
import { ApiClientError } from '@/services/api/client'
import { toaster } from '@/lib/toaster'
import type { DeleteTodoResponse } from '@/types/todo'

vi.mock('@/services/api/todoApi')
vi.mock('@/lib/toaster', () => ({ toaster: { create: vi.fn() } }))

const ID = 'a1b2c3d4-0000-4000-8000-000000000001'

const renderButton = () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <ChakraProvider value={defaultSystem}>
        <TodoDeleteButton id={ID} />
      </ChakraProvider>
    </QueryClientProvider>
  )
}

const pending = () => {
  const handle: {
    resolve: (value: DeleteTodoResponse) => void
    reject: (error: Error) => void
  } = { resolve: () => {}, reject: () => {} }
  const promise = new Promise<DeleteTodoResponse>((resolve, reject) => {
    handle.resolve = resolve
    handle.reject = reject
  })
  return { promise, ...handle }
}

describe('Delete toasts follow the server (Q6.9)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  it('shows "Todo deleted" only after the server confirms', async () => {
    const answer = pending()
    vi.mocked(todoApi.todoApi.delete).mockReturnValue(answer.promise)
    renderButton()

    fireEvent.click(screen.getByText('Delete Todo'))
    await waitFor(() => expect(todoApi.todoApi.delete).toHaveBeenCalledWith(ID))
    expect(toaster.create).not.toHaveBeenCalled()

    answer.resolve({ success: true, message: 'Deleted successfully' })

    await waitFor(() =>
      expect(toaster.create).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Todo deleted', type: 'success' })
      )
    )
    expect(toaster.create).toHaveBeenCalledTimes(1)
  })

  it('shows a failure, even after the button has gone', async () => {
    const answer = pending()
    vi.mocked(todoApi.todoApi.delete).mockReturnValue(answer.promise)
    const { unmount } = renderButton()

    fireEvent.click(screen.getByText('Delete Todo'))
    await waitFor(() => expect(todoApi.todoApi.delete).toHaveBeenCalledTimes(1))
    // The optimistic update removes the row, and with it the button.
    unmount()
    answer.reject(new ApiClientError(500, 'Internal Server Error', 'Internal error'))

    await waitFor(() =>
      expect(toaster.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Failed to delete todo',
          description: 'API Error 500: Internal error',
          type: 'error',
        })
      )
    )
    expect(toaster.create).toHaveBeenCalledTimes(1)
  })

  it('retries from the failure toast', async () => {
    vi.mocked(todoApi.todoApi.delete)
      .mockRejectedValueOnce(new ApiClientError(500, 'Internal Server Error', 'Internal error'))
      .mockResolvedValueOnce({ success: true, message: 'Deleted successfully' })
    renderButton()

    fireEvent.click(screen.getByText('Delete Todo'))
    await waitFor(() => expect(toaster.create).toHaveBeenCalledTimes(1))
    const failure = vi.mocked(toaster.create).mock.calls[0][0]
    expect(failure.action?.label).toBe('Retry')
    failure.action?.onClick?.()

    await waitFor(() =>
      expect(toaster.create).toHaveBeenLastCalledWith(expect.objectContaining({ title: 'Todo deleted' }))
    )
    expect(todoApi.todoApi.delete).toHaveBeenCalledTimes(2)
  })

  it('does nothing when the prompt is declined', () => {
    vi.mocked(window.confirm).mockReturnValue(false)
    renderButton()

    fireEvent.click(screen.getByText('Delete Todo'))

    expect(todoApi.todoApi.delete).not.toHaveBeenCalled()
    expect(toaster.create).not.toHaveBeenCalled()
  })
})
