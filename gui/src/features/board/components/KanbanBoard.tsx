/**
 * Kanban Board view - tasks organized by status columns with drag-drop support
 */

import { useState, useCallback, useMemo } from "react";
import { Plus, MoreHorizontal, SortAsc, SortDesc, Filter, Archive } from "lucide-react";
import type { TaskListItem, TaskStatus } from "@/types/task";
import { EmptyState } from "@/components/common/EmptyState";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/common/Toast";
import { cn } from "@/lib/utils";
import { TaskCard } from "@/features/tasks/components/TaskCard";

interface KanbanBoardProps {
  tasks: TaskListItem[];
  onTaskClick?: (taskId: string) => void;
  onNewTask?: () => void;
  onStatusChange?: (taskId: string, newStatus: TaskStatus) => void;
  onDelete?: (taskId: string) => void;
  isLoading?: boolean;
}

type StatusColumn = "TODO" | "ACTIVE" | "DONE";

interface ColumnConfig {
  id: StatusColumn;
  title: string;
  statusFilter: TaskStatus[];
  targetStatus: TaskStatus;
  color: string;
  bgColor: string;
  borderColor: string;
}

const columns: ColumnConfig[] = [
  {
    id: "TODO",
    title: "TODO",
    statusFilter: ["TODO"],
    targetStatus: "TODO",
    color: "hsl(var(--foreground-subtle))",
    bgColor: "hsl(var(--background-muted))",
    borderColor: "hsl(var(--border))",
  },
  {
    id: "ACTIVE",
    title: "ACTIVE",
    statusFilter: ["ACTIVE"],
    targetStatus: "ACTIVE",
    color: "hsl(var(--primary))",
    bgColor: "hsl(var(--primary-subtle))",
    borderColor: "hsl(var(--primary))",
  },
  {
    id: "DONE",
    title: "DONE",
    statusFilter: ["DONE"],
    targetStatus: "DONE",
    color: "hsl(var(--status-done))",
    bgColor: "hsl(var(--status-done) / 0.1)",
    borderColor: "hsl(var(--status-done))",
  },
];

export function KanbanBoard({
  tasks,
  onTaskClick,
  onNewTask,
  onStatusChange,
  onDelete,
  isLoading = false,
}: KanbanBoardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draggedTaskId, setDraggedTaskId] = useState<string | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<StatusColumn | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc" | null>(null);
  const [columnFilters, setColumnFilters] = useState<Record<StatusColumn, string>>({
    TODO: "",
    ACTIVE: "",
    DONE: "",
  });
  const [editingFilterColumn, setEditingFilterColumn] = useState<StatusColumn | null>(null);
  const [hideDoneTasks, setHideDoneTasks] = useState(false);

  const handleClick = useCallback((taskId: string) => {
    setSelectedId(taskId);
    onTaskClick?.(taskId);
  }, [onTaskClick]);

  const handleDragStart = useCallback((taskId: string) => {
    setDraggedTaskId(taskId);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedTaskId(null);
    setDragOverColumn(null);
  }, []);

  const handleDragOver = useCallback((columnId: StatusColumn) => {
    setDragOverColumn(columnId);
  }, []);

  const handleDrop = useCallback((targetStatus: TaskStatus) => {
    if (draggedTaskId && onStatusChange) {
      const task = tasks.find(t => t.id === draggedTaskId);
      if (task && task.status !== targetStatus) {
        onStatusChange(draggedTaskId, targetStatus);
      }
    }
    setDraggedTaskId(null);
    setDragOverColumn(null);
  }, [draggedTaskId, tasks, onStatusChange]);

  const handleSort = (dir: "asc" | "desc") => {
    setSortDirection(dir);
    toast.info(dir === "asc" ? "Sorted A–Z" : "Sorted Z–A");
  };

  const toggleFilterForColumn = (columnId: StatusColumn) => {
    setEditingFilterColumn((prev) => (prev === columnId ? null : columnId));
  };

  const setFilterForColumn = (columnId: StatusColumn, value: string) => {
    setColumnFilters((prev) => ({ ...prev, [columnId]: value }));
  };

  const toggleHideDone = () => {
    setHideDoneTasks((prev) => {
      const next = !prev;
      toast.info(next ? "Done tasks hidden from board" : "Done tasks visible");
      return next;
    });
  };

  const filteredColumns = useMemo(() => {
    return columns.map(column => {
      let columnTasks = tasks.filter((t) => column.statusFilter.includes(t.status));

      const filterValue = columnFilters[column.id];
      if (filterValue) {
        const q = filterValue.toLowerCase();
        columnTasks = columnTasks.filter(
          (t) => t.title.toLowerCase().includes(q) || t.id.toLowerCase().includes(q)
        );
      }

      if (column.id === "DONE" && hideDoneTasks) {
        columnTasks = [];
      }

      if (sortDirection) {
        columnTasks = [...columnTasks].sort((a, b) =>
          sortDirection === "asc"
            ? a.title.localeCompare(b.title)
            : b.title.localeCompare(a.title)
        );
      }

      return {
        ...column,
        tasks: columnTasks
      };
    });
  }, [tasks, columnFilters, sortDirection, hideDoneTasks]);

  if (isLoading) {
    return (
      <div className="flex gap-5 p-6 flex-1 overflow-x-auto">
        {columns.map((col) => (
          <KanbanColumnSkeleton key={col.id} title={col.title} />
        ))}
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <EmptyState variant="tasks" onAction={onNewTask} />
      </div>
    );
  }

  return (
    <div className="flex gap-5 p-6 flex-1 overflow-x-auto items-start h-full">
      {filteredColumns.map((column) => (
        <KanbanColumn
          key={column.id}
          config={column}
          tasks={column.tasks}
          selectedId={selectedId}
          draggedTaskId={draggedTaskId}
          isDragOver={dragOverColumn === column.id}
          onTaskClick={handleClick}
          onNewTask={column.id === "TODO" ? onNewTask : undefined}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragOver={() => handleDragOver(column.id)}
          onDrop={() => handleDrop(column.targetStatus)}
          onSort={handleSort}
          onToggleFilter={() => toggleFilterForColumn(column.id)}
          filterValue={columnFilters[column.id]}
          isFilterEditing={editingFilterColumn === column.id}
          onFilterChange={(v) => setFilterForColumn(column.id, v)}
          hideDoneTasks={hideDoneTasks}
          onToggleHideDone={toggleHideDone}
          onStatusChange={onStatusChange}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

interface KanbanColumnProps {
  config: ColumnConfig;
  tasks: TaskListItem[];
  selectedId: string | null;
  draggedTaskId: string | null;
  isDragOver: boolean;
  onTaskClick: (taskId: string) => void;
  onNewTask?: () => void;
  onDragStart: (taskId: string) => void;
  onDragEnd: () => void;
  onDragOver: () => void;
  onDrop: () => void;
  onSort: (dir: "asc" | "desc") => void;
  onToggleFilter: () => void;
  filterValue: string;
  isFilterEditing: boolean;
  onFilterChange: (value: string) => void;
  hideDoneTasks: boolean;
  onToggleHideDone: () => void;
  onStatusChange?: (taskId: string, newStatus: TaskStatus) => void;
  onDelete?: (taskId: string) => void;
}

function KanbanColumn({
  config,
  tasks,
  selectedId,
  draggedTaskId,
  isDragOver,
  onTaskClick,
  onNewTask,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
  onSort,
  onToggleFilter,
  filterValue,
  isFilterEditing,
  onFilterChange,
  hideDoneTasks,
  onToggleHideDone,
  onStatusChange,
  onDelete,
}: KanbanColumnProps) {
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    onDragOver();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    onDrop();
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col min-w-[320px] max-w-[320px] rounded-xl transition-all duration-200 h-full max-h-full",
        isDragOver ? "bg-muted/80 border-2 border-dashed border-primary/50" : "bg-muted/30 border-2 border-transparent"
      )}
    >
      {/* Column header */}
      <div className="flex items-center justify-between p-3.5 border-b border-border/50 bg-background/50 backdrop-blur-sm sticky top-0 rounded-t-xl z-10">
        <div className="flex items-center gap-2.5">
          <span
            className="w-2 h-2 rounded-full ring-2 ring-opacity-20"
            style={{ backgroundColor: config.color, boxShadow: `0 0 0 2px ${config.color}20` }}
          />
          <span className="text-sm font-semibold text-foreground tracking-tight">
            {config.title}
          </span>
          <span className="rounded-full bg-background-muted px-2 py-0.5 text-xs font-medium text-foreground-muted tabular-nums">
            {tasks.length}
          </span>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7 hover:bg-background-muted">
              <MoreHorizontal className="h-4 w-4 text-foreground-subtle" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={() => onSort("asc")}>
              <SortAsc className="mr-2 h-3.5 w-3.5" /> Sort A-Z
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onSort("desc")}>
              <SortDesc className="mr-2 h-3.5 w-3.5" /> Sort Z-A
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onToggleFilter}>
              <Filter className="mr-2 h-3.5 w-3.5" /> {filterValue ? "Edit filter" : "Filter tasks"}
            </DropdownMenuItem>
            {config.id === "DONE" && (
              <DropdownMenuItem onClick={onToggleHideDone}>
                <Archive className="mr-2 h-3.5 w-3.5" /> {hideDoneTasks ? "Show done tasks" : "Hide done tasks"}
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {isFilterEditing && (
        <div className="p-3 border-b border-border bg-background animate-accordion-down">
          <Input
            value={filterValue}
            onChange={(e) => onFilterChange(e.target.value)}
            placeholder="Filter tasks..."
            autoFocus
            className="h-8 text-xs"
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                onToggleFilter();
              }
            }}
          />
        </div>
      )}

      {/* Column content */}
      <div className="flex-1 flex flex-col gap-3 overflow-y-auto p-3 min-h-[100px] scrollbar-thin">
        {tasks.map((task) => (
          <div
            key={task.id}
            draggable
            onDragStart={(e) => {
              e.dataTransfer.effectAllowed = "move";
              e.dataTransfer.setData("text/plain", task.id);
              onDragStart(task.id);
            }}
            onDragEnd={onDragEnd}
            className={cn(
              "cursor-grab active:cursor-grabbing",
              draggedTaskId === task.id && "opacity-50 grayscale"
            )}
          >
            <TaskCard
              task={task}
              isSelected={selectedId === task.id}
              onClick={() => onTaskClick(task.id)}
              onStatusChange={(status) => onStatusChange?.(task.id, status)}
              onDelete={() => onDelete?.(task.id)}
            />
          </div>
        ))}

        {/* Drop zone indicator when empty */}
        {tasks.length === 0 && isDragOver && (
          <div className="flex flex-1 min-h-[120px] rounded-xl border-2 border-dashed border-primary/20 bg-primary/5 items-center justify-center text-sm font-medium text-primary opacity-70 animate-pulse">
            Drop here
          </div>
        )}

        {/* Add task button */}
        {onNewTask && (
          <button
            onClick={onNewTask}
            className="group flex w-full items-center gap-2 rounded-xl border border-dashed border-border p-3 text-[13px] text-foreground-muted transition-all hover:border-primary hover:bg-primary-subtle hover:text-primary mt-auto"
          >
            <Plus className="h-4 w-4" />
            Create new task
          </button>
        )}
      </div>
    </div>
  );
}

function KanbanColumnSkeleton({ title }: { title: string }) {
  return (
    <div className="flex flex-col min-w-[320px] max-w-[320px] rounded-xl bg-background-subtle h-[500px] animate-pulse">
      <div className="flex items-center gap-2.5 p-3.5 border-b border-border">
        <div className="h-2 w-2 rounded-full bg-border" />
        <span className="text-sm font-semibold text-foreground opacity-50">{title}</span>
      </div>
    </div>
  );
}