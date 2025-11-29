import { render, screen } from '@testing-library/react'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { ErrorMessage } from '../ErrorMessage'
import { describe, it, expect } from 'vitest'

const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider value={defaultSystem}>
      {component}
    </ChakraProvider>
  )
}

describe('ErrorMessage', () => {
  it('displays error message', () => {
    renderWithChakra(<ErrorMessage message="Test error" />)
    expect(screen.getByText('Test error')).toBeInTheDocument()
  })

  it('renders with proper styling', () => {
    const { container } = renderWithChakra(<ErrorMessage message="Test error" />)
    const box = container.firstChild
    expect(box).toBeInTheDocument()
  })
})
