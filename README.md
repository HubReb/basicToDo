# basicToDo
A simple ToDo application to be enhanced over time.

## Basic functionality
![image](images/basicApp.png)

The app lists the ToDo items on the main screen.

### Add an item
Enter an item into the editline and hit 'enter'.
![image](images/basicAppAddToDo.png)

### Update an item
Hit 'Update' an item and enter a new description.
![image](images/basicAppAddUpdateToDo.png)

### Delete an item
Hit 'Delete' an item to remove it from the list.
![image](images/basicAppDeleteToDo.png)


## Installation

### Frontend
Enter the folder _frontend_ and run
```
npm install
```

### Backend
It is recommended to use a python package manager.
This project uses ```uv```. Refer to [uv installations instructions](https://docs.astral.sh/uv/getting-started/installation/) for installation instructions.

Run 
```uv sync uv.lock```
to install the python dependencies.


## Running the application

Run the python backend 
``` python -m app.main```

and run the frontend

```npm run dev```
