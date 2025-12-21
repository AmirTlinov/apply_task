import { cn } from "@/lib/utils";

interface CheckpointMarksProps {
  criteriaOk?: boolean;
  testsOk?: boolean;
  className?: string;
  size?: "sm" | "md";
}

export function CheckpointMarks({
  criteriaOk = false,
  testsOk = false,
  className,
  size = "sm",
}: CheckpointMarksProps) {
  const dotSize = size === "sm" ? "h-2 w-2" : "h-2.5 w-2.5";
  const bracketSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <span className={cn("inline-flex items-center gap-1 font-mono text-foreground-subtle", bracketSize, className)}>
      <span>[</span>
      <span
        className={cn(
          "inline-block rounded-full",
          dotSize,
          criteriaOk ? "bg-status-ok" : "bg-foreground-muted/40"
        )}
      />
      <span
        className={cn(
          "inline-block rounded-full",
          dotSize,
          testsOk ? "bg-status-ok" : "bg-foreground-muted/40"
        )}
      />
      <span>]</span>
    </span>
  );
}
