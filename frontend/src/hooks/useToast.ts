import { toaster } from '@/components/ui/toaster'

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

