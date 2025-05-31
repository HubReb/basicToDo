import { useState } from 'react'
import { ChakraProvider } from '@chakra-ui/react';
import { defaultSystem } from '@chakra-ui/react';
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import Header from './components/Header';
import Todos from './components/Todos';

function App() {
  const [count, setCount] = useState(0)

  return (
	  <ChakraProvider value={defaultSystem}>
	  	<Header />
		<Todos /> {}
	</ChakraProvider>
  )
}

export default App
