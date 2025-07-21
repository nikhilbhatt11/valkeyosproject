import React, { useEffect, useState } from "react";
import axios from "axios";

const TaskForm = ({ editTask, setEditTask, onSuccess }) => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [deadline, setDeadline] = useState("");
  const [status, setStatus] = useState("pending");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (editTask) {
      setTitle(editTask.title || "");
      setDescription(editTask.description || "");
      setDeadline(
        editTask.deadline
          ? new Date(editTask.deadline).toISOString().slice(0, 10)
          : ""
      );
      setStatus(editTask.status || "pending");
    } else {
      setTitle("");
      setDescription("");
      setDeadline("");
      setStatus("pending");
    }
  }, [editTask]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const taskData = { title, description, deadline, status };

    try {
      if (editTask) {
        await axios.put(
          `http://localhost:8000/updatetasks/${editTask.id}`,
          taskData
        );
        setEditTask(null);
        setMessage("Task updated successfully");
        onSuccess();
      } else {
        await axios.post("http://localhost:8000/addtasks", taskData);
        setMessage("New task created");

        setTimeout(() => {
          onSuccess();
        }, 300);
      }

      setTitle("");
      setDescription("");
      setDeadline("");
      setStatus("pending");

      setTimeout(() => setMessage(""), 3000); // Clear message
    } catch (err) {
      console.error("Error submitting task:", err);
      setMessage("Error submitting task");
      setTimeout(() => setMessage(""), 3000);
    }
  };

  const handleCancel = () => {
    setEditTask(null);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white shadow-md p-4 rounded-lg space-y-4"
    >
      <h2 className="text-xl font-semibold text-center">
        {editTask ? "Update Task" : "Add New Task"}
      </h2>

      {message && (
        <div className="text-green-600 text-center font-medium">{message}</div>
      )}

      <input
        type="text"
        value={title}
        placeholder="Title"
        onChange={(e) => setTitle(e.target.value)}
        required
        className="w-full border p-2 rounded"
      />

      <textarea
        value={description}
        placeholder="Description"
        onChange={(e) => setDescription(e.target.value)}
        className="w-full border p-2 rounded"
      ></textarea>

      <input
        type="date"
        value={deadline}
        onChange={(e) => setDeadline(e.target.value)}
        className="w-full border p-2 rounded"
      />

      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="w-full border p-2 rounded"
      >
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
        <option value="inprogress">In Progress</option>
      </select>

      <div className="flex gap-4 justify-end">
        {editTask && (
          <button
            type="button"
            onClick={handleCancel}
            className="bg-gray-300 hover:bg-gray-400 text-black px-4 py-2 rounded"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          {editTask ? "Update Task" : "Add Task"}
        </button>
      </div>
    </form>
  );
};

export default TaskForm;
