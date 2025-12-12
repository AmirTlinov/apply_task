import { useState } from "react";
import { CheckCircle2, Circle, ChevronRight, Check, Clock, Trash2 } from "lucide-react";
import type { TaskListItem, TaskStatus } from "@/types/task";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface TaskCardProps {
  task: TaskListItem;
  onClick?: () => void;
  onStatusChange?: (status: TaskStatus) => void;
  onDelete?: () => void;
  isSelected?: boolean;
}

const statusConfig: Record<TaskStatus, { badge: string; dot: string }> = {
  DONE: { badge: "outline", dot: "bg-status-done" },
  ACTIVE: { badge: "outline", dot: "bg-status-active" },
  TODO: { badge: "outline", dot: "bg-foreground/20" },
};

function formatRelativeTime(date: string): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString();
}

export function TaskCard({ task, onClick, onStatusChange, onDelete, isSelected = false }: TaskCardProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const config = statusConfig[task.status] || statusConfig.TODO;
  const progress = task.progress || 0;
  const allCompleted =
    task.completed_count === task.subtask_count && task.subtask_count > 0;

  const handleStatusChange = (e: React.MouseEvent, newStatus: TaskStatus) => {
    e.stopPropagation();
    if (task.status !== newStatus) {
      onStatusChange?.(newStatus);
    }
  };

  return (
    <>
      <div
        className={cn(
          "group relative flex flex-col rounded-xl border p-4 transition-all duration-200 outline-none",
          "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          isSelected
            ? "border-primary bg-primary-subtle shadow-[0_0_0_2px] shadow-primary"
            : "border-border bg-card hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
        )}
        onClick={onClick}
        tabIndex={0}
        role="button"
        aria-pressed={isSelected}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onClick?.();
          }
        }}
      >
        {/* Quick Actions - appear on hover OR focus-within */}
        {(onStatusChange || onDelete) && (
          <div className="absolute top-3 right-3 z-10 hidden gap-1 rounded-lg bg-background/95 p-1.5 shadow-md backdrop-blur-sm group-hover:flex group-focus-within:flex animate-in fade-in zoom-in-95 duration-200">
            {onStatusChange && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn("h-7 w-7", task.status === "DONE" && "bg-status-done text-status-done-foreground opacity-100 cursor-default")}
                  onClick={(e) => handleStatusChange(e, "DONE")}
                  disabled={task.status === "DONE"}
                  title="Mark DONE"
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn("h-7 w-7", task.status === "ACTIVE" && "bg-status-active text-status-active-foreground opacity-100 cursor-default")}
                  onClick={(e) => handleStatusChange(e, "ACTIVE")}
                  disabled={task.status === "ACTIVE"}
                  title="Mark ACTIVE"
                >
                  <Clock className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn("h-7 w-7", task.status === "TODO" && "bg-status-todo text-status-todo-foreground opacity-100 cursor-default")}
                  onClick={(e) => handleStatusChange(e, "TODO")}
                  disabled={task.status === "TODO"}
                  title="Mark TODO"
                >
                  <Circle className="h-4 w-4" />
                </Button>
              </>
            )}
            {onDelete && (
              <>
                <div className="mx-0.5 w-px bg-border/50" />
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-status-fail hover:bg-status-fail-subtle hover:text-status-fail"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowDeleteConfirm(true);
                  }}
                  title="Delete task"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        )}

        {/* Header: ID, Status, Updated */}
        <div className="mb-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* Task ID badge */}
            <span className="rounded-md bg-background-muted px-2 py-0.5 font-mono text-[11px] font-medium text-foreground-muted tracking-wide">
              {task.id}
            </span>

            {/* Status badge */}
            <Badge variant={config.badge as any} className="gap-1.5 px-2.5 py-0.5 text-[10px] uppercase tracking-wider">
              <span className={cn("h-1.5 w-1.5 rounded-full", config.dot)} />
              {task.status}
            </Badge>
          </div>

          {/* Timestamp */}
          {task.updated_at && (
            <span className="text-[11px] text-foreground-subtle group-hover:opacity-0 transition-opacity duration-200">
              {formatRelativeTime(task.updated_at)}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="mb-2.5 text-[15px] font-medium leading-relaxed text-foreground line-clamp-2 tracking-tight">
          {task.title}
        </h3>

        {/* Tags */}
        {task.tags && task.tags.length > 0 && (
          <div className="mb-3.5 flex flex-wrap gap-1.5">
            {task.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="mono" className="font-normal px-2 py-0.5 text-[11px]">
                #{tag}
              </Badge>
            ))}
            {task.tags.length > 3 && (
              <span className="px-1 text-[11px] text-foreground-subtle">
                +{task.tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Footer: Progress & Subtasks */}
        <div className="mt-auto flex items-center justify-between pt-1">
          <div className="flex flex-1 items-center gap-4">
            {/* Progress bar */}
            <div className="flex flex-1 max-w-[140px] items-center gap-2.5">
              <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-background-muted">
                <div
                  className={cn(
                    "h-full w-full flex-1 rounded-full transition-all duration-500 ease-out",
                    progress === 100 ? "bg-status-done" : "bg-primary"
                  )}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className={cn(
                "min-w-[36px] text-xs font-semibold tabular-nums",
                progress === 100 ? "text-status-done" : "text-foreground-muted"
              )}>
                {progress}%
              </span>
            </div>

            {/* Subtask count */}
            <div className={cn(
              "flex items-center gap-1.5 text-xs font-medium tabular-nums",
              allCompleted ? "text-status-done" : "text-foreground-muted"
            )}>
              {allCompleted ? (
                <CheckCircle2 className="h-3.5 w-3.5" />
              ) : (
                <Circle className="h-3.5 w-3.5 opacity-60" />
              )}
              <span>
                {task.completed_count}/{task.subtask_count}
              </span>
            </div>
          </div>

          {/* Domain badge */}
          {task.domain && (
            <span className="ml-3 max-w-[90px] truncate text-[11px] text-foreground-subtle">
              {task.domain}
            </span>
          )}

          {/* Animated arrow */}
          <ChevronRight className="ml-2 h-4 w-4 shrink-0 text-foreground-subtle opacity-0 transition-all duration-200 group-hover:translate-x-1 group-hover:opacity-100" />
        </div>
      </div>

      {onDelete && (
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          title={`Delete task "${task.title}"?`}
          description="This will permanently remove the task and all its subtasks."
          confirmLabel="Delete"
          cancelLabel="Cancel"
          danger
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={() => {
            onDelete();
            setShowDeleteConfirm(false);
          }}
        />
      )}
    </>
  );
}