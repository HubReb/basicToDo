import { createToaster } from '@chakra-ui/react'

const toaster = createToaster({
  placement: 'top',
  duration: 5000,
})

export interface ToastOptions {
  title: string
  description?: string
  status?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  onRetry?: () => void
}

export const useAppToast = () => {
  const showToast = ({ title, description, status = 'info', duration = 5000, onRetry }: ToastOptions) => {
    toaster.create({
      title,
      description,
      type: status,
      duration,
      action: onRetry ? {
        label: 'Retry',
        onClick: onRetry,
      } : undefined,
    })
  }

  return { showToast }
}

export { toaster }

