/**
 * Empty state component for when there's no data to display
 */

import { Plus, Search, FolderOpen, CheckCircle2, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";

type EmptyStateVariant = "plans" | "tasks" | "search" | "filtered" | "completed" | "default";

interface EmptyStateProps {
  variant?: EmptyStateVariant;
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const variantConfig: Record<
  EmptyStateVariant,
  {
    icon: React.ComponentType<{ style?: React.CSSProperties; className?: string }>;
    title: string;
    description: string;
    actionLabel?: string;
  }
> = {
  tasks: {
    icon: Inbox,
    title: "No tasks yet",
    description: "Create your first task to start tracking your work",
    actionLabel: "Create Task",
  },
  plans: {
    icon: Inbox,
    title: "No plans yet",
    description: "Create your first plan to structure the work",
    actionLabel: "Create Plan",
  },
  search: {
    icon: Search,
    title: "No results found",
    description: "Try adjusting your search or filter to find what you're looking for",
  },
  filtered: {
    icon: FolderOpen,
    title: "No matching tasks",
    description: "No tasks match your current filters. Try changing your selection.",
  },
  completed: {
    icon: CheckCircle2,
    title: "All done!",
    description: "You've completed all your tasks. Time to celebrate.",
  },
  default: {
    icon: Inbox,
    title: "Nothing here",
    description: "This section is empty",
  },
};

export function EmptyState({
  variant = "default",
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;
  const displayTitle = title ?? config.title;
  const displayDescription = description ?? config.description;
  const displayActionLabel = actionLabel ?? config.actionLabel;

  return (
    <div className="flex min-h-[260px] flex-col items-center justify-center p-[var(--density-page-pad)] text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-background-muted">
        <Icon className="h-8 w-8 text-foreground-subtle" />
      </div>

      <h3 className="mb-2 text-lg font-semibold tracking-tight text-foreground">
        {displayTitle}
      </h3>

      <p
        className={
          displayActionLabel
            ? "mb-6 max-w-[360px] text-sm leading-relaxed text-foreground-muted"
            : "max-w-[360px] text-sm leading-relaxed text-foreground-muted"
        }
      >
        {displayDescription}
      </p>

      {displayActionLabel && onAction && (
        <Button onClick={onAction} className="gap-2">
          <Plus className="h-4 w-4" />
          {displayActionLabel}
        </Button>
      )}
    </div>
  );
}

/**
 * Minimal empty state for inline use
 */
export function EmptyStateInline({
  message = "No items",
}: {
  message?: string;
}) {
  return (
    <div className="p-[var(--density-page-pad)] text-center text-sm text-foreground-muted">{message}</div>
  );
}
