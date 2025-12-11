import { cn } from "@/lib/utils";
import { Clock, PlayCircle, AlertCircle, CheckCircle2 } from "lucide-react";
import type { SubtaskStatus } from "@/types/task";

interface SubtaskStatusBadgeProps {
  status: SubtaskStatus;
  size?: "sm" | "md";
  showLabel?: boolean;
  showIcon?: boolean;
}

const statusConfig: Record<
  SubtaskStatus,
  {
    label: string;
    bgColor: string;
    textColor: string;
    icon: typeof Clock;
  }
> = {
  pending: {
    label: "Pending",
    bgColor: "bg-[var(--color-foreground-subtle)]",
    textColor: "text-[var(--color-foreground-muted)]",
    icon: Clock,
  },
  in_progress: {
    label: "In Progress",
    bgColor: "bg-[var(--color-status-warn-subtle)]",
    textColor: "text-[var(--color-status-warn)]",
    icon: PlayCircle,
  },
  blocked: {
    label: "Blocked",
    bgColor: "bg-[var(--color-status-fail-subtle)]",
    textColor: "text-[var(--color-status-fail)]",
    icon: AlertCircle,
  },
  completed: {
    label: "Completed",
    bgColor: "bg-[var(--color-status-ok-subtle)]",
    textColor: "text-[var(--color-status-ok)]",
    icon: CheckCircle2,
  },
};

export function SubtaskStatusBadge({
  status,
  size = "sm",
  showLabel = true,
  showIcon = true,
}: SubtaskStatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        config.bgColor,
        config.textColor,
        size === "sm" ? "px-1.5 py-0.5 text-xs" : "px-2 py-1 text-xs"
      )}
    >
      {showIcon && (
        <Icon
          className={cn(
            size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5"
          )}
        />
      )}
      {showLabel && <span>{config.label}</span>}
    </span>
  );
}
