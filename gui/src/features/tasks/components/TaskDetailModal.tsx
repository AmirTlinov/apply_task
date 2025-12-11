/**
 * Task Detail Modal - Full task view with subtask tree and actions
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  X,
  ChevronRight,
  ChevronDown,
  CheckCircle2,
  Circle,
  AlertCircle,
  Clock,
  Tag,
  Calendar,
  ListTodo,
  FileText,
  PlayCircle,
  AlertTriangle,
  Check,
  Loader2,
  Edit3,
  Trash2,
  Copy,
  ArrowUpRight,
  FileText as NotesIcon,
} from "lucide-react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { SubtaskStatusBadge } from "@/components/common/SubtaskStatusBadge";
import { showTask, updateTaskStatus as apiUpdateTaskStatus, toggleSubtask } from "@/lib/tauri";
import type { Task, SubTask, TaskStatus } from "@/types/task";

interface TaskDetailModalProps {
  taskId: string | null;
  domain?: string;
  onClose: () => void;
  onDelete?: (taskId: string) => void;
}

const statusConfig: Record<TaskStatus, { icon: typeof CheckCircle2; color: string; label: string }> = {
  OK: { icon: CheckCircle2, color: "var(--color-status-ok)", label: "Completed" },
  WARN: { icon: Clock, color: "var(--color-status-warn)", label: "In Progress" },
  FAIL: { icon: AlertCircle, color: "var(--color-status-fail)", label: "Blocked" },
};

export function TaskDetailModal({
  taskId,
  domain,
  onClose,
  onDelete,
}: TaskDetailModalProps) {
  const queryClient = useQueryClient();
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set(["0", "1"]));

  const { data: task, isLoading, error } = useQuery({
    queryKey: ["task", taskId, domain],
    queryFn: async () => {
      const response = await showTask(taskId!, domain);
      if (!response.success || !response.task) {
        throw new Error(response.error || "Task not found");
      }
      return response.task;
    },
    enabled: !!taskId,
    // Auto-expand paths when task loads - handled via side effect in onSuccess if we want,
    // or just let state initialization handle it (which resets only on mount).
    // For now, we keep manual expansion state separate.
  });

  const updateStatusMutation = useMutation({
    mutationFn: async ({ taskId, status }: { taskId: string; status: TaskStatus }) => {
      const response = await apiUpdateTaskStatus(taskId, status);
      if (!response.success) throw new Error(response.error);
      return response;
    },
    onMutate: async ({ taskId, status }) => {
      await queryClient.cancelQueries({ queryKey: ["task", taskId] });
      const previousTask = queryClient.getQueryData<Task>(["task", taskId]);

      if (previousTask) {
        queryClient.setQueryData<Task>(["task", taskId], {
          ...previousTask,
          status,
        });
      }
      // Also update list view if present
      await queryClient.cancelQueries({ queryKey: ["tasks"] });
      // We can't easily update list view without scanning, but invalidation will handle it.

      return { previousTask };
    },
    onError: (_err, variables, context) => {
      if (context?.previousTask) {
        queryClient.setQueryData(["task", variables.taskId], context.previousTask);
      }
    },
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: ["task", variables.taskId] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  // Optimistic subtask toggle
  const handleSubtaskToggle = async (path: string, completed: boolean) => {
    if (!task) return;

    // Optimistic update
    const previousTask = queryClient.getQueryData<Task>(["task", task.id, domain]);

    queryClient.setQueryData<Task>(["task", task.id, domain], (old) => {
      if (!old) return old;
      // Deep copy to avoid mutating cache directly
      const updated = JSON.parse(JSON.stringify(old)) as Task;

      const indices = path.split(".").map(Number);
      let current: SubTask[] = updated.subtasks ?? [];

      // Navigate to the correct nesting level
      for (let i = 0; i < indices.length - 1; i++) {
        if (!current[indices[i]] || !current[indices[i]].subtasks) break;
        current = current[indices[i]].subtasks!;
      }

      // Update the specific subtask
      const targetIndex = indices[indices.length - 1];
      if (current[targetIndex]) {
        current[targetIndex].completed = completed;
      }
      return updated;
    });

    try {
      // Async backend call
      const response = await toggleSubtask(task.id, path, completed, domain);

      if (!response.success) {
        throw new Error(response.error || "Failed to update subtask");
      }

      // Invalidate to ensure consistency (optional, but good for sync)
      queryClient.invalidateQueries({ queryKey: ["task", task.id] });
      // Also update list view progress
      queryClient.invalidateQueries({ queryKey: ["tasks"] });

    } catch (err) {
      console.error("Failed to persist subtask toggle:", err);
      // Rollback on error
      if (previousTask) {
        queryClient.setQueryData(["task", task.id, domain], previousTask);
      }
      // Show error toast/alert (we'll just log for now)
    }
  };

  const handleStatusChange = (status: TaskStatus) => {
    if (!task) return;
    updateStatusMutation.mutate({ taskId: task.id, status });
  };

  const handleDelete = () => {
    if (!task) return;
    onDelete?.(task.id);
    onClose();
  };

  const handleToggleExpand = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  // Don't render if no taskId
  if (!taskId) return null;

  if (isLoading) {
    return (
      <ModalOverlay onClose={onClose}>
        <Loader2
          style={{
            width: "32px",
            height: "32px",
            color: "var(--color-primary)",
            animation: "spin 1s linear infinite",
            margin: "0 auto 16px",
          }}
        />
        <p style={{ color: "var(--color-foreground-muted)", fontSize: "14px" }}>
          Loading task...
        </p>
      </ModalOverlay>
    );
  }

  if (error || !task) {
    return (
      <ModalOverlay onClose={onClose}>
        <AlertCircle
          style={{
            width: "32px",
            height: "32px",
            color: "var(--color-status-fail)",
            margin: "0 auto 16px",
          }}
        />
        <p style={{ color: "var(--color-status-fail)", fontSize: "14px", marginBottom: "16px" }}>
          {(error as Error)?.message || "Task not found"}
        </p>
        <button
          onClick={onClose}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "1px solid var(--color-border)",
            backgroundColor: "transparent",
            color: "var(--color-foreground)",
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          Close
        </button>
      </ModalOverlay>
    );
  }

  const StatusIcon = statusConfig[task.status].icon;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "24px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "720px",
          maxHeight: "90vh",
          backgroundColor: "var(--color-background)",
          borderRadius: "16px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--color-border)",
            display: "flex",
            alignItems: "flex-start",
            gap: "16px",
          }}
        >
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <span
                style={{
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--color-foreground-muted)",
                  backgroundColor: "var(--color-background-muted)",
                  padding: "3px 8px",
                  borderRadius: "4px",
                }}
              >
                {task.id}
              </span>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 10px",
                  borderRadius: "999px",
                  backgroundColor: `${statusConfig[task.status].color}15`,
                }}
              >
                <StatusIcon
                  style={{ width: "14px", height: "14px", color: statusConfig[task.status].color }}
                />
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 500,
                    color: statusConfig[task.status].color,
                  }}
                >
                  {statusConfig[task.status].label}
                </span>
              </div>
            </div>
            <h2
              style={{
                fontSize: "18px",
                fontWeight: 600,
                color: "var(--color-foreground)",
                lineHeight: 1.4,
              }}
            >
              {task.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: "8px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "transparent",
              cursor: "pointer",
              color: "var(--color-foreground-muted)",
            }}
          >
            <X style={{ width: "20px", height: "20px" }} />
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
          {/* Description */}
          {task.description && (
            <div style={{ marginBottom: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <FileText style={{ width: "14px", height: "14px", color: "var(--color-foreground-muted)" }} />
                <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--color-foreground-muted)" }}>
                  Description
                </span>
              </div>
              <p style={{ fontSize: "14px", color: "var(--color-foreground)", lineHeight: 1.6 }}>
                {task.description}
              </p>
            </div>
          )}

          {/* Meta info */}
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "16px",
              marginBottom: "24px",
              padding: "16px",
              backgroundColor: "var(--color-background-subtle)",
              borderRadius: "10px",
            }}
          >
            {task.priority && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <AlertTriangle style={{ width: "14px", height: "14px", color: "var(--color-status-warn)" }} />
                <span style={{ fontSize: "13px", color: "var(--color-foreground-muted)" }}>
                  {task.priority}
                </span>
              </div>
            )}
            {task.domain && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Tag style={{ width: "14px", height: "14px", color: "var(--color-primary)" }} />
                <span style={{ fontSize: "13px", color: "var(--color-foreground-muted)" }}>
                  {task.domain}
                </span>
              </div>
            )}
            {task.updated_at && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Calendar style={{ width: "14px", height: "14px", color: "var(--color-foreground-subtle)" }} />
                <span style={{ fontSize: "13px", color: "var(--color-foreground-muted)" }}>
                  Updated {new Date(task.updated_at).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>

          {/* Tags */}
          {task.tags && task.tags.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "24px" }}>
              {task.tags.map((tag) => (
                <span
                  key={tag}
                  style={{
                    fontSize: "12px",
                    color: "var(--color-primary)",
                    backgroundColor: "var(--color-primary-subtle)",
                    padding: "4px 10px",
                    borderRadius: "999px",
                  }}
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* Subtasks */}
          {task.subtasks && task.subtasks.length > 0 && (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <ListTodo style={{ width: "14px", height: "14px", color: "var(--color-foreground-muted)" }} />
                <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--color-foreground-muted)" }}>
                  Subtasks ({task.subtasks.length})
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                {task.subtasks.map((subtask, index) => (
                  <SubtaskItem
                    key={index}
                    subtask={subtask}
                    path={String(index)}
                    depth={0}
                    expandedPaths={expandedPaths}
                    onToggleExpand={handleToggleExpand}
                    onToggleComplete={handleSubtaskToggle}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Tests */}
          {task.tests && task.tests.length > 0 && (
            <div style={{ marginTop: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <PlayCircle style={{ width: "14px", height: "14px", color: "var(--color-status-ok)" }} />
                <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--color-foreground-muted)" }}>
                  Tests
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {task.tests.map((test, i) => (
                  <code
                    key={i}
                    style={{
                      fontSize: "12px",
                      fontFamily: "var(--font-mono)",
                      color: "var(--color-foreground)",
                      backgroundColor: "var(--color-background-muted)",
                      padding: "8px 12px",
                      borderRadius: "6px",
                    }}
                  >
                    {test}
                  </code>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "16px 24px",
            borderTop: "1px solid var(--color-border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", gap: "8px" }}>
            {(["FAIL", "WARN", "OK"] as TaskStatus[]).map((status) => (
              <button
                key={status}
                onClick={() => handleStatusChange(status)}
                style={{
                  padding: "8px 14px",
                  borderRadius: "8px",
                  border: `1px solid ${task.status === status ? statusConfig[status].color : "var(--color-border)"}`,
                  backgroundColor: task.status === status ? `${statusConfig[status].color}15` : "transparent",
                  color: task.status === status ? statusConfig[status].color : "var(--color-foreground-muted)",
                  fontSize: "13px",
                  fontWeight: 500,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  transition: "all 150ms ease",
                }}
              >
                {statusConfig[status].label}
                {task.status === status && <Check style={{ width: "14px", height: "14px" }} />}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            {onDelete && (
              <button
                onClick={handleDelete}
                style={{
                  padding: "8px 14px",
                  borderRadius: "8px",
                  border: "1px solid var(--color-status-fail)",
                  backgroundColor: "transparent",
                  color: "var(--color-status-fail)",
                  fontSize: "13px",
                  fontWeight: 500,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  transition: "all 150ms ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "var(--color-status-fail)";
                  e.currentTarget.style.color = "white";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "var(--color-status-fail)";
                }}
              >
                <Trash2 style={{ width: "14px", height: "14px" }} />
                Delete
              </button>
            )}
            <button
              onClick={onClose}
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: "var(--color-primary)",
                color: "white",
                fontSize: "13px",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModalOverlay({ onClose, children }: { onClose: () => void; children: React.ReactNode }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "24px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "400px",
          backgroundColor: "var(--color-background)",
          borderRadius: "16px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          padding: "32px",
          textAlign: "center",
        }}
      >
        {children}
      </div>
    </div>
  );
}

interface SubtaskItemProps {
  subtask: SubTask;
  path: string;
  depth: number;
  expandedPaths: Set<string>;
  onToggleExpand: (path: string) => void;
  onToggleComplete: (path: string, completed: boolean) => void;
}

function SubtaskItem({
  subtask,
  path,
  depth,
  expandedPaths,
  onToggleExpand,
  onToggleComplete,
}: SubtaskItemProps) {
  const hasChildren = subtask.subtasks && subtask.subtasks.length > 0;
  const isExpanded = expandedPaths.has(path);
  const isBlocked = subtask.blockers && subtask.blockers.length > 0 && !subtask.completed;

  // Phase 1: Use blocked flag and block_reason if available
  const isBlockedPhase1 = subtask.blocked ?? isBlocked;
  const blockReason = subtask.block_reason || (subtask.blockers && subtask.blockers[0]);

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "8px",
          padding: "10px 12px",
          paddingLeft: `${12 + depth * 24}px`,
          borderRadius: "8px",
          backgroundColor: subtask.completed ? "var(--color-status-ok-subtle)" : "transparent",
          transition: "background-color 150ms ease",
        }}
        onMouseEnter={(e) => {
          if (!subtask.completed) {
            e.currentTarget.style.backgroundColor = "var(--color-background-subtle)";
          }
          const actionsEl = e.currentTarget.querySelector(".subtask-actions") as HTMLElement;
          if (actionsEl) actionsEl.style.opacity = "1";
        }}
        onMouseLeave={(e) => {
          if (!subtask.completed) {
            e.currentTarget.style.backgroundColor = "transparent";
          }
          const actionsEl = e.currentTarget.querySelector(".subtask-actions") as HTMLElement;
          if (actionsEl) actionsEl.style.opacity = "0";
        }}
      >
        {/* Expand/collapse button */}
        {hasChildren ? (
          <button
            onClick={() => onToggleExpand(path)}
            style={{
              padding: "2px",
              border: "none",
              backgroundColor: "transparent",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--color-foreground-muted)",
            }}
          >
            {isExpanded ? (
              <ChevronDown style={{ width: "16px", height: "16px" }} />
            ) : (
              <ChevronRight style={{ width: "16px", height: "16px" }} />
            )}
          </button>
        ) : (
          <div style={{ width: "20px" }} />
        )}

        {/* Checkbox */}
        <button
          onClick={() => onToggleComplete(path, !subtask.completed)}
          style={{
            padding: "2px",
            border: "none",
            backgroundColor: "transparent",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          {subtask.completed ? (
            <CheckCircle2
              style={{ width: "18px", height: "18px", color: "var(--color-status-ok)" }}
            />
          ) : isBlockedPhase1 ? (
            <AlertCircle
              style={{ width: "18px", height: "18px", color: "var(--color-status-fail)" }}
            />
          ) : (
            <Circle
              style={{ width: "18px", height: "18px", color: "var(--color-foreground-subtle)" }}
            />
          )}
        </button>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <div
              style={{
                fontSize: "13px",
                color: subtask.completed ? "var(--color-foreground-muted)" : "var(--color-foreground)",
                textDecoration: subtask.completed ? "line-through" : "none",
                lineHeight: 1.4,
                flex: 1,
              }}
            >
              {subtask.title}
            </div>

            {/* Phase 1: Computed status badge */}
            {subtask.computed_status && (
              <SubtaskStatusBadge status={subtask.computed_status} size="sm" showLabel={false} />
            )}

            {/* Phase 1: Progress notes count */}
            {subtask.progress_notes && subtask.progress_notes.length > 0 && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "3px",
                  fontSize: "11px",
                  color: "var(--color-primary)",
                  backgroundColor: "var(--color-primary-subtle)",
                  padding: "2px 6px",
                  borderRadius: "4px",
                }}
                title={`${subtask.progress_notes.length} progress note(s)`}
              >
                <NotesIcon style={{ width: "10px", height: "10px" }} />
                <span>{subtask.progress_notes.length}</span>
              </div>
            )}
          </div>

          {/* Phase 1: Started timestamp */}
          {subtask.started_at && (
            <div
              style={{
                fontSize: "11px",
                color: "var(--color-foreground-subtle)",
                marginTop: "2px",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <Clock style={{ width: "10px", height: "10px" }} />
              Started {new Date(subtask.started_at).toLocaleString()}
            </div>
          )}

          {/* Phase 1: Block reason */}
          {isBlockedPhase1 && blockReason && (
            <div
              style={{
                fontSize: "11px",
                color: "var(--color-status-fail)",
                marginTop: "4px",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <AlertCircle style={{ width: "12px", height: "12px" }} />
              {blockReason}
            </div>
          )}
        </div>

        {/* Actions */}
        <div
          className="subtask-actions"
          style={{
            opacity: 0,
            transition: "opacity 150ms ease",
          }}
        >
          <DropdownMenu
            trigger={
              <button
                style={{
                  padding: "4px",
                  border: "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  color: "var(--color-foreground-subtle)",
                  borderRadius: "4px",
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <ArrowUpRight style={{ width: "14px", height: "14px" }} />
              </button>
            }
            items={[
              {
                label: "Edit subtask",
                icon: <Edit3 style={{ width: "14px", height: "14px" }} />,
                onClick: () => console.log("Edit subtask", path),
              },
              {
                label: "Copy title",
                icon: <Copy style={{ width: "14px", height: "14px" }} />,
                onClick: () => navigator.clipboard.writeText(subtask.title),
              },
              { type: "separator" as const },
              {
                label: "Remove",
                icon: <Trash2 style={{ width: "14px", height: "14px" }} />,
                onClick: () => console.log("Remove subtask", path),
                danger: true,
              },
            ]}
          />
        </div>
      </div>

      {/* Nested subtasks */}
      {hasChildren && isExpanded && (
        <div>
          {subtask.subtasks!.map((child, index) => (
            <SubtaskItem
              key={index}
              subtask={child}
              path={`${path}.${index}`}
              depth={depth + 1}
              expandedPaths={expandedPaths}
              onToggleExpand={onToggleExpand}
              onToggleComplete={onToggleComplete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
