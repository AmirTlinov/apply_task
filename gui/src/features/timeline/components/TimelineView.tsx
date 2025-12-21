/**
 * Timeline View - Activity history and events chronology
 */

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  Plus,
  FileText,
  GitBranch,
  History,
  MessageSquare,
  Filter,
} from "lucide-react";
import type { TaskListItem } from "@/types/task";
import { cn } from "@/lib/utils";
import { getApiTaskIdFromUiTaskId } from "@/lib/taskId";
import type { OperationHistoryEntry, TaskTimelineEventRecord } from "@/lib/tauri";
import { getOperationHistory, getTaskTimelineEvents } from "@/lib/tauri";
import { useUIStore } from "@/stores/uiStore";

interface TimelineViewProps {
  tasks: TaskListItem[];
  isLoading?: boolean;
  selectedNamespace?: string | null;
  onTaskClick?: (taskId: string) => void;
}

type EventType =
  | "created"
  | "status"
  | "checkpoint"
  | "blocked"
  | "dependency"
  | "contract"
  | "plan"
  | "note"
  | "subtask"
  | "operation"
  | "other";

interface TimelineEvent {
  id: string;
  type: EventType;
  taskId: string;
  taskTitle: string;
  timestamp: Date;
  description?: string;
  actor?: string;
  target?: string;
  eventType?: string;
  data?: Record<string, unknown>;
}

const eventConfig: Record<EventType, { icon: typeof Clock; colorClass: string; label: string }> = {
  created: { icon: Plus, colorClass: "bg-primary text-primary-foreground", label: "Created" },
  status: { icon: Play, colorClass: "bg-status-warn text-white", label: "Status" },
  checkpoint: { icon: CheckCircle2, colorClass: "bg-status-done text-white", label: "Checkpoint" },
  blocked: { icon: AlertCircle, colorClass: "bg-status-fail text-white", label: "Blocked" },
  dependency: { icon: GitBranch, colorClass: "bg-muted text-muted-foreground", label: "Dependency" },
  contract: { icon: FileText, colorClass: "bg-muted text-muted-foreground", label: "Contract" },
  plan: { icon: GitBranch, colorClass: "bg-muted text-muted-foreground", label: "Plan" },
  note: { icon: MessageSquare, colorClass: "bg-muted text-muted-foreground", label: "Note" },
  subtask: { icon: GitBranch, colorClass: "bg-primary text-primary-foreground", label: "Step" },
  operation: { icon: History, colorClass: "bg-muted text-muted-foreground", label: "Operation" },
  other: { icon: Clock, colorClass: "bg-muted text-muted-foreground", label: "Other" },
};

function parseTimestamp(raw: string): Date | null {
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return null;
  return d;
}

function mapTaskEventType(eventType: string): EventType {
  switch (eventType) {
    case "created":
      return "created";
    case "status":
      return "status";
    case "checkpoint":
      return "checkpoint";
    case "blocked":
    case "unblocked":
      return "blocked";
    case "dependency_added":
    case "dependency_resolved":
      return "dependency";
    case "contract_updated":
      return "contract";
    case "plan_updated":
    case "plan_advanced":
      return "plan";
    case "comment":
      return "note";
    case "subtask_done":
      return "subtask";
    default:
      return "other";
  }
}

function describeTaskEvent(record: TaskTimelineEventRecord): string | undefined {
  const data = record.data || {};
  switch (record.event_type) {
    case "status": {
      const oldStatus = typeof data.old === "string" ? data.old : "";
      const newStatus = typeof data.new === "string" ? data.new : "";
      return oldStatus && newStatus ? `${oldStatus} → ${newStatus}` : undefined;
    }
    case "checkpoint": {
      const checkpoint = typeof data.checkpoint === "string" ? data.checkpoint : "";
      const note = typeof data.note === "string" ? data.note : "";
      const base = checkpoint ? `${checkpoint} confirmed` : "Checkpoint confirmed";
      return note ? `${base} — ${note}` : base;
    }
    case "blocked": {
      const reason = typeof data.reason === "string" ? data.reason : "";
      const blocker = typeof data.blocker_task === "string" ? data.blocker_task : "";
      const suffix = blocker ? ` (by ${blocker})` : "";
      return reason ? `${reason}${suffix}` : suffix || undefined;
    }
    case "unblocked":
      return "Unblocked";
    case "dependency_added": {
      const dep = typeof data.depends_on === "string" ? data.depends_on : "";
      return dep ? `Added ${dep}` : "Dependency added";
    }
    case "dependency_resolved": {
      const dep = typeof data.depends_on === "string" ? data.depends_on : "";
      return dep ? `Resolved ${dep}` : "Dependency resolved";
    }
    case "contract_updated": {
      const version = typeof data.version === "number" ? data.version : undefined;
      const note = typeof data.note === "string" ? data.note : "";
      const base = version ? `Contract v${version}` : "Contract updated";
      return note ? `${base} — ${note}` : base;
    }
    case "plan_updated": {
      const current = typeof data.current === "number" ? data.current : undefined;
      const steps = Array.isArray(data.steps) ? data.steps : undefined;
      const total = typeof data.steps_count === "number" ? data.steps_count : (steps ? steps.length : undefined);
      if (typeof current === "number" && typeof total === "number") return `${current}/${total}`;
      return "Plan updated";
    }
    case "plan_advanced": {
      const current = typeof data.current === "number" ? data.current : undefined;
      const total = typeof data.total === "number" ? data.total : undefined;
      if (typeof current === "number" && typeof total === "number") return `${current}/${total}`;
      return "Plan advanced";
    }
    case "comment": {
      const text = typeof data.text === "string" ? data.text : "";
      return text || undefined;
    }
    case "subtask_done":
      return record.target ? `${record.target} completed` : "Step completed";
    default:
      return undefined;
  }
}

function describeOperation(op: OperationHistoryEntry): string | undefined {
  const taskPart = op.task_id ? `(${op.task_id})` : "";
  const undone = op.undone ? " — undone" : "";
  return `${op.intent}${taskPart}${undone}`;
}

async function mapWithConcurrency<T, R>(items: T[], concurrency: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  if (items.length === 0) return [];
  const limit = Math.max(1, Math.min(concurrency, items.length));
  const results: R[] = new Array(items.length);
  let cursor = 0;

  const workers = Array.from({ length: limit }, async () => {
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const idx = cursor++;
      if (idx >= items.length) return;
      results[idx] = await fn(items[idx]);
    }
  });
  await Promise.all(workers);
  return results;
}

async function fetchTaskEvents(task: TaskListItem, options: { limit: number; namespace?: string }): Promise<TimelineEvent[]> {
  const taskId = task.id;
  const resp = await getTaskTimelineEvents({ taskId, limit: options.limit });
  if (!resp.success || !resp.events) return [];

  const events: TimelineEvent[] = [];
  for (const record of resp.events) {
    const ts = parseTimestamp(record.timestamp);
    if (!ts) continue;
    const type = mapTaskEventType(record.event_type);
    const eventId = `${task.id}:${record.event_type}:${record.timestamp}:${record.target || ""}`;
    events.push({
      id: eventId,
      type,
      taskId: task.id,
      taskTitle: task.title,
      timestamp: ts,
      description: describeTaskEvent(record),
      actor: record.actor,
      target: record.target,
      eventType: record.event_type,
      data: record.data,
    });
  }

  return events;
}

async function fetchOperationEvents(params: { limit: number; namespace: string; taskLookup?: Map<string, TaskListItem> }): Promise<TimelineEvent[]> {
  const resp = await getOperationHistory({ limit: params.limit });
  const history = resp.history;
  if (!resp.success || !history) return [];

  const events: TimelineEvent[] = [];
  for (const op of history.operations) {
    const rawTs = op.datetime || (typeof op.timestamp === "number" ? new Date(op.timestamp * 1000).toISOString() : "");
    if (!rawTs) continue;
    const ts = parseTimestamp(rawTs);
    if (!ts) continue;
    const known = op.task_id ? params.taskLookup?.get(op.task_id) : undefined;
    const taskId = op.task_id ? (known?.id || op.task_id) : "operation";
    events.push({
      id: `op:${op.id}`,
      type: "operation",
      taskId,
      taskTitle: known?.title || op.task_id || "Operation",
      timestamp: ts,
      description: describeOperation(op),
      actor: op.undone ? "undo" : "apply",
      eventType: op.intent,
    });
  }

  return events;
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function groupEventsByDate(events: TimelineEvent[]): Map<string, TimelineEvent[]> {
  const groups = new Map<string, TimelineEvent[]>();

  events.forEach((event) => {
    const dateKey = event.timestamp.toDateString();
    const existing = groups.get(dateKey) || [];
    groups.set(dateKey, [...existing, event]);
  });

  return groups;
}

const DEFAULT_VISIBLE_EVENTS = 250;
const LOAD_MORE_STEP = 250;

const TASKS_FETCH_LIMIT = 60;
const TASK_EVENTS_LIMIT = 40;
const OPS_LIMIT = 200;
const FETCH_CONCURRENCY = 6;

export function TimelineView({ tasks, isLoading = false, onTaskClick, selectedNamespace }: TimelineViewProps) {
  const [filter, setFilter] = useState<EventType | "all">("all");
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [visibleLimit, setVisibleLimit] = useState(DEFAULT_VISIBLE_EVENTS);
  const detailPanelTaskId = useUIStore((s) => s.detailPanel?.taskId);

  const tasksForFetch = useMemo(() => {
    const sorted = [...tasks].sort((a, b) => {
      const at = a.updated_at ? new Date(a.updated_at).getTime() : 0;
      const bt = b.updated_at ? new Date(b.updated_at).getTime() : 0;
      return bt - at;
    });
    return sorted.slice(0, TASKS_FETCH_LIMIT);
  }, [tasks]);

  const tasksSignature = useMemo(() => {
    return tasksForFetch
      .map((t) => `${t.id}@${t.updated_at || ""}`)
      .join("|");
  }, [tasksForFetch]);

  const timelineQuery = useQuery({
    queryKey: ["timeline", selectedNamespace ?? "all", tasksSignature],
    enabled: tasksForFetch.length > 0,
    queryFn: async () => {
      const taskEvents = await mapWithConcurrency(tasksForFetch, FETCH_CONCURRENCY, async (t) => {
        try {
          return await fetchTaskEvents(t, { limit: TASK_EVENTS_LIMIT });
        } catch {
          return [];
        }
      });
      const flatTaskEvents = taskEvents.flat();

      let opEvents: TimelineEvent[] = [];
      try {
        const taskLookup = new Map<string, TaskListItem>();
        for (const t of tasks) {
          taskLookup.set(t.id, t);
        }
        opEvents = await fetchOperationEvents({ limit: OPS_LIMIT, namespace: "", taskLookup });
      } catch {
        opEvents = [];
      }

      const merged = [...flatTaskEvents, ...opEvents].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
      return merged;
    },
  });

  const allEvents = timelineQuery.data || [];
  const filteredEvents = useMemo(() => {
    if (filter === "all") return allEvents;
    return allEvents.filter((e) => e.type === filter);
  }, [allEvents, filter]);
  const visibleEvents = useMemo(
    () => filteredEvents.slice(0, visibleLimit),
    [filteredEvents, visibleLimit]
  );
  const groupedEvents = useMemo(() => groupEventsByDate(visibleEvents), [visibleEvents]);
  const hiddenCount = filteredEvents.length - visibleEvents.length;

  if (isLoading || timelineQuery.isLoading) {
    return <TimelineSkeleton />;
  }

  if (allEvents.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 text-foreground-muted">
        <Clock className="h-12 w-12 opacity-50" />
        <div className="text-base font-medium">No activity yet</div>
        <div className="text-sm">Events will appear here as you work on tasks</div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Filter bar */}
      <div className="flex items-center gap-2 border-b border-border bg-background px-[var(--density-page-pad)] py-1.5">
        <Filter className="h-3.5 w-3.5 text-foreground-muted" />
        <span className="text-xs text-foreground-muted mr-1">Filter:</span>
        {(["all", "created", "status", "checkpoint", "plan", "contract", "note", "operation", "blocked"] as const).map((type) => (
          <button
            key={type}
            onClick={() => {
              setFilter(type);
              setVisibleLimit(DEFAULT_VISIBLE_EVENTS);
              setSelectedEventId(null);
            }}
            className={cn(
              "px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-150 ease-out",
              filter === type
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-foreground-muted hover:bg-muted/80"
            )}
          >
            {type === "all" ? "All" : eventConfig[type].label}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto p-[var(--density-page-pad)] scrollbar-thin">
        {Array.from(groupedEvents.entries()).map(([dateKey, events]) => (
          <div key={dateKey} className="mb-[var(--density-page-gap)] last:mb-0">
            {/* Date header */}
            <div className="mb-2 pl-6 text-xs font-semibold uppercase tracking-wider text-foreground-muted">
              {new Date(dateKey).toLocaleDateString("en-US", {
                weekday: "long",
                month: "short",
                day: "numeric",
              })}
            </div>

            {/* Events */}
            <div className="flex flex-col gap-0.5">
              {events.map((event, idx) => (
                <TimelineEventItem
                  key={event.id}
                  event={event}
                  isLast={idx === events.length - 1}
                  isSelected={selectedEventId === event.id}
                  isRelated={
                    detailPanelTaskId
                      ? getApiTaskIdFromUiTaskId(event.taskId) === detailPanelTaskId
                      : false
                  }
                  onTaskClick={onTaskClick}
                  onSelect={() => setSelectedEventId(event.id)}
                />
              ))}
            </div>
          </div>
        ))}

        {hiddenCount > 0 && (
          <div className="mt-[var(--density-page-gap)] flex justify-center">
            <button
              onClick={() => setVisibleLimit((prev) => prev + LOAD_MORE_STEP)}
              className="rounded-full border border-border bg-background px-3 py-1 text-xs font-medium text-foreground-muted transition-colors hover:bg-background-muted"
            >
              Show more ({hiddenCount} hidden)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

interface TimelineEventItemProps {
  event: TimelineEvent;
  isLast: boolean;
  isSelected: boolean;
  isRelated: boolean;
  onTaskClick?: (taskId: string) => void;
  onSelect?: () => void;
}

function TimelineEventItem({ event, isLast, isSelected, isRelated, onTaskClick, onSelect }: TimelineEventItemProps) {
  const config = eventConfig[event.type];
  const Icon = config.icon;
  const apiTaskId = getApiTaskIdFromUiTaskId(event.taskId);
  const isTaskLike = /^TASK-\d+$/.test(apiTaskId);

  return (
    <div
      onClick={() => {
        onSelect?.();
        if (isTaskLike) {
          onTaskClick?.(event.taskId);
        }
      }}
      className={cn(
        "group relative flex gap-3 rounded-lg px-2 py-1 transition-all duration-200",
        onTaskClick && isTaskLike ? "cursor-pointer hover:bg-muted/50" : "cursor-default",
        isSelected
          ? "bg-primary/10 ring-1 ring-primary/20"
          : isRelated
            ? "bg-primary/5"
            : undefined
      )}
    >
      {/* Timeline line */}
      {!isLast && (
        <div className="absolute left-[17px] top-6 bottom-[-2px] w-[2px] bg-border" />
      )}

      {/* Icon */}
      <div className={cn(
        "flex h-5 w-5 shrink-0 items-center justify-center rounded-full z-10",
        config.colorClass
      )}>
        <Icon className="h-2.5 w-2.5" />
      </div>

      {/* Content */}
      <div className="flex min-w-0 flex-1 flex-col pb-1.5">
        <div className="mb-1 flex items-baseline gap-2">
          <span className="text-sm font-medium text-foreground">
            {config.label}
          </span>
          <span className="text-xs text-foreground-muted">
            {formatRelativeTime(event.timestamp)}
          </span>
        </div>

        <div className="flex min-w-0 items-center gap-1.5 text-sm text-foreground-muted">
          <FileText className="h-3 w-3" />
          <span
            title={event.taskId}
            className="max-w-[160px] truncate rounded bg-muted px-1.5 py-px text-[11px] font-mono"
          >
            {event.taskId}
          </span>
          <span className="min-w-0 flex-1 line-clamp-1">{event.taskTitle}</span>
        </div>

        {event.description && (
          <div className="mt-1 text-xs text-foreground-subtle italic">
            {event.description}
          </div>
        )}

        {(event.actor || event.target || event.eventType) && (
          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-foreground-subtle">
            {event.actor && (
              <span className="rounded bg-background-muted px-1.5 py-px font-mono">
                {event.actor}
              </span>
            )}
            {event.target && (
              <span className="rounded bg-background-muted px-1.5 py-px font-mono">
                {event.target}
              </span>
            )}
            {event.eventType && (
              <span className="rounded bg-muted px-1.5 py-px font-mono">
                {event.eventType}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TimelineSkeleton() {
  return (
    <div className="flex flex-col gap-[var(--density-page-gap)] p-[var(--density-page-pad)] animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-3">
          <div className="h-5 w-5 rounded-full bg-muted" />
          <div className="flex-1">
            <div className="mb-2 h-3.5 w-32 rounded bg-muted" />
            <div className="h-3 w-3/4 rounded bg-muted/50" />
          </div>
        </div>
      ))}
    </div>
  );
}
