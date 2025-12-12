import { z } from "zod";
import { invoke } from "@tauri-apps/api/core";

// --- Domain Schemas ---

export const TaskStatusSchema = z.enum(["TODO", "ACTIVE", "DONE"]);
export type TaskStatus = z.infer<typeof TaskStatusSchema>;

export const TaskPrioritySchema = z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);
export type TaskPriority = z.infer<typeof TaskPrioritySchema>;

export const SubtaskSchema = z.object({
    title: z.string(),
    criteria: z.array(z.string()).default([]),
    tests: z.array(z.string()).default([]),
    blockers: z.array(z.string()).default([]),
});
export type Subtask = z.infer<typeof SubtaskSchema>;

export const TaskSchema = z.object({
    id: z.string(), // This is the UUID
    task_id: z.string(), // This is the ID-123 human readable ID
    title: z.string(),
    status: TaskStatusSchema,
    priority: TaskPrioritySchema.default("MEDIUM"),
    description: z.string().optional(),
    tags: z.array(z.string()).optional(),
    domain: z.string().optional(),
    namespace: z.string().optional(),
    subtasks: z.array(SubtaskSchema).optional(),
    created_at: z.string(),
    updated_at: z.string(),
    completed_at: z.string().nullable().optional(),

    // Computed/Frontend-only props from legacy type (might need review)
    progress: z.number().optional(),
    subtask_count: z.number().optional(),
    completed_count: z.number().optional().default(0),
});
export type Task = z.infer<typeof TaskSchema>;

export const NamespaceSchema = z.object({
    namespace: z.string(),
    path: z.string(),
    task_count: z.number(),
});
export type Namespace = z.infer<typeof NamespaceSchema>;

// --- API Response Schemas ---

export const TaskListResponseSchema = z.object({
    success: z.boolean(),
    tasks: z.array(TaskSchema), // Strict array of tasks
    total: z.number(),
});

export const StorageResponseSchema = z.object({
    success: z.boolean(),
    namespaces: z.array(NamespaceSchema),
});

export const GenericResponseSchema = z.object({
    success: z.boolean(),
    error: z.string().optional(),
    data: z.unknown().optional(),
});

// --- Typed API Client ---

const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

// Mock Data (Mutable for dev)
let MOCK_TASKS: Task[] = [
    {
        id: "mock-1",
        task_id: "TASK-1",
        title: "Setup Architecture",
        status: "DONE",
        priority: "HIGH",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        tags: ["infra", "arch"],
        subtasks: [],
        completed_count: 0,
        subtask_count: 0,
    },
    {
        id: "mock-2",
        task_id: "TASK-2",
        title: "Implement Router",
        status: "ACTIVE",
        priority: "CRITICAL",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        tags: ["ui", "feat"],
        subtasks: [],
        completed_count: 0,
        subtask_count: 0,
    },
];

export const client = {
    tasks: {
        list: async (
            status?: TaskStatus,
            namespace?: string,
            limit: number = 50,
            offset: number = 0
        ): Promise<z.infer<typeof TaskListResponseSchema>> => {
            if (!isTauri) {
                console.warn("⚠️ Using Mock Data for listTasks");
                return { success: true, tasks: MOCK_TASKS, total: MOCK_TASKS.length };
            }

            const raw = await invoke("tasks_list", { filter_status: status, namespace, limit, offset });
            return TaskListResponseSchema.parse(raw);
        },

        create: async (payload: unknown) => {
            if (!isTauri) {
                console.warn("⚠️ Using Mock Data for createTask");
                return { success: true };
            }
            return invoke("tasks_create", { payload });
        },

        updateStatus: async (taskId: string, status: TaskStatus, domain: string = "default", namespace?: string) => {
            if (!isTauri) {
                console.warn("⚠️ Using Mock Data for updateStatus", { taskId, status });
                MOCK_TASKS = MOCK_TASKS.map(t => t.id === taskId ? { ...t, status } : t);
                return { success: true };
            }
            return invoke("tasks_update_status", { taskId, status, domain, namespace });
        }
    },

    storage: {
        get: async (domain: string = "default") => {
            if (!isTauri) {
                return { success: true, namespaces: [{ namespace: "default", path: "/tmp", task_count: MOCK_TASKS.length }] };
            }
            const raw = await invoke("storage_get", { domain });
            return StorageResponseSchema.parse(raw);
        }
    }
};
