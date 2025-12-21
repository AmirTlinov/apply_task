import { createRoute, useNavigate } from "@tanstack/react-router";
import { Route as rootRoute } from "./__root";
import { PlanDetailView } from "@/features/plans/components/PlanDetailView";
import { useUIStore } from "@/stores/uiStore";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/plan/$planId",
  component: PlanRoute,
});

function PlanRoute() {
  const navigate = useNavigate();
  const { planId } = Route.useParams();
  const searchQuery = useUIStore((s) => s.searchQuery);
  const setNewTaskModalOpen = useUIStore((s) => s.setNewTaskModalOpen);

  const handleBack = () => {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    navigate({ to: "/plans" });
  };

  return (
    <div className="flex flex-1 w-full min-h-0 overflow-hidden bg-background">
      <PlanDetailView
        planId={planId}
        searchQuery={searchQuery}
        onBack={handleBack}
        onOpenTask={(taskId) => {
          navigate({ to: "/task/$taskId", params: { taskId } });
        }}
        onNewTask={() => setNewTaskModalOpen(true)}
      />
    </div>
  );
}
