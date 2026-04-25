import { Button, Flex } from '@chakra-ui/react'

interface PaginationProps {
  page: number
  totalCount: number
  limit: number
  onNext: () => void
  onPrev: () => void
}

export const Pagination = ({ page, totalCount, limit, onNext, onPrev }: PaginationProps) => {
  const isFirstPage = page === 1
  const isLastPage = page * limit >= totalCount

  return (
    <Flex gap={2} justify="center" mt={4}>
      <Button size="sm" onClick={onPrev} disabled={isFirstPage} variant="outline">
        Previous
      </Button>
      <Button size="sm" onClick={onNext} disabled={isLastPage} variant="outline">
        Next
      </Button>
    </Flex>
  )
}
