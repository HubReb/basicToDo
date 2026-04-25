import { Button } from '@chakra-ui/react'
import { useRestoreTodo } from '@/hooks/queries/useRestoreTodo'
import { useAppToast } from '@/hooks/useToast'

interface TodoRestoreButtonProps {
  id: string
}

export const TodoRestoreButton = ({ id }: TodoRestoreButtonProps) => {
  const restoreTodo = useRestoreTodo()
  const { showToast } = useAppToast()

  const handleRestore = () => {
    restoreTodo.mutate(id, {
      onSuccess: () => {
        showToast({
          title: 'Todo restored',
          description: 'Your todo has been restored successfully',
          status: 'success',
        })
      },
      onError: (error) => {
        showToast({
          title: 'Failed to restore todo',
          description: error instanceof Error ? error.message : 'An error occurred',
          status: 'error',
          onRetry: () => restoreTodo.mutate(id),
        })
      },
    })
  }

  return (
    <Button
      size="sm"
      onClick={handleRestore}
      colorPalette="green"
      loading={restoreTodo.isPending}
    >
      Restore
    </Button>
  )
}
