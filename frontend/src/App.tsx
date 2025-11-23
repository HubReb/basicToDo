import { ChakraProvider, Toaster } from '@chakra-ui/react';
import { defaultSystem } from '@chakra-ui/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import './App.css';
import Header from './components/Header';
import Todos, {TodosProvider} from './components/Todos';
import { queryClient } from './config/queryClient';
import { toaster } from './hooks/useToast';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChakraProvider value={defaultSystem}>
        <TodosProvider >
          <Header />
          <Todos />
          <Toaster toaster={toaster}>{() => null}</Toaster>
        </TodosProvider>
      </ChakraProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;