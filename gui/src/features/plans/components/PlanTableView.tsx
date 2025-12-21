import { useCallback, useEffect, useMemo, useState } from "react";
import type { PlanListItem, TaskListItem } from "@/types/task";
import { TaskListSkeleton } from "@/components/common/Skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { useKeyboardListNavigation } from "@/hooks/useKeyboardListNavigation";
import { CheckpointMarks } from "@/components/common/CheckpointMarks";
import { cn } from "@/lib/utils";
import { TASK_STATUS_UI } from "@/lib/taskStatus";

interface PlanTableViewProps {
  plans: PlanListItem[];
  tasks: TaskListItem[];
  onPlanClick?: (planId: string) => void;
  focusedPlanId?: string | null;
  onFocusChange?: (planId: string | null) => void;
  onNewPlan?: () => void;
  isLoading?: boolean;
  searchQuery?: string;
}

interface PlanCounts {
  total: number;
  done: number;
}

function computePlanCounts(tasks: TaskListItem[]): Map<string, PlanCounts> {
  const map = new Map<string, PlanCounts>();
  for (const task of tasks) {
    const parent = String(task.parent || "").trim();
    if (!parent.startsWith("PLAN-")) continue;
    const blocked = !!task.blocked;
    const progress = typeof task.progress === "number" ? task.progress : 0;
    let status = String(task.status_code || task.status || "").toUpperCase();
    if (progress >= 100 && !blocked) status = "DONE";
    const current = map.get(parent) ?? { total: 0, done: 0 };
    current.total += 1;
    if (status === "DONE") current.done += 1;
    map.set(parent, current);
  }
  return map;
}

export function PlanTableView({
  plans,
  tasks,
  onPlanClick,
  focusedPlanId,
  onFocusChange,
  onNewPlan,
  isLoading = false,
  searchQuery,
}: PlanTableViewProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const effectiveSelectedId = focusedPlanId ?? selectedId;

  const planCounts = useMemo(() => computePlanCounts(tasks), [tasks]);
  const planIds = useMemo(() => plans.map((p) => p.id), [plans]);

  const setActivePlanId = useCallback(
    (planId: string | null) => {
      setSelectedId(planId);
      onFocusChange?.(planId);
    },
    [onFocusChange]
  );

  useKeyboardListNavigation({
    enabled: plans.length > 0,
    itemIds: planIds,
    activeId: effectiveSelectedId,
    onActiveChange: setActivePlanId,
    onActivate: (planId) => {
      setActivePlanId(planId);
      onPlanClick?.(planId);
    },
  });

  useEffect(() => {
    if (!effectiveSelectedId) return;
    const el = document.querySelector<HTMLElement>(`[data-plan-id="${effectiveSelectedId}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [effectiveSelectedId]);

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-[var(--density-page-pad)]">
        <TaskListSkeleton count={6} />
      </div>
    );
  }

  if (plans.length === 0 && !searchQuery) {
    return (
      <div className="flex flex-1 items-center justify-center p-[var(--density-page-pad)]">
        <EmptyState variant="plans" onAction={onNewPlan} />
      </div>
    );
  }

  if (plans.length === 0 && searchQuery) {
    return (
      <div className="flex flex-1 items-center justify-center p-[var(--density-page-pad)]">
        <EmptyState
          variant="search"
          title="No matching plans"
          description={`No plans found for "${searchQuery}". Try a different search term.`}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-[var(--density-page-pad)]">
      <div className="rounded-xl border border-border bg-card">
        <div className="grid grid-cols-[44px_36px_1fr_80px_70px_70px] items-center gap-2 border-b border-border px-3 py-2 text-xs font-semibold uppercase tracking-wide text-foreground-muted">
          <span>#</span>
          <span>Status</span>
          <span>Plan</span>
          <span className="text-center">✓✓</span>
          <span className="text-center">%</span>
          <span className="text-center">Σ</span>
        </div>
        <div className="divide-y divide-border">
          {plans.map((plan, idx) => {
            const counts = planCounts.get(plan.id) ?? { total: 0, done: 0 };
            const progress =
              counts.total > 0 ? Math.round((counts.done / counts.total) * 100) : 0;
            const status =
              counts.total > 0 && counts.done === counts.total
                ? "DONE"
                : counts.done > 0
                  ? "ACTIVE"
                  : "TODO";
            const statusUi = TASK_STATUS_UI[status];
            const criteriaOk = !!plan.criteria_confirmed || !!plan.criteria_auto_confirmed;
            const testsOk = !!plan.tests_confirmed || !!plan.tests_auto_confirmed;
            const isSelected = effectiveSelectedId === plan.id;

            return (
              <div
                key={plan.id}
                data-plan-id={plan.id}
                role="button"
                tabIndex={0}
                onClick={() => {
                  setSelectedId(plan.id);
                  onFocusChange?.(plan.id);
                  onPlanClick?.(plan.id);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setSelectedId(plan.id);
                    onFocusChange?.(plan.id);
                    onPlanClick?.(plan.id);
                  }
                }}
                className={cn(
                  "grid grid-cols-[44px_36px_1fr_80px_70px_70px] items-center gap-2 px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                  isSelected ? "bg-primary/10" : "hover:bg-background-subtle"
                )}
              >
                <span className="text-xs font-mono text-foreground-subtle">{idx + 1}</span>
                <span className="flex items-center">
                  <span className={cn("h-2.5 w-2.5 rounded-full", statusUi.classes.dot)} />
                </span>
                <div className="flex min-w-0 flex-col gap-0.5">
                  <span className="truncate font-medium text-foreground" title={plan.title}>
                    {plan.title}
                  </span>
                  <span className="truncate text-xs text-foreground-subtle">{plan.id}</span>
                </div>
                <span className="flex justify-center">
                  <CheckpointMarks criteriaOk={criteriaOk} testsOk={testsOk} />
                </span>
                <span className="text-center text-xs font-semibold tabular-nums text-foreground-muted">
                  {progress}%
                </span>
                <span className="text-center text-xs font-semibold tabular-nums text-foreground-muted">
                  {counts.done}/{counts.total}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
