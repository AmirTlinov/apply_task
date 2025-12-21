import { createRoute, useNavigate } from "@tanstack/react-router";
import { Route as rootRoute } from "./__root";
import { TaskDetailView } from "@/features/tasks/components/TaskDetailModal";

interface TaskRouteSearch {
  namespace?: string;
  domain?: string;
  subtask?: string;
}

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/task/$taskId",
  validateSearch: (search: Record<string, unknown>): TaskRouteSearch => {
    return {
      namespace: typeof search.namespace === "string" ? search.namespace : undefined,
      domain: typeof search.domain === "string" ? search.domain : undefined,
      subtask: typeof search.subtask === "string" ? search.subtask : undefined,
    };
  },
  component: TaskRoute,
});

function TaskRoute() {
  const navigate = useNavigate();
  const { taskId } = Route.useParams();
  const { namespace, domain, subtask } = Route.useSearch();

  const handleClose = () => {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    navigate({ to: "/" });
  };

  return (
    <div className="flex flex-1 w-full min-h-0 overflow-hidden bg-background">
      <TaskDetailView
        taskId={taskId}
        domain={domain}
        namespace={namespace}
        subtaskPath={subtask}
        onSubtaskPathChange={(next) => {
          navigate({
            to: "/task/$taskId",
            params: { taskId },
            search: {
              namespace,
              domain,
              subtask: next,
            },
            replace: true,
          });
        }}
        onClose={handleClose}
      />
    </div>
  );
}
