import react from "@vitejs/plugin-react"
import { defineConfig } from 'vite'
import tsconfigPaths from "vite-tsconfig-paths"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  optimizeDeps: {
    include: ['@chakra-ui/react', '@chakra-ui/system']
  }
})
