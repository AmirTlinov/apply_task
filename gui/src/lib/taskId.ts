import type { TaskListItem } from "@/types/task";

export function getApiTaskIdFromUiTaskId(uiTaskId: string): string {
  const parts = uiTaskId.split("/");
  return parts[parts.length - 1] || uiTaskId;
}

export function getApiTaskId(task: TaskListItem): string {
  return getApiTaskIdFromUiTaskId(task.id);
}
