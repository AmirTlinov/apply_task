import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ListTodo } from "lucide-react";
import type { TaskListItem, TaskStatus } from "@/types/task";
import { EmptyState } from "@/components/common/EmptyState";
import { TaskListSkeleton } from "@/components/common/Skeleton";
import { ProgressBar } from "@/components/common/ProgressBar";
import { Badge } from "@/components/ui/badge";
import { TASK_STATUS_UI } from "@/lib/taskStatus";
import { getApiTaskId } from "@/lib/taskId";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/uiStore";

interface TaskTreeViewProps {
  tasks: TaskListItem[];
  isLoading?: boolean;
  searchQuery?: string;
  onNewTask?: () => void;
  onOpenTask: (taskId: string, subtaskPath?: string) => void;
}

type TaskKey = string;

function normalizeParent(value: unknown): string | null {
  const raw = typeof value === "string" ? value.trim() : "";
  if (!raw) return null;
  if (raw.toUpperCase() === "ROOT") return null;
  return raw;
}

function buildTaskKey(task: TaskListItem): TaskKey {
  const ns = task.namespace || "";
  return `${ns}|${getApiTaskId(task)}`;
}

function compareTasks(a: TaskListItem, b: TaskListItem): number {
  const aNs = a.namespace || "";
  const bNs = b.namespace || "";
  if (aNs !== bNs) return aNs.localeCompare(bNs);
  const aId = getApiTaskId(a);
  const bId = getApiTaskId(b);
  return aId.localeCompare(bId);
}

function matchesQuery(task: TaskListItem, queryLower: string): boolean {
  if (!queryLower) return true;
  return (
    task.title.toLowerCase().includes(queryLower) ||
    task.id.toLowerCase().includes(queryLower)
  );
}

export function TaskTreeView({
  tasks,
  isLoading = false,
  searchQuery,
  onNewTask,
  onOpenTask,
}: TaskTreeViewProps) {
  const detailPanel = useUIStore((s) => s.detailPanel);
  const [expandedKeys, setExpandedKeys] = useState<Set<TaskKey>>(new Set());
  const [childRevealByKey, setChildRevealByKey] = useState<Record<TaskKey, number>>({});
  const CHILD_REVEAL_STEP = 12;

  const tree = useMemo(() => {
    const tasksByKey = new Map<TaskKey, TaskListItem>();
    const parentByKey = new Map<TaskKey, TaskKey | null>();
    const childrenByKey = new Map<TaskKey, TaskKey[]>();

    for (const task of tasks) {
      tasksByKey.set(buildTaskKey(task), task);
    }

    for (const [key, task] of tasksByKey.entries()) {
      const parentId = normalizeParent(task.parent);
      const selfId = getApiTaskId(task);
      if (!parentId || parentId === selfId) {
        parentByKey.set(key, null);
        continue;
      }

      const ns = task.namespace || "";
      const parentKey = `${ns}|${parentId}`;
      if (!tasksByKey.has(parentKey)) {
        parentByKey.set(key, null);
        continue;
      }
      parentByKey.set(key, parentKey);
      const children = childrenByKey.get(parentKey) || [];
      children.push(key);
      childrenByKey.set(parentKey, children);
    }

    // Sort children deterministically
    for (const [parentKey, childKeys] of childrenByKey.entries()) {
      childKeys.sort((a, b) => {
        const ta = tasksByKey.get(a);
        const tb = tasksByKey.get(b);
        if (!ta || !tb) return a.localeCompare(b);
        return compareTasks(ta, tb);
      });
      childrenByKey.set(parentKey, childKeys);
    }

    const rootKeys = Array.from(tasksByKey.keys())
      .filter((k) => (parentByKey.get(k) ?? null) === null)
      .sort((a, b) => {
        const ta = tasksByKey.get(a);
        const tb = tasksByKey.get(b);
        if (!ta || !tb) return a.localeCompare(b);
        return compareTasks(ta, tb);
      });

    return { tasksByKey, parentByKey, childrenByKey, rootKeys };
  }, [tasks]);

  const selectedKey = useMemo(() => {
    if (!detailPanel) return null;
    const match = tasks.find((t) => {
      if (detailPanel.namespace && t.namespace !== detailPanel.namespace) return false;
      return getApiTaskId(t) === detailPanel.taskId;
    });
    return match ? buildTaskKey(match) : null;
  }, [detailPanel, tasks]);

  const queryLower = (searchQuery || "").trim().toLowerCase();

  const visibleKeys = useMemo(() => {
    if (!queryLower) return null;

    const visible = new Set<TaskKey>();
    const visited = new Set<TaskKey>();

    const addAncestors = (key: TaskKey) => {
      let current: TaskKey | null = key;
      while (current) {
        if (visited.has(current)) break;
        visited.add(current);
        visible.add(current);
        current = tree.parentByKey.get(current) ?? null;
      }
    };

    for (const [key, task] of tree.tasksByKey.entries()) {
      if (matchesQuery(task, queryLower)) {
        addAncestors(key);
      }
    }

    return visible;
  }, [queryLower, tree.parentByKey, tree.tasksByKey]);

  const autoExpanded = useMemo(() => {
    const auto = new Set<TaskKey>();

    const addParents = (from: TaskKey | null) => {
      const visited = new Set<TaskKey>();
      let current = from;
      while (current) {
        const parent = tree.parentByKey.get(current) ?? null;
        if (!parent) break;
        if (visited.has(parent)) break;
        visited.add(parent);
        auto.add(parent);
        current = parent;
      }
    };

    addParents(selectedKey);

    if (visibleKeys) {
      // Expand all non-leaf nodes that are on visible paths so matches are discoverable.
      for (const key of visibleKeys) {
        const parent = tree.parentByKey.get(key) ?? null;
        if (parent) auto.add(parent);
      }
    }

    return auto;
  }, [selectedKey, tree.parentByKey, visibleKeys]);

  const effectiveExpanded = useMemo(() => {
    const next = new Set<TaskKey>(expandedKeys);
    for (const k of autoExpanded) next.add(k);
    return next;
  }, [expandedKeys, autoExpanded]);

  useEffect(() => {
    if (!selectedKey) return;
    window.setTimeout(() => {
      const el = document.querySelector<HTMLElement>(`[data-task-tree-key="${selectedKey}"]`);
      el?.scrollIntoView({ block: "nearest" });
    }, 30);
  }, [selectedKey]);

  const toggleExpanded = (key: TaskKey) => {
    setChildRevealByKey((prev) => {
      if (!(key in prev)) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const renderNode = (key: TaskKey, depth: number) => {
    if (visibleKeys && !visibleKeys.has(key)) return null;

    const task = tree.tasksByKey.get(key);
    if (!task) return null;

    const childKeys = tree.childrenByKey.get(key) || [];
    const visibleChildKeys = visibleKeys ? childKeys.filter((k) => visibleKeys.has(k)) : childKeys;
    const hasChildren = visibleChildKeys.length > 0;
    const isExpanded = effectiveExpanded.has(key);
    const isSelected = selectedKey === key;

    const statusUi = TASK_STATUS_UI[task.status as TaskStatus];
    const progressPct = Math.max(0, Math.min(100, Math.round(task.progress || 0)));
    const stepsCount = task.steps_count ?? 0;
    const completedSteps = task.steps?.reduce((acc, st) => acc + (st.completed ? 1 : 0), 0) ?? 0;

    const revealLimit = childRevealByKey[key] ?? CHILD_REVEAL_STEP;
    const revealedChildKeys = isExpanded ? visibleChildKeys.slice(0, revealLimit) : [];
    const remainingChildren = isExpanded ? Math.max(0, visibleChildKeys.length - revealedChildKeys.length) : 0;

    return (
      <div key={key} className="flex flex-col">
        <div
          data-task-tree-key={key}
          role="button"
          tabIndex={0}
          onClick={() => onOpenTask(task.id)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onOpenTask(task.id);
            }
          }}
          className={cn(
            "group flex cursor-pointer select-none items-center justify-between gap-3 rounded-lg border px-3 py-1.5 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            isSelected
              ? "border-primary/50 bg-primary/10"
              : "border-border bg-card hover:bg-background-subtle"
          )}
          style={{ paddingLeft: `${12 + depth * 18}px` }}
        >
          <div className="flex min-w-0 items-center gap-2">
            {hasChildren ? (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExpanded(key);
                }}
                className="flex h-6 w-6 items-center justify-center rounded-md text-foreground-muted hover:bg-background-hover"
                aria-label={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>
            ) : (
              <div className="h-6 w-6" />
            )}

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-md bg-background-muted px-2 py-0.5 font-mono text-[11px] font-medium text-foreground-muted tracking-wide">
                  {task.id}
                </span>
                <Badge
                  variant="outline"
                  className={cn(
                    "gap-1.5 border-transparent px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                    statusUi.classes.bg,
                    statusUi.classes.text
                  )}
                >
                  <span className={cn("h-1.5 w-1.5 rounded-full", statusUi.classes.dot)} />
                  {task.status}
                </Badge>
                {task.domain && (
                  <span className="max-w-[180px] truncate text-[11px] text-foreground-subtle">
                    {task.domain}
                  </span>
                )}
              </div>

              <div
                className="mt-1 block w-full min-w-0 truncate text-left text-sm font-semibold text-foreground"
                title={task.title}
              >
                {task.title}
              </div>
            </div>
          </div>

          <div className="hidden items-center gap-3 sm:flex">
            <ProgressBar value={progressPct} size="sm" />
            <span className="text-xs font-semibold tabular-nums text-foreground-muted">
              {completedSteps}/{stepsCount}
            </span>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="mt-1 flex flex-col gap-1">
            {revealedChildKeys.map((childKey) => renderNode(childKey, depth + 1))}
            {remainingChildren > 0 && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setChildRevealByKey((prev) => ({
                    ...prev,
                    [key]: (prev[key] ?? CHILD_REVEAL_STEP) + CHILD_REVEAL_STEP,
                  }));
                }}
                className={cn(
                  "flex items-center gap-2 rounded-lg border border-dashed px-3 py-2 text-left text-xs font-semibold text-foreground-muted transition-colors hover:bg-background-subtle",
                  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                )}
                style={{ paddingLeft: `${12 + (depth + 1) * 18 + 28}px` }}
              >
                <span>Show more</span>
                <span className="text-[11px] font-medium tabular-nums text-foreground-subtle">
                  ({remainingChildren} hidden)
                </span>
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-[var(--density-page-pad)]">
        <TaskListSkeleton count={6} />
      </div>
    );
  }

  if (tasks.length === 0 && !queryLower) {
    return (
      <div className="flex flex-1 items-center justify-center p-[var(--density-page-pad)]">
        <EmptyState variant="tasks" onAction={onNewTask} />
      </div>
    );
  }

  const rootsToRender = visibleKeys
    ? tree.rootKeys.filter((k) => visibleKeys.has(k))
    : tree.rootKeys;

  if (rootsToRender.length === 0 && queryLower) {
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
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground-muted">
        <ListTodo className="h-4 w-4" />
        <span>Tasks tree</span>
      </div>

      <div className="flex flex-col gap-2">
        {rootsToRender.map((key) => renderNode(key, 0))}
      </div>
    </div>
  );
}
