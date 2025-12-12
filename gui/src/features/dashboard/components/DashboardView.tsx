/**
 * Dashboard View - Project metrics, charts, and health overview
 */

import {
  BarChart3,
  TrendingUp,
  CheckCircle2,
  Clock,
  AlertCircle,
  Target,
  Zap,
  Calendar,
} from "lucide-react";
import type { TaskListItem } from "@/types/task";
import { cn } from "@/lib/utils";

interface DashboardViewProps {
  tasks: TaskListItem[];
  projectName?: string;
  isLoading?: boolean;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: typeof BarChart3;
  iconClassName?: string;
  bgClassName?: string;
  trend?: { value: number; isUp: boolean };
}

function MetricCard({ title, value, subtitle, icon: Icon, iconClassName, bgClassName, trend }: MetricCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-background p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between">
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", bgClassName)}>
          <Icon className={cn("h-5 w-5", iconClassName)} />
        </div>
        {trend && (
          <div className={cn(
            "flex items-center gap-1 text-xs font-medium",
            trend.isUp ? "text-status-ok" : "text-status-fail"
          )}>
            <TrendingUp className={cn("h-3.5 w-3.5", !trend.isUp && "rotate-180")} />
            {trend.value}%
          </div>
        )}
      </div>

      <div>
        <div className="text-2xl font-bold text-foreground tabular-nums tracking-tight">
          {value}
        </div>
        <div className="text-sm text-foreground-muted font-medium">{title}</div>
        {subtitle && (
          <div className="mt-1 text-[11px] text-foreground-subtle">
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
}

interface ProgressBarProps {
  label: string;
  value: number;
  total: number;
  colorClass: string;
}

function ProgressBar({ label, value, total, colorClass }: ProgressBarProps) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-foreground-muted">{label}</span>
        <span className="text-xs font-medium text-foreground tabular-nums">
          {value} / {total}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/50">
        <div
          className={cn("h-full rounded-full transition-all duration-500", colorClass)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export function DashboardView({ tasks, projectName, isLoading = false }: DashboardViewProps) {
  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Calculate metrics
  const total = tasks.length;
  const done = tasks.filter((t) => t.status === "DONE").length;
  const active = tasks.filter((t) => t.status === "ACTIVE").length;
  const todo = tasks.filter((t) => t.status === "TODO").length;

  const overallProgress = total > 0 ? Math.round((done / total) * 100) : 0;

  // Group by tags
  const tagCounts = new Map<string, number>();
  tasks.forEach((task) => {
    task.tags?.forEach((tag) => {
      tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
    });
  });
  const topTags = Array.from(tagCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div className="flex flex-1 flex-col gap-6 overflow-y-auto p-6 scrollbar-thin">
      {/* Header */}
      <div>
        <h2 className="mb-1 text-xl font-semibold text-foreground tracking-tight">
          {projectName || "Project"} Overview
        </h2>
        <p className="text-sm text-foreground-muted">
          Track your project progress and performance metrics
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Tasks"
          value={total}
          subtitle="All project tasks"
          icon={Target}
          iconClassName="text-primary"
          bgClassName="bg-primary/10"
        />
        <MetricCard
          title="DONE"
          value={done}
          subtitle={`${overallProgress}% of total`}
          icon={CheckCircle2}
          iconClassName="text-status-ok"
          bgClassName="bg-status-ok/10"
        />
        <MetricCard
          title="ACTIVE"
          value={active}
          subtitle="Currently active"
          icon={Clock}
          iconClassName="text-primary"
          bgClassName="bg-primary/10"
        />
        <MetricCard
          title="TODO"
          value={todo}
          subtitle="Not started"
          icon={AlertCircle}
          iconClassName="text-foreground-muted"
          bgClassName="bg-muted"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Progress Overview */}
        <div className="rounded-xl border border-border bg-background p-5 hover:shadow-sm transition-shadow">
          <div className="mb-5 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">
              Progress Overview
            </h3>
          </div>

          <div className="flex flex-col gap-4">
            <ProgressBar
              label="DONE"
              value={done}
              total={total}
              colorClass="bg-status-done"
            />
            <ProgressBar
              label="ACTIVE"
              value={active}
              total={total}
              colorClass="bg-primary"
            />
            <ProgressBar
              label="TODO"
              value={todo}
              total={total}
              colorClass="bg-foreground-subtle"
            />
          </div>

          {/* Overall progress ring */}
          <div className="mt-6 flex items-center gap-4 rounded-lg bg-muted/30 p-4">
            <div
              className="flex h-16 w-16 items-center justify-center rounded-full bg-background"
              style={{
                background: `conic-gradient(hsl(var(--primary)) ${overallProgress * 3.6}deg, hsl(var(--background-muted)) 0deg)`
              }}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-background text-sm font-bold text-foreground">
                {overallProgress}%
              </div>
            </div>

            <div>
              <div className="text-sm font-medium text-foreground">
                Overall Progress
              </div>
              <div className="text-xs text-foreground-muted">
                {done} of {total} tasks completed
              </div>
            </div>
          </div>
        </div>

        {/* Tags Distribution */}
        <div className="rounded-xl border border-border bg-background p-5 hover:shadow-sm transition-shadow">
          <div className="mb-5 flex items-center gap-2">
            <Zap className="h-4 w-4 text-status-warn" />
            <h3 className="text-sm font-semibold text-foreground">
              Top Tags
            </h3>
          </div>

          {topTags.length > 0 ? (
            <div className="flex flex-col gap-3">
              {topTags.map(([tag, count]) => (
                <div
                  key={tag}
                  className="flex items-center justify-between rounded-lg bg-muted/40 px-3 py-2.5 transition-colors hover:bg-muted/60"
                >
                  <span className="text-sm font-medium text-foreground-muted">
                    #{tag}
                  </span>
                  <span className="text-sm font-medium text-foreground tabular-nums">
                    {count} tasks
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex h-40 items-center justify-center text-sm text-foreground-muted">
              No tags used yet
            </div>
          )}
        </div>
      </div>

      {/* Weekly Activity - Based on real task updated_at dates */}
      <WeeklyActivityChart tasks={tasks} />
    </div>
  );
}

// Calculate real weekly activity from task updated_at dates
function getWeeklyActivity(tasks: TaskListItem[]): Map<number, number> {
  const activity = new Map<number, number>();
  const now = new Date();
  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - now.getDay() + 1); // Monday
  startOfWeek.setHours(0, 0, 0, 0);

  // Initialize all days to 0
  for (let i = 0; i < 7; i++) {
    activity.set(i, 0);
  }

  // Count tasks updated this week
  tasks.forEach((task) => {
    if (!task.updated_at) return;
    const updatedDate = new Date(task.updated_at);
    if (updatedDate >= startOfWeek) {
      const dayOfWeek = (updatedDate.getDay() + 6) % 7; // 0=Mon, 6=Sun
      activity.set(dayOfWeek, (activity.get(dayOfWeek) || 0) + 1);
    }
  });

  return activity;
}

interface WeeklyActivityChartProps {
  tasks: TaskListItem[];
}

function WeeklyActivityChart({ tasks }: WeeklyActivityChartProps) {
  const activity = getWeeklyActivity(tasks);
  const maxActivity = Math.max(...Array.from(activity.values()), 1);
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const today = (new Date().getDay() + 6) % 7; // 0=Mon, 6=Sun

  return (
    <div className="rounded-xl border border-border bg-background p-5 hover:shadow-sm transition-shadow">
      <div className="mb-4 flex items-center gap-2">
        <Calendar className="h-4 w-4 text-foreground-muted" />
        <h3 className="text-sm font-semibold text-foreground">
          This Week's Activity
        </h3>
      </div>

      <div className="grid grid-cols-7 gap-2">
        {days.map((day, i) => {
          const count = activity.get(i) || 0;
          const intensity = count > 0 ? 0.2 + (count / maxActivity) * 0.6 : 0;
          const isToday = i === today;

          return (
            <div
              key={day}
              className="flex flex-col items-center gap-2"
            >
              <span className={cn(
                "text-[10px] font-medium uppercase tracking-wider",
                isToday ? "text-primary" : "text-foreground-muted"
              )}>
                {day}
              </span>
              <div
                className={cn(
                  "flex h-9 w-full items-center justify-center rounded-md border text-xs font-semibold transition-all",
                  isToday ? "border-primary shadow-sm" : "border-transparent",
                  count > 0 ? "text-primary-foreground" : "bg-muted text-foreground-subtle"
                )}
                style={{
                  backgroundColor: count > 0 ? `rgba(59, 130, 246, ${intensity})` : undefined,
                  color: count > 0 ? 'white' : undefined
                }}
              >
                {count > 0 ? count : "-"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-6 animate-pulse">
      <div>
        <div className="mb-2 h-6 w-32 rounded bg-muted" />
        <div className="h-4 w-64 rounded bg-muted/50" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 rounded-xl bg-muted/30" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="h-64 rounded-xl bg-muted/30" />
        <div className="h-64 rounded-xl bg-muted/30" />
      </div>
    </div>
  );
}
