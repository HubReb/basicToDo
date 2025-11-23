import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock environment variables for tests
vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
