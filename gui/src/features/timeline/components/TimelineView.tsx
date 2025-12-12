/**
 * Timeline View - Activity history and events chronology
 */

import { useState } from "react";
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  Plus,
  FileText,
  GitBranch,
  MessageSquare,
  Filter,
} from "lucide-react";
import type { TaskListItem } from "@/types/task";
import { cn } from "@/lib/utils";

interface TimelineViewProps {
  tasks: TaskListItem[];
  isLoading?: boolean;
  onTaskClick?: (taskId: string) => void;
}

type EventType = "created" | "started" | "completed" | "blocked" | "comment" | "subtask";

interface TimelineEvent {
  id: string;
  type: EventType;
  taskId: string;
  taskTitle: string;
  timestamp: Date;
  description?: string;
}

const eventConfig: Record<EventType, { icon: typeof Clock; colorClass: string; label: string }> = {
  created: { icon: Plus, colorClass: "bg-primary text-primary-foreground", label: "Created" },
  started: { icon: Play, colorClass: "bg-status-warn text-white", label: "Started" },
  completed: { icon: CheckCircle2, colorClass: "bg-status-done text-white", label: "Completed" },
  blocked: { icon: AlertCircle, colorClass: "bg-status-fail text-white", label: "Blocked" },
  comment: { icon: MessageSquare, colorClass: "bg-muted text-muted-foreground", label: "Comment" },
  subtask: { icon: GitBranch, colorClass: "bg-primary text-primary-foreground", label: "Subtask" },
};

function generateEventsFromTasks(tasks: TaskListItem[]): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  tasks.forEach((task) => {
    const timestamp = task.updated_at ? new Date(task.updated_at) : null;
    if (!timestamp) return;

    const statusEventMap: Record<string, EventType> = {
      DONE: "completed",
      ACTIVE: "started",
      TODO: "created",
    };

    const eventType = statusEventMap[task.status] || "created";

    events.push({
      id: `${task.id}-${eventType}`,
      type: eventType,
      taskId: task.id,
      taskTitle: task.title,
      timestamp,
      description: task.status === "TODO" && task.progress && task.progress > 0
        ? "Task moved back to TODO"
        : undefined,
    });

    if (task.completed_count && task.completed_count > 0 && task.subtask_count && task.subtask_count > 0) {
      events.push({
        id: `${task.id}-subtask-progress`,
        type: "subtask",
        taskId: task.id,
        taskTitle: task.title,
        timestamp: new Date(timestamp.getTime() - 1000),
        description: `${task.completed_count} of ${task.subtask_count} subtasks completed`,
      });
    }
  });

  return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
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

export function TimelineView({ tasks, isLoading = false, onTaskClick }: TimelineViewProps) {
  const [filter, setFilter] = useState<EventType | "all">("all");

  if (isLoading) {
    return <TimelineSkeleton />;
  }

  const allEvents = generateEventsFromTasks(tasks);
  const filteredEvents = filter === "all" ? allEvents : allEvents.filter((e) => e.type === filter);
  const groupedEvents = groupEventsByDate(filteredEvents);

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
      <div className="flex items-center gap-2 border-b border-border bg-background px-6 py-4">
        <Filter className="h-3.5 w-3.5 text-foreground-muted" />
        <span className="text-xs text-foreground-muted mr-1">Filter:</span>
        {(["all", "created", "started", "completed", "blocked"] as const).map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium transition-all duration-150 ease-out",
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
      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
        {Array.from(groupedEvents.entries()).map(([dateKey, events]) => (
          <div key={dateKey} className="mb-8 last:mb-0">
            {/* Date header */}
            <div className="mb-4 pl-7 text-xs font-semibold uppercase tracking-wider text-foreground-muted">
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
                  onTaskClick={onTaskClick}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface TimelineEventItemProps {
  event: TimelineEvent;
  isLast: boolean;
  onTaskClick?: (taskId: string) => void;
}

function TimelineEventItem({ event, isLast, onTaskClick }: TimelineEventItemProps) {
  const config = eventConfig[event.type];
  const Icon = config.icon;

  return (
    <div
      onClick={() => onTaskClick?.(event.taskId)}
      className={cn(
        "group relative flex gap-3 rounded-lg px-2 py-1 transition-all duration-200",
        onTaskClick ? "cursor-pointer hover:bg-muted/50" : "cursor-default"
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
      <div className="flex flex-1 flex-col pb-4">
        <div className="mb-1 flex items-baseline gap-2">
          <span className="text-sm font-medium text-foreground">
            {config.label}
          </span>
          <span className="text-xs text-foreground-muted">
            {formatRelativeTime(event.timestamp)}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-sm text-foreground-muted">
          <FileText className="h-3 w-3" />
          <span className="rounded bg-muted px-1.5 py-px text-[11px] font-mono">
            {event.taskId}
          </span>
          <span className="line-clamp-1">{event.taskTitle}</span>
        </div>

        {event.description && (
          <div className="mt-1 text-xs text-foreground-subtle italic">
            {event.description}
          </div>
        )}
      </div>
    </div>
  );
}

function TimelineSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-6 animate-pulse">
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
