import { useEffect, useMemo, useState, useCallback } from "react";
import { TaskCard } from "./TaskCard";
import { TaskListSkeleton } from "@/components/common/Skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { useKeyboardListNavigation } from "@/hooks/useKeyboardListNavigation";
import { getApiTaskId } from "@/lib/taskId";
import { useUIStore } from "@/stores/uiStore";
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
  const detailPanelTaskId = useUIStore((s) => s.detailPanel?.taskId);
  const effectiveSelectedId = focusedTaskId ?? selectedId;

  const handleClick = (taskId: string) => {
    setSelectedId(taskId);
    onFocusChange?.(taskId);
    onTaskClick?.(taskId);
  };

  const taskIds = useMemo(() => tasks.map((t) => t.id), [tasks]);

  const setActiveTaskId = useCallback(
    (taskId: string | null) => {
      setSelectedId(taskId);
      onFocusChange?.(taskId);
    },
    [onFocusChange]
  );

  useKeyboardListNavigation({
    enabled: tasks.length > 0,
    itemIds: taskIds,
    activeId: effectiveSelectedId,
    onActiveChange: setActiveTaskId,
    onActivate: (taskId) => {
      setActiveTaskId(taskId);
      onTaskClick?.(taskId);
    },
  });

  useEffect(() => {
    if (!effectiveSelectedId) return;
    const el = document.querySelector<HTMLElement>(`[data-task-id="${effectiveSelectedId}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [effectiveSelectedId]);

  useEffect(() => {
    if (!detailPanelTaskId) return;
    const match = tasks.find((t) => getApiTaskId(t) === detailPanelTaskId);
    if (!match) return;
    setSelectedId(match.id);
    onFocusChange?.(match.id);
  }, [detailPanelTaskId, onFocusChange, tasks]);

  // Skeleton loading state
  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-[var(--density-page-pad)]">
        <TaskListSkeleton count={6} />
      </div>
    );
  }

  // Empty state - no tasks at all
  if (tasks.length === 0 && !searchQuery) {
    return (
      <div className="flex flex-1 items-center justify-center p-[var(--density-page-pad)]">
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
      <div className="flex flex-1 items-center justify-center p-[var(--density-page-pad)]">
        <EmptyState
          variant="search"
          title="No matching tasks"
          description={`No tasks found for "${searchQuery}". Try a different search term.`}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-[var(--density-page-pad)]">
       <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-3 content-start">
        {tasks.map((task) => (
            <div key={task.id} data-task-id={task.id}>
            <TaskCard
                task={task}
                onClick={() => handleClick(task.id)}
                onStatusChange={onStatusChange ? (status) => onStatusChange(task.id, status) : undefined}
                onDelete={onDelete ? () => onDelete(task.id) : undefined}
                isSelected={
                  effectiveSelectedId === task.id ||
                  (detailPanelTaskId ? getApiTaskId(task) === detailPanelTaskId : false)
                }
            />
            </div>
        ))}
      </div>
    </div>
  );
}
