import { ChakraProvider } from '@chakra-ui/react';
import { defaultSystem } from '@chakra-ui/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import './App.css';
import Header from './components/Header';
import { TodoList } from './components/todos/TodoList';
import { ErrorBoundary } from './components/errors/ErrorBoundary';
import { queryClient } from './config/queryClient';
import { Toaster } from './components/ui/toaster';

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ChakraProvider value={defaultSystem}>
          <Header />
          <TodoList />
          <Toaster />
        </ChakraProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;