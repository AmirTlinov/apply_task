import type { TaskStatus } from "@/types/task";

export const TASK_STATUS_UI: Record<
  TaskStatus,
  {
    label: TaskStatus;
    colors: { text: string; bg: string; dot: string };
    classes: { bg: string; text: string; dot: string };
  }
> = {
  DONE: {
    label: "DONE",
    colors: {
      text: "hsl(var(--status-ok))",
      bg: "hsl(var(--status-ok) / 0.12)",
      dot: "hsl(var(--status-ok))",
    },
    classes: {
      bg: "bg-status-ok/10",
      text: "text-status-ok",
      dot: "bg-status-ok",
    },
  },
  ACTIVE: {
    label: "ACTIVE",
    colors: {
      text: "hsl(var(--status-active))",
      bg: "hsl(var(--status-active) / 0.12)",
      dot: "hsl(var(--status-active))",
    },
    classes: {
      bg: "bg-status-active/10",
      text: "text-status-active",
      dot: "bg-status-active",
    },
  },
  TODO: {
    label: "TODO",
    colors: {
      text: "hsl(var(--foreground))",
      bg: "hsl(var(--background-muted))",
      dot: "hsl(var(--foreground) / 0.35)",
    },
    classes: {
      bg: "bg-background-muted",
      text: "text-foreground",
      dot: "bg-foreground/30",
    },
  },
};

export function getTaskStatusLabel(status: TaskStatus): TaskStatus {
  return TASK_STATUS_UI[status].label;
}
