import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listTasks, getStorage, updateTaskStatus as apiUpdateTaskStatus, deleteTask as apiDeleteTask } from "@/lib/tauri";
import type { TaskListItem, TaskStatus, Namespace, StorageInfo } from "@/types/task";
import { toast } from "@/components/common/toast";
import { getApiTaskIdFromUiTaskId } from "@/lib/taskId";

interface UseTasksResult {
  tasks: TaskListItem[];
  isLoading: boolean;
  error: string | null;
  projectName: string | null;
  projectPath: string | null;
  namespaces: Namespace[];
  refresh: () => Promise<void>;
  updateTaskStatus: (taskId: string, newStatus: TaskStatus) => void;
  deleteTask: (taskId: string) => void;
}

interface UseTasksParams {
  domain?: string;
  status?: string;
  namespace?: string | null;
  allNamespaces?: boolean;
}

export function useTasks(params?: UseTasksParams): UseTasksResult {
  const queryClient = useQueryClient();
  const queryKey = ["tasks", params?.domain, params?.status, params?.namespace, params?.allNamespaces];

  // Tasks Query
  const tasksQuery = useQuery({
    queryKey,
    queryFn: async () => {
      const response = await listTasks({
        domain: params?.domain,
        status: params?.status,
        compact: true,
      });
      if (!response.success) {
        throw new Error(response.error || "Failed to load tasks");
      }
      return response.tasks as TaskListItem[];
      },
  });

  // Storage Query
  const storageQuery = useQuery({
    queryKey: ["storage"],
    queryFn: async () => {
      const response = await getStorage();
      if (!response.success) {
        throw new Error(response.error || "Failed to load storage info");
      }
      if (!response.storage) {
        throw new Error("Storage response missing payload");
      }
      return response.storage as StorageInfo;
    },
  });

  // Mutations
  const updateStatusMutation = useMutation({
    mutationFn: async ({ taskId, newStatus }: { taskId: string; newStatus: TaskStatus }) => {
      const actualTaskId = getApiTaskIdFromUiTaskId(taskId);
      const response = await apiUpdateTaskStatus(actualTaskId, newStatus);
      if (!response.success) throw new Error(response.error);
      return response;
    },
    onMutate: async ({ taskId, newStatus }) => {
      await queryClient.cancelQueries({ queryKey });
      const previousTasks = queryClient.getQueryData<TaskListItem[]>(queryKey);

      if (previousTasks) {
        queryClient.setQueryData<TaskListItem[]>(queryKey, (old) =>
          old?.map((task) =>
            task.id === taskId
              ? {
                ...task,
                status: newStatus,
                updated_at: new Date().toISOString(),
              }
              : task
          )
        );
      }
      return { previousTasks };
    },
    onError: (err, _newTodo, context) => {
      if (context?.previousTasks) {
        queryClient.setQueryData(queryKey, context.previousTasks);
      }
      toast.error(err instanceof Error ? err.message : "Failed to update task status");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

	  const deleteMutation = useMutation({
	    mutationFn: async (taskId: string) => {
      const actualTaskId = getApiTaskIdFromUiTaskId(taskId);
      const response = await apiDeleteTask(actualTaskId);
      if (!response.success) throw new Error(response.error);
	      return response;
	    },
	    onSuccess: () => {
      toast.success("Task deleted");
	    },
	    onMutate: async (taskId) => {
      await queryClient.cancelQueries({ queryKey });
      const previousTasks = queryClient.getQueryData<TaskListItem[]>(queryKey);

      if (previousTasks) {
        queryClient.setQueryData<TaskListItem[]>(queryKey, (old) =>
          old?.filter((task) => task.id !== taskId)
        );
      }
      return { previousTasks };
    },
    onError: (err, _newTodo, context) => {
      if (context?.previousTasks) {
        queryClient.setQueryData(queryKey, context.previousTasks);
      }
      toast.error(err instanceof Error ? err.message : "Failed to delete task");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    tasks: tasksQuery.data || [],
    isLoading: tasksQuery.isLoading || storageQuery.isLoading,
    error: (tasksQuery.error as Error)?.message || (storageQuery.error as Error)?.message || null,
    projectName: storageQuery.data?.current_namespace || null,
    projectPath: storageQuery.data?.current_storage || null,
    namespaces: storageQuery.data?.namespaces || [],
    refresh: async () => {
      await Promise.all([tasksQuery.refetch(), storageQuery.refetch()]);
    },
    updateTaskStatus: (taskId, newStatus) => updateStatusMutation.mutate({ taskId, newStatus }),
    deleteTask: (taskId) => deleteMutation.mutate(taskId),
  };
}
