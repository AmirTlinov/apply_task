import { TaskDetailView } from "@/features/tasks/components/TaskDetailModal";
import { useUIStore } from "@/stores/uiStore";

export function TaskDetailSidePanel() {
  const detailPanel = useUIStore((s) => s.detailPanel);
  const closeDetailPanel = useUIStore((s) => s.closeDetailPanel);
  const setDetailSubtaskPath = useUIStore((s) => s.setDetailSubtaskPath);

  if (!detailPanel) return null;

  return (
    <aside className="hidden h-full shrink-0 border-l border-border bg-background md:block w-[min(500px,40vw)]">
      <TaskDetailView
        taskId={detailPanel.taskId}
        domain={detailPanel.domain}
        namespace={detailPanel.namespace}
        subtaskPath={detailPanel.subtaskPath}
        onSubtaskPathChange={(next) => setDetailSubtaskPath(next)}
        onClose={closeDetailPanel}
        variant="panel"
      />
    </aside>
  );
}
