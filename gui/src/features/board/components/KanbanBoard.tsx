/**
 * Kanban Board view - tasks organized by status columns with drag-drop support
 */

import { useEffect, useState, useCallback, useMemo } from "react";
import { Plus, MoreHorizontal, SortAsc, SortDesc, Filter, Archive } from "lucide-react";
import type { TaskListItem, TaskStatus } from "@/types/task";
import { EmptyState } from "@/components/common/EmptyState";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/common/toast";
import { cn } from "@/lib/utils";
import { TaskCard } from "@/features/tasks/components/TaskCard";
import { getApiTaskId } from "@/lib/taskId";
import { useUIStore } from "@/stores/uiStore";

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
  const isMobile = useMediaQuery("(max-width: 767px)");
  const detailPanelTaskId = useUIStore((s) => s.detailPanel?.taskId);
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

  useEffect(() => {
    if (!detailPanelTaskId) return;
    const match = tasks.find((t) => getApiTaskId(t) === detailPanelTaskId);
    if (!match) return;
    setSelectedId(match.id);
  }, [detailPanelTaskId, tasks]);

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
      toast.info(next ? "Done steps hidden from board" : "Done steps visible");
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
      <div
        className={cn(
          "flex flex-1 min-h-0 gap-[var(--density-page-gap)] p-[var(--density-page-pad)]",
          isMobile ? "flex-col overflow-y-auto overflow-x-hidden" : "overflow-x-auto items-stretch"
        )}
      >
        {columns.map((col) => (
          <KanbanColumnSkeleton key={col.id} title={col.title} isMobile={isMobile} />
        ))}
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-[var(--density-page-pad)]">
        <EmptyState variant="tasks" onAction={onNewTask} />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-1 min-h-0 gap-[var(--density-page-gap)] p-[var(--density-page-pad)]",
        isMobile ? "flex-col overflow-y-auto overflow-x-hidden" : "overflow-x-auto items-stretch"
      )}
    >
      {filteredColumns.map((column) => (
        <KanbanColumn
          key={column.id}
          mode={isMobile ? "stacked" : "columns"}
          config={column}
          tasks={column.tasks}
          selectedId={selectedId}
          detailPanelTaskId={detailPanelTaskId || undefined}
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
  mode: "columns" | "stacked";
  config: ColumnConfig;
  tasks: TaskListItem[];
  selectedId: string | null;
  detailPanelTaskId?: string;
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
  mode,
  config,
  tasks,
  selectedId,
  detailPanelTaskId,
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
  const dragEnabled = mode === "columns";

  const handleDragOver = (e: React.DragEvent) => {
    if (!dragEnabled) return;
    e.preventDefault();
    onDragOver();
  };

  const handleDrop = (e: React.DragEvent) => {
    if (!dragEnabled) return;
    e.preventDefault();
    onDrop();
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col rounded-xl transition-all duration-200 border-2",
        mode === "columns"
          ? "flex-1 min-h-0 min-w-[240px] sm:min-w-[260px] xl:min-w-[300px] h-full max-h-full"
          : "w-full min-w-0",
        dragEnabled && isDragOver
          ? "bg-muted/80 border-dashed border-primary/50"
          : "bg-muted/30 border-transparent"
      )}
    >
      {/* Column header */}
      <div
        className={cn(
          "flex items-center justify-between border-b border-border/50 bg-background/50 backdrop-blur-sm rounded-t-xl",
          mode === "columns" && "sticky top-0 z-10",
          "p-[var(--density-card-pad)]"
        )}
      >
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
	              <Filter className="mr-2 h-3.5 w-3.5" /> {filterValue ? "Edit filter" : "Filter steps"}
	            </DropdownMenuItem>
	            {config.id === "DONE" && (
	              <DropdownMenuItem onClick={onToggleHideDone}>
	                <Archive className="mr-2 h-3.5 w-3.5" /> {hideDoneTasks ? "Show done steps" : "Hide done steps"}
	              </DropdownMenuItem>
	            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {isFilterEditing && (
        <div className="p-[var(--density-card-pad)] border-b border-border bg-background animate-accordion-down">
	          <Input
	            value={filterValue}
	            onChange={(e) => onFilterChange(e.target.value)}
	            placeholder="Filter steps..."
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
      <div
        className={cn(
          "flex flex-col gap-2 p-[var(--density-card-pad)]",
          mode === "columns" ? "flex-1 min-h-[100px] overflow-y-auto scrollbar-thin" : "overflow-visible"
        )}
      >
        {tasks.map((task) => (
          <div
            key={task.id}
            draggable={dragEnabled}
            onDragStart={
              dragEnabled
                ? (e) => {
                    e.dataTransfer.effectAllowed = "move";
                    e.dataTransfer.setData("text/plain", task.id);
                    onDragStart(task.id);
                  }
                : undefined
            }
            onDragEnd={dragEnabled ? onDragEnd : undefined}
            className={cn(
              dragEnabled && "cursor-grab active:cursor-grabbing",
              draggedTaskId === task.id && "opacity-50 grayscale"
            )}
          >
            <TaskCard
              task={task}
              isSelected={
                selectedId === task.id ||
                (detailPanelTaskId ? getApiTaskId(task) === detailPanelTaskId : false)
              }
              onClick={() => onTaskClick(task.id)}
              onStatusChange={(status) => onStatusChange?.(task.id, status)}
              onDelete={() => onDelete?.(task.id)}
            />
          </div>
        ))}

        {/* Drop zone indicator when empty */}
        {dragEnabled && tasks.length === 0 && isDragOver && (
          <div className="flex flex-1 min-h-[120px] rounded-xl border-2 border-dashed border-primary/20 bg-primary/5 items-center justify-center text-sm font-medium text-primary opacity-70 animate-pulse">
            Drop here
          </div>
        )}

	        {/* Add step button */}
	        {onNewTask && (
	          <button
	            onClick={onNewTask}
	            className="group mt-auto flex w-full items-center gap-2 rounded-xl border border-dashed border-border p-2 text-[13px] text-foreground-muted transition-all hover:border-primary hover:bg-primary-subtle hover:text-primary"
	          >
	            <Plus className="h-4 w-4" />
	            Create new step
	          </button>
	        )}
      </div>
    </div>
  );
}

function KanbanColumnSkeleton({ title, isMobile }: { title: string; isMobile: boolean }) {
  return (
    <div
      className={cn(
        "flex flex-col rounded-xl bg-background-subtle animate-pulse border border-border/60",
        isMobile ? "w-full" : "flex-1 min-w-[260px] sm:min-w-[280px] xl:min-w-[320px] h-[500px]"
      )}
    >
      <div className="flex items-center gap-2.5 p-[var(--density-card-pad)] border-b border-border">
        <div className="h-2 w-2 rounded-full bg-border" />
        <span className="text-sm font-semibold text-foreground opacity-50">{title}</span>
      </div>
    </div>
  );
}
