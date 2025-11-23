import { ChakraProvider } from '@chakra-ui/react';
import { defaultSystem } from '@chakra-ui/react';
import './App.css';
import Header from './components/Header';
import Todos, {TodosProvider} from './components/Todos';

function App() {
  return (
    <ChakraProvider value={defaultSystem}>
    <TodosProvider >
        <Header />
        <Todos />
    </TodosProvider>
    </ChakraProvider>
  );
}

export default App;