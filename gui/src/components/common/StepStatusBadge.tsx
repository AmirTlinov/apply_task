import { cn } from "@/lib/utils";
import { Clock, PlayCircle, AlertCircle, CheckCircle2 } from "lucide-react";
import type { StepStatus } from "@/types/task";

interface StepStatusBadgeProps {
  status: StepStatus;
  size?: "sm" | "md";
  showLabel?: boolean;
  showIcon?: boolean;
}

const statusConfig: Record<
  StepStatus,
  {
    label: string;
    bgColor: string;
    textColor: string;
    icon: typeof Clock;
  }
> = {
  pending: {
    label: "Pending",
    bgColor: "bg-background-muted",
    textColor: "text-foreground-muted",
    icon: Clock,
  },
  in_progress: {
    label: "In Progress",
    bgColor: "bg-status-warn/10",
    textColor: "text-status-warn",
    icon: PlayCircle,
  },
  blocked: {
    label: "Blocked",
    bgColor: "bg-status-fail/10",
    textColor: "text-status-fail",
    icon: AlertCircle,
  },
  completed: {
    label: "Completed",
    bgColor: "bg-status-ok/10",
    textColor: "text-status-ok",
    icon: CheckCircle2,
  },
};

export function StepStatusBadge({
  status,
  size = "sm",
  showLabel = true,
  showIcon = true,
}: StepStatusBadgeProps) {
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
