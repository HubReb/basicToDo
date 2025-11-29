import { render } from '@testing-library/react'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'
import { Spinner } from '../Spinner'
import { describe, it, expect } from 'vitest'

const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider value={defaultSystem}>
      {component}
    </ChakraProvider>
  )
}

describe('Spinner', () => {
  it('renders spinner', () => {
    const { container } = renderWithChakra(<Spinner />)
    const spinner = container.querySelector('.chakra-spinner')
    expect(spinner).toBeInTheDocument()
  })

  it('renders with custom size', () => {
    const { container } = renderWithChakra(<Spinner size="sm" />)
    const spinner = container.querySelector('.chakra-spinner')
    expect(spinner).toBeInTheDocument()
  })
})
