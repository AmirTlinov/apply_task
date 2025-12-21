/**
 * API response types matching Python intent API output
 * from core/desktop/devtools/interface/intent_api.py
 */

import type { Plan, PlanListItem, Task, TaskEvent, TaskListItem, Project, Step, TaskNode, StepPlan } from "./task";

/** Base API response structure */
export interface ApiResponse<T = unknown> {
  command: string;
  status: "OK" | "WARN" | "ERROR";
  message: string;
  timestamp: string;
  summary?: string;
  payload: T;
}

export interface Suggestion {
  action: string;
  target: string;
  reason: string;
  priority?: string;
  params?: Record<string, unknown>;
}

export interface AIError {
  code: string;
  message: string;
  recovery?: string;
}

/** Canonical AI intent response (matches intent_api.AIResponse.to_dict()). */
export interface AIResponse<T = unknown> {
  success: boolean;
  intent: string;
  result: T;
  summary?: string;
  state?: Record<string, unknown>;
  hints?: Array<Record<string, unknown>>;
  warnings: string[];
  context: Record<string, unknown>;
  suggestions: Suggestion[];
  meta: Record<string, unknown>;
  error: AIError | null;
  timestamp: string;
}

export interface ContextData {
  counts: { plans: number; tasks: number };
  by_status: { TODO: number; ACTIVE: number; DONE: number };
  plans?: PlanListItem[];
  tasks?: TaskListItem[];
  plans_pagination?: Pagination;
  tasks_pagination?: Pagination;
  filtered_counts?: { plans: number; tasks: number };
  filters_applied?: string[];
  subtree?: SubtreePayload;
  current_plan?: Plan;
  current_task?: Task;
}

export type MirrorStatus = "pending" | "in_progress" | "completed";

export interface MirrorItem {
  kind: "step" | "task";
  path?: string;
  id?: string;
  task_id?: string;
  title: string;
  status: MirrorStatus;
  progress: number;
  children_done: number;
  children_total: number;
  criteria_confirmed?: boolean;
  tests_confirmed?: boolean;
  criteria_auto_confirmed?: boolean;
  tests_auto_confirmed?: boolean;
  blocked?: boolean;
}

export interface MirrorScope {
  task_id: string;
  kind: "plan" | "task" | "step";
  path?: string;
}

export interface MirrorSummary {
  total: number;
  completed: number;
  in_progress: number;
  pending: number;
}

export interface MirrorData {
  scope: MirrorScope;
  items: MirrorItem[];
  summary: MirrorSummary;
}

export interface Pagination {
  cursor?: string | null;
  next_cursor?: string | null;
  total: number;
  count: number;
  limit: number;
}

export interface SubtreePayload {
  task_id: string;
  kind: "step" | "plan" | "task";
  path: string;
  node: Step | TaskNode | StepPlan;
}

export interface ResumeData {
  plan?: Plan;
  task?: Task;
  timeline?: TaskEvent[];
  checkpoint_status?: { pending: string[]; ready: string[] };
}

/** List command payload */
export interface ListPayload {
  tasks: TaskListItem[];
  total: number;
  filters_applied?: string[];
}

/** Show command payload */
export interface ShowPayload {
  task: Task;
}

/** Create command result */
export interface CreateResult {
  plan_id?: string;
  task_id?: string;
}

/** Storage intent result */
export interface StorageResult {
  tasks_dir: string;
  namespace: string;
  source: string;
  task_count: number;
}

/** History intent result */
export interface HistoryResult {
  events: TaskEvent[];
  total: number;
}

/** Batch operation */
export interface BatchOperation {
  intent: string;
  task?: string;
  path?: string;
  [key: string]: unknown;
}

/** Batch result */
export interface BatchResult {
  results: Array<{
    intent: string;
    success: boolean;
    result?: unknown;
    error?: string;
  }>;
  all_succeeded: boolean;
}

/** Projects list result */
export interface ProjectsResult {
  projects: Project[];
  current?: string;
}

/** JSON-RPC 2.0 request */
export interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: number | string;
  method: string;
  params?: Record<string, unknown>;
}

/** JSON-RPC 2.0 response */
export interface JsonRpcResponse<T = unknown> {
  jsonrpc: "2.0";
  id: number | string;
  result?: T;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

/** JSON-RPC 2.0 notification */
export interface JsonRpcNotification {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown>;
}
