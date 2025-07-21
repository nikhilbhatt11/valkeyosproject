import React from "react";
import axios from "axios";

const priorityColors = {
  High: "bg-red-500",
  Medium: "bg-yellow-500",
  Low: "bg-green-500",
};

const statusColors = {
  completed: "text-green-600",
  pending: "text-red-500",
  inprogress: "text-yellow-500",
};

const TaskCard = ({ task, onEdit, onDelete }) => {
  return (
    <div className="bg-white shadow-md rounded-xl p-5 hover:shadow-lg transition-all">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-xl font-semibold">{task.title}</h2>
        <span
          className={`text-xs px-2 py-1 rounded-full text-white ${
            priorityColors[task.priority]
          }`}
        >
          {task.priority}
        </span>
      </div>

      <p className="text-sm text-gray-700">{task.description}</p>

      <div className="mt-4 flex justify-between items-center text-sm text-gray-500">
        <span>Deadline {task.deadline}</span>
        <span className={`font-semibold ${statusColors[task.status]}`}>
          {task.status}
        </span>
      </div>

      <div className="mt-4 flex justify-end gap-4">
        <button
          onClick={() => onEdit(task)}
          className="text-blue-600 hover:underline text-sm"
        >
          Update
        </button>
        <button
          onClick={() => onDelete(task.id)}
          className="text-red-600 hover:underline text-sm"
        >
          Delete
        </button>
      </div>
    </div>
  );
};

export default TaskCard;
