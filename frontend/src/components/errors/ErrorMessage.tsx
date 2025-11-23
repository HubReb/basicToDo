import { Box, Text } from '@chakra-ui/react'

interface ErrorMessageProps {
  message: string
}

export const ErrorMessage = ({ message }: ErrorMessageProps) => {
  return (
    <Box p={2} bg="red.50" borderRadius="md" borderWidth="1px" borderColor="red.200">
      <Text color="red.600" fontSize="sm">
        {message}
      </Text>
    </Box>
  )
}
