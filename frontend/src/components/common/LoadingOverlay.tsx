import { Box, Spinner } from '@chakra-ui/react'

export const LoadingOverlay = () => {
  return (
    <Box
      position="fixed"
      top={0}
      left={0}
      right={0}
      bottom={0}
      bg="blackAlpha.300"
      display="flex"
      alignItems="center"
      justifyContent="center"
      zIndex={9999}
    >
      <Spinner size="xl" color="white" />
    </Box>
  )
}
