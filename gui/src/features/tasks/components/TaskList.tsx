import { useEffect, useState } from "react";
import { TaskCard } from "./TaskCard";
import { TaskListSkeleton } from "@/components/common/Skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import type { TaskListItem, TaskStatus } from "@/types/task";

interface TaskListProps {
  tasks: TaskListItem[];
  onTaskClick?: (taskId: string) => void;
  focusedTaskId?: string | null;
  onFocusChange?: (taskId: string | null) => void;
  onNewTask?: () => void;
  onStatusChange?: (taskId: string, status: TaskStatus) => void;
  onDelete?: (taskId: string) => void;
  isLoading?: boolean;
  searchQuery?: string;
}

export function TaskList({
  tasks,
  onTaskClick,
  focusedTaskId,
  onFocusChange,
  onNewTask,
  onStatusChange,
  onDelete,
  isLoading = false,
  searchQuery,
}: TaskListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const effectiveSelectedId = focusedTaskId ?? selectedId;

  const handleClick = (taskId: string) => {
    setSelectedId(taskId);
    onFocusChange?.(taskId);
    onTaskClick?.(taskId);
  };

  useEffect(() => {
    if (!effectiveSelectedId) return;
    const el = document.querySelector<HTMLElement>(`[data-task-id="${effectiveSelectedId}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [effectiveSelectedId]);

  // Skeleton loading state
  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-6">
        <TaskListSkeleton count={6} />
      </div>
    );
  }

  // Empty state - no tasks at all
  if (tasks.length === 0 && !searchQuery) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <EmptyState
          variant="tasks"
          onAction={onNewTask}
        />
      </div>
    );
  }

  // Empty state - search with no results
  if (tasks.length === 0 && searchQuery) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <EmptyState
          variant="search"
          title="No matching tasks"
          description={`No tasks found for "${searchQuery}". Try a different search term.`}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
       <div className="grid grid-cols-[repeat(auto-fill,minmax(340px,1fr))] gap-4 content-start">
        {tasks.map((task) => (
            <div key={task.id} data-task-id={task.id}>
            <TaskCard
                task={task}
                onClick={() => handleClick(task.id)}
                onStatusChange={onStatusChange ? (status) => onStatusChange(task.id, status) : undefined}
                onDelete={onDelete ? () => onDelete(task.id) : undefined}
                isSelected={effectiveSelectedId === task.id}
            />
            </div>
        ))}
      </div>
    </div>
  );
}