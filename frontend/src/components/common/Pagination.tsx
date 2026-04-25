import { Button, Flex, Text } from '@chakra-ui/react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export const Pagination = ({ currentPage, totalPages, onPageChange }: PaginationProps) => {
  if (totalPages <= 1) return null

  return (
    <Flex justify="center" align="center" gap={4} mt={6}>
      <Button
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        variant="outline"
      >
        Previous
      </Button>
      <Text fontSize="sm" color="gray.500">
        Page {currentPage} of {totalPages}
      </Text>
      <Button
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        variant="outline"
      >
        Next
      </Button>
    </Flex>
  )
}
