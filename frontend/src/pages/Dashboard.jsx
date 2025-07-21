import React, { useEffect, useState } from "react";
import TaskForm from "../components/AddTaskForm.jsx";
import TaskCard from "../components/TaskCard.jsx";
import axios from "axios";

const TaskDashboard = () => {
  const [tasks, setTasks] = useState([]);
  const [count, setCount] = useState(0);
  const [editTask, setEditTask] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [taskdeleted, setTaskdeleted] = useState(false);
  const limit = 1000;

  const fetchTasks = async (page = 1) => {
    try {
      console.log("calling backend");
      const res = await axios.get(
        `http://localhost:8000/alltasks?page=${page}&limit=${limit}`
      );

      setTasks(res.data.tasks);
      setCount(res.data.count);
    } catch (err) {
      console.error("Error fetching tasks:", err);
    }
  };

  useEffect(() => {
    console.log("useeffect called");
    fetchTasks(currentPage);
    setTaskdeleted(false);
  }, [currentPage, taskdeleted]);

  const handleDelete = async (id) => {
    try {
      console.log("deleting data");

      await axios.delete(`http://localhost:8000/deletetask/${id}`);

      const totalAfterDelete = count - 1;
      const maxPages = Math.max(Math.ceil(totalAfterDelete / limit), 1);
      const newPage = currentPage > maxPages ? maxPages : currentPage;
      setCurrentPage(newPage);
      setTaskdeleted(true);
    } catch (error) {
      console.error("Failed to delete task:", error);
      alert("Failed to delete the task.");
    }
  };

  const handleNext = () => {
    const maxPages = Math.ceil(count / limit);

    setCurrentPage(currentPage + 1);
  };

  const handlePrevious = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  return (
    <div className="p-4 mx-auto flex flex-col items-center">
      <div className="fixed top-0 z-50 max-w-6xl">
        <TaskForm
          editTask={editTask}
          setEditTask={setEditTask}
          onSuccess={() => fetchTasks(currentPage)}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mt-96">
        {tasks.length > 0 ? (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onEdit={setEditTask}
              onDelete={handleDelete}
            />
          ))
        ) : (
          <p className="text-center text-gray-500 col-span-full">
            No tasks found.
          </p>
        )}
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={handlePrevious}
          disabled={currentPage === 1}
          className="px-4 py-2 rounded bg-gray-300 hover:bg-gray-400 disabled:opacity-50"
        >
          Previous
        </button>

        <span className="text-lg font-semibold">Page {currentPage}</span>

        <button
          onClick={handleNext}
          className="px-4 py-2 rounded bg-gray-300 hover:bg-gray-400 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default TaskDashboard;
