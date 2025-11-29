import { Spinner as ChakraSpinner, Center } from '@chakra-ui/react'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

export const Spinner = ({ size = 'lg' }: SpinnerProps) => {
  return (
    <Center p={8}>
      <ChakraSpinner size={size} />
    </Center>
  )
}
