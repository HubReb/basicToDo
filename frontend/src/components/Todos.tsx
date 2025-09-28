import React, { useEffect, useState, createContext, useContext } from 'react';
import {
  Box,
  Button,
  Container,
  Flex,
  Input,
  Stack,
  Text,
} from '@chakra-ui/react';
import { v4 as uuid } from "uuid";

interface Todo {
  id: string;
  title: string;
  description: string;
}

interface TodoContextType {
  todos: Todo[];
  fetchTodos: () => void;
}

const TodosContext = createContext<TodoContextType | undefined>(undefined);

const useTodos = () => {
  const context = useContext(TodosContext);
  if (!context) {
    throw new Error('useTodos must be used within a TodosProvider');
  }
  return context;
};

const UpdateToDo = ({ item, id, fetchTodos }: { item: string; id: string; fetchTodos: () => void }) => {
  const [todo, setTodo] = useState(item);
  const [isOpen, setIsOpen] = useState(false);
  
  const updateToDo = async () => {
    try {
      await fetch(`http://localhost:8000/todo/entry?item=${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "accept": "application/json"
        },
        body: JSON.stringify({ 
          id: id,
          title: todo,
          description: "not implemented yet",
          done: false
        }),
      });
      await fetchTodos();
      setIsOpen(false);
    } catch (error) {
      console.error("Error updating todo:", error);
    }
  };

  return (
    <Box p={1} shadow="sm">
      <Flex justify="space-between" gap="2rem" rowGap="2rem">
        <Text mt={4} as="div">
          <Flex align="end" gap="1rem">
            <Button 
              size="sm" 
              onClick={() => setIsOpen(!isOpen)}
            >
              Edit
            </Button>
            <DeleteTodo id={id} fetchTodos={fetchTodos} />
          </Flex>
        </Text>
      </Flex>
      
      {isOpen && (
        <Box mt={2} p={2} borderWidth="1px" borderRadius="md">
          <Input
            value={todo}
            onChange={(e) => setTodo(e.target.value)}
            placeholder="Edit todo"
          />
          <Flex gap={2} mt={2}>
            <Button 
              size="sm" 
              onClick={updateToDo}
              colorScheme="blue"
            >
              Save
            </Button>
            <Button 
              size="sm" 
              onClick={() => setIsOpen(false)}
              variant="outline"
            >
              Cancel
            </Button>
          </Flex>
        </Box>
      )}
    </Box>
  );
};

const TodoHelper = ({ item, id, fetchTodos }: { item: string; id: string; fetchTodos: () => void }) => {
  return (
    <Box p={1} shadow="sm">
      <Flex justify="space-between" gap="2rem" rowGap="2rem">
        <Text mt={4} as="div">
          {item}
          <Flex align="end" gap="1rem">
            <UpdateToDo item={item} id={id} fetchTodos={fetchTodos} />
          </Flex>
        </Text>
      </Flex>
    </Box>
  );
};

const DeleteTodo = ({ id, fetchTodos }: { id: string; fetchTodos: () => void }) => {
  const deleteTodo = async () => {
    if (window.confirm("Do you really want to delete this item?")) {
      try {
        await fetch(`http://localhost:8000/todo/entry?item=${id}`, {
          method: "DELETE",
          headers: {
                  "accept": "application/json"
          }
        });
        await fetchTodos();
      } catch (error) {
        console.error("Error deleting todo:", error);
      }
    }
  };

  return (
    <Button 
      size="sm" 
      marginLeft={2} 
      onClick={deleteTodo}
      colorScheme="red"
    >
      Delete Todo
    </Button>
  );
};

const AddToDo = ({ fetchTodos }: { fetchTodos: () => void }) => {
  const [item, setItem] = React.useState("");

  const handleInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    setItem(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!item.trim()) return;
    
    try {
      const newTodo = {
        id: uuid(),
        title: item.trim(),
        description: "not implemented yet"
      };

      await fetch(`http://localhost:8000/todo/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "accept": "application/json"
        },
        body: JSON.stringify(newTodo)
      });
      
      await fetchTodos();
      setItem("");
    } catch (error) {
      console.error("Error adding todo:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Input
        value={item}
        pr="4.5rem"
        type="text"
        placeholder="Add a todo item"
        aria-label="Add a todo item"
        onChange={handleInput}
      />
    </form>
  );
};

export default function Todos() {
  const [todos, setTodos] = useState<Todo[]>([]);
  
  const fetchTodos = async () => {
    try {
      const response = await fetch("http://localhost:8000/todo?limit=10&page=1");
      const result = await response.json();
      if (Array.isArray(result)) {
              setTodos(result);
      } else if (result.data && Array.isArray(result.data)) {
              setTodos(result.data);
      } else {
              setTodos([]);
      }
    } catch (error) {
      console.error("Error fetching todos:", error);
      setTodos([]);
    }
  };

  useEffect(() => {
    fetchTodos();
  }, []);

  return (
    <TodosContext.Provider value={{ todos, fetchTodos }}>
      <Container maxW={{ base: "container.xl", md: "container.xl" }} pt="100px">
        <AddToDo fetchTodos={fetchTodos} />
        <Stack gap={5}>
          {todos.map((todo: Todo) => (
            <TodoHelper 
              key={todo.id} 
              item={todo.title} 
              id={todo.id} 
              fetchTodos={fetchTodos} 
            />
          ))}
        </Stack>
      </Container>
    </TodosContext.Provider>
  );
}
