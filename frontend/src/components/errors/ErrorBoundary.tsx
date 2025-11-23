import React, { Component, type ReactNode } from 'react'
import { Box, Button, Container, Heading, Text } from '@chakra-ui/react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Container maxW="container.md" pt="100px">
          <Box textAlign="center" p={8}>
            <Heading size="lg" mb={4}>Something went wrong</Heading>
            <Text mb={4} color="gray.600">
              {this.state.error?.message || 'An unexpected error occurred'}
            </Text>
            <Button onClick={this.handleReset} colorScheme="blue">
              Try Again
            </Button>
          </Box>
        </Container>
      )
    }

    return this.props.children
  }
}
