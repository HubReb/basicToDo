import React, { useEffect, useState, createContext, useContext, useCallback } from 'react';
import {
  Box,
  Button,
  Container,
  Flex,
  Input,
  Stack,
  Text,
  Checkbox,
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerBody,
  DrawerFooter,
  useDisclosure
} from '@chakra-ui/react';
import { v4 as uuid } from "uuid";

// Define Todo interface
interface Todo {
  id: string;
  title: string;
  description: string;
  done: boolean; // Add done status for the todo
}

// Define the TodoContextType interface
interface TodoContextType {
  todos: Todo[];
  fetchTodos: (page: number, limit: number) => void;
  total: number;
  setPage: React.Dispatch<React.SetStateAction<number>>;
  page: number;
  limit: number;
  toggleDone: (id: string, done: boolean) => void; // Function to toggle done state
}

// Create TodosContext to manage the state globally
export const TodosContext = createContext<TodoContextType | undefined>(undefined);

// Custom hook to access Todos context
export const useTodos = () => {
  const context = useContext(TodosContext);
  if (!context) {
    throw new Error('useTodos must be used within a TodosProvider');
  }
console.log('Todos context:', context);  // Add this line to log the context
  return context;
};

// Component to handle todo update (edit title/description)
const UpdateToDo = ({ item, id, description, fetchTodos }: { item: string, id: string, description: string, fetchTodos: () => void }) => {
  const [todoTitle, setTodoTitle] = useState(item);
  const [isOpen, setIsOpen] = useState(false);
  const updateToDo = async () => {
    try {
      await fetch(`http://localhost:8000/todo/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "accept": "application/json"
        },
        body: JSON.stringify({
          id: id,
          title: todoTitle,
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
          </Flex>
        </Text>
      </Flex>

      {isOpen && (
        <Box mt={2} p={2} borderWidth="1px" borderRadius="md">
          <Input
            value={todoTitle}
            onChange={(e) => setTodoTitle(e.target.value)}
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


// Component to display a single todo
const TodoHelper = ({ item, id, done, description, fetchTodos, toggleDone }: { item: string; id: string; done: boolean; description: string; fetchTodos: () => void; toggleDone: (id: string, done: boolean) => void }) => {

    const handleToggleDone = useCallback(() => {
        toggleDone(id, !done); // Toggle done state manually
    }, [toggleDone, id, done]);
  return (
    <Box p={1} shadow="sm">
      <Flex justify="space-between" gap="2rem" rowGap="2rem">
        <Text mt={4} as="div">
          {item}
          <Flex align="end" gap="1rem">
            <UpdateToDo id={id} item={item} description={description} fetchTodos={fetchTodos} />
            <DeleteTodo id={id} fetchTodos={fetchTodos} />
          </Flex>
        </Text>
      </Flex>
    </Box>
  );
};

// Component to handle todo deletion
const DeleteTodo = ({ id, fetchTodos }: { id: string; fetchTodos: () => void }) => {
        console.log("DeleteTodo ID:", id);
  const deleteTodo = async () => {
    if (window.confirm("Do you really want to delete this item?")) {
      try {
        await fetch(`http://localhost:8000/todo/${id}`, {
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

// Component to add a new todo
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
        description: "not implemented yet",
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

// TodosProvider Component for managing global state
export const TodosProvider = ({ children }: { children: React.ReactNode }) => {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [page, setPage] = useState(1); // Current page
  const [limit, setLimit] = useState(10); // Todos per page
  const [total, setTotal] = useState(0); // Total number of todos

  const fetchTodos = useCallback(async (currentPage = page, currentLimit = limit) => {
    try {
      const response = await fetch(`http://localhost:8000/todo?limit=${currentLimit}&page=${currentPage}`);
      const result = await response.json();
      if (Array.isArray(result.todo_entries)) {
        setTodos(result.todo_entries); // Use the correct response structure
      }
      setTotal(result.results || 0); // Set total from response
    } catch (error) {
      console.error("Error fetching todos:", error);
      setTodos([]);
    }
  }, [page, limit]);

  const toggleDone = async (id: string, done: boolean) => {
    try {
      await fetch(`http://localhost:8000/todo/entry?item=${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "accept": "application/json"
        },
        body: JSON.stringify({
          done: done
        }),
      });
      await fetchTodos(); // Refetch todos to update done status
    } catch (error) {
      console.error("Error toggling done state:", error);
    }
  };

  return (
    <TodosContext.Provider value={{ todos, fetchTodos, total, setPage, page, limit, toggleDone }}>
      {children}
    </TodosContext.Provider>
  );
};

// Main Todos component to render the UI

export default function Todos() {
  const { todos, fetchTodos, page, total, setPage, limit, toggleDone } = useTodos();

  useEffect(() => {
        if (todos.length === 0) {
            fetchTodos(page, limit);
        }
  }, [page, limit, fetchTodos, todos.length]);

  return (
    <Container maxW="container.xl" pt="100px">
      <AddToDo fetchTodos={fetchTodos} />
      <Stack gap={5}>
        {todos.map((todo: Todo) => (
          <TodoHelper
            item={todo.title}
            id={todo.id}
            done={todo.done}
            description={todo.description}
            fetchTodos={fetchTodos}
            toggleDone={toggleDone}
          />
        ))}
      </Stack>
    </Container>
  );
};