import { render, screen } from '@testing-library/react'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { ErrorBoundary } from '../ErrorBoundary'
import { describe, it, expect, vi } from 'vitest'

const ThrowError = () => {
  throw new Error('Test error')
}

const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider value={defaultSystem}>
      {component}
    </ChakraProvider>
  )
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    renderWithChakra(
      <ErrorBoundary>
        <div>Content</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders error UI when error occurs', () => {
    // Suppress console.error for this test
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

    renderWithChakra(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument()
    expect(screen.getByText('Test error')).toBeInTheDocument()

    spy.mockRestore()
  })

  it('renders custom fallback when provided', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

    renderWithChakra(
      <ErrorBoundary fallback={<div>Custom Fallback</div>}>
        <ThrowError />
      </ErrorBoundary>
    )
    expect(screen.getByText('Custom Fallback')).toBeInTheDocument()

    spy.mockRestore()
  })
})
