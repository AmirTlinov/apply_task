import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number;
  max?: number;
  size?: "sm" | "md";
  showLabel?: boolean;
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  size = "md",
  showLabel = false,
  className,
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  // Color based on progress
  const getProgressColor = (pct: number) => {
    if (pct >= 100) return "bg-status-ok";
    if (pct >= 50) return "bg-status-warn";
    return "bg-foreground/30";
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "flex-1 overflow-hidden rounded-full bg-background-muted",
          size === "sm" ? "h-1" : "h-1.5"
        )}
      >
        <div
          className={cn(
            "h-full rounded-full transition-[width] duration-300 ease-out",
            getProgressColor(percentage)
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-medium tabular-nums text-foreground-muted">
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  );
}
