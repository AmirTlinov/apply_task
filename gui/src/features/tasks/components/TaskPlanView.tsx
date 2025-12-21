import { CheckCircle2, ChevronRight, Circle, Route } from "lucide-react";
import type { PlanChecklist } from "@/types/task";
import { cn } from "@/lib/utils";

export type TaskPlanStepFilter = "ALL" | "DONE" | "ACTIVE" | "TODO";

interface TaskPlanViewProps {
  plan?: PlanChecklist | null;
  className?: string;
  title?: string;
  showHeader?: boolean;
  filter?: TaskPlanStepFilter;
}

export function TaskPlanView({
  plan,
  className,
  title = "Plan",
  showHeader = true,
  filter = "ALL",
}: TaskPlanViewProps) {
  const steps = plan?.steps ?? [];
  if (steps.length === 0) return null;

  const currentRaw = typeof plan?.current === "number" ? plan.current : 0;
  const current = Math.max(0, Math.min(currentRaw, steps.length));
  const hasActiveStep = current < steps.length;
  const normalizedFilter: TaskPlanStepFilter = filter ?? "ALL";

  const matchesFilter = (state: "done" | "current" | "todo") => {
    if (normalizedFilter === "ALL") return true;
    if (normalizedFilter === "DONE") return state === "done";
    if (normalizedFilter === "ACTIVE") return state === "current";
    if (normalizedFilter === "TODO") return state === "todo";
    return true;
  };

  const hasVisibleSteps = steps.some((_step, idx) => {
    const state: "done" | "current" | "todo" =
      idx < current ? "done" : idx === current && hasActiveStep ? "current" : "todo";
    return matchesFilter(state);
  });

  return (
    <section className={cn("mb-6 rounded-lg border border-border bg-background-subtle p-4", className)}>
      {showHeader && (
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground-muted">
            <Route className="h-4 w-4 text-primary" />
            {title}
          </div>
          <div className="text-xs font-semibold tabular-nums text-foreground-muted">
            {current}/{steps.length}
          </div>
        </div>
      )}

      {hasVisibleSteps ? (
        <div className="flex flex-col gap-1.5">
          {steps.map((step, idx) => {
            const state: "done" | "current" | "todo" =
              idx < current ? "done" : idx === current && hasActiveStep ? "current" : "todo";
            if (!matchesFilter(state)) return null;

            const Icon =
              state === "done" ? CheckCircle2 : state === "current" ? ChevronRight : Circle;

            return (
              <div
                key={idx}
                className={cn(
                  "flex items-start gap-2 rounded-md px-2 py-1.5",
                  state === "current" && "bg-primary/10"
                )}
                data-state={state}
              >
                <div
                  className={cn(
                    "mt-[2px] flex h-5 w-5 items-center justify-center rounded-full",
                    state === "done"
                      ? "text-status-ok"
                      : state === "current"
                        ? "text-primary"
                        : "text-foreground-subtle"
                  )}
                  aria-hidden
                >
                  <Icon className="h-4 w-4" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-start gap-2">
                    <span className="mt-[2px] w-6 shrink-0 text-right font-mono text-[11px] text-foreground-subtle">
                      {idx + 1}.
                    </span>
                    <div
                      className={cn(
                        "min-w-0 whitespace-pre-wrap text-sm leading-relaxed",
                        state === "done" && "text-foreground-muted",
                        state === "current" && "font-medium text-foreground",
                        state === "todo" && "text-foreground"
                      )}
                    >
                      {step}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-background p-3 text-sm text-foreground-muted">
          No steps match this filter
        </div>
      )}
    </section>
  );
}
