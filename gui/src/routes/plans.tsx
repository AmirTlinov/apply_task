import { createRoute, useNavigate } from "@tanstack/react-router";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Route as rootRoute } from "./__root";
import { PlanTableView } from "@/features/plans/components/PlanTableView";
import { listPlans, listTasks } from "@/lib/tauri";
import { useUIStore } from "@/stores/uiStore";
import type { PlanListItem, TaskListItem } from "@/types/task";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/plans",
  component: PlansRoute,
});

function PlansRoute() {
  const navigate = useNavigate();
  const searchQuery = useUIStore((s) => s.searchQuery);
  const setNewTaskModalOpen = useUIStore((s) => s.setNewTaskModalOpen);

  const plansQuery = useQuery({
    queryKey: ["plans"],
    queryFn: async () => {
      const resp = await listPlans({ compact: true });
      if (!resp.success) throw new Error(resp.error || "Failed to load plans");
      return resp.plans as PlanListItem[];
    },
  });

  const tasksQuery = useQuery({
    queryKey: ["plan-counts"],
    queryFn: async () => {
      const resp = await listTasks({ compact: true });
      if (!resp.success) throw new Error(resp.error || "Failed to load tasks");
      return resp.tasks as TaskListItem[];
    },
  });

  const plans = plansQuery.data ?? [];
  const tasks = tasksQuery.data ?? [];
  const filteredPlans = useMemo(() => {
    if (!searchQuery) return plans;
    const query = searchQuery.toLowerCase();
    return plans.filter(
      (plan) =>
        plan.title.toLowerCase().includes(query) ||
        plan.id.toLowerCase().includes(query)
    );
  }, [plans, searchQuery]);

  const openPlan = (planId: string) => {
    navigate({ to: "/plan/$planId", params: { planId } });
  };

  return (
    <div className="flex flex-1 w-full min-h-0 flex-col bg-background">
      <PlanTableView
        plans={filteredPlans}
        tasks={tasks}
        isLoading={plansQuery.isLoading || tasksQuery.isLoading}
        onPlanClick={openPlan}
        onNewPlan={() => setNewTaskModalOpen(true)}
        searchQuery={searchQuery}
      />
    </div>
  );
}
