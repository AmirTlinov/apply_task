/**
 * Skeleton loading components for perceived performance
 */

import { cn } from "@/lib/utils";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
}

export function Skeleton({
  width,
  height = 16,
  borderRadius = 6,
  className = "",
}: SkeletonProps) {
  return (
    <div
      className={cn("skeleton", className)}
      style={{
        width: width ?? "100%",
        height,
        borderRadius,
      }}
    />
  );
}

/**
 * TaskCard skeleton for loading state
 */
export function TaskCardSkeleton() {
  return (
    <div
      className="rounded-xl border border-border bg-background p-4"
    >
      {/* Header: ID, Status, Updated */}
      <div className="mb-2.5 flex items-center justify-between">
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Skeleton width={60} height={22} borderRadius={6} />
          <Skeleton width={50} height={22} borderRadius={999} />
        </div>
        <Skeleton width={50} height={14} />
      </div>

      {/* Title */}
      <Skeleton height={20} className="mb-2" />
      <Skeleton width="70%" height={20} />

      {/* Tags */}
      <div className="my-3.5 flex gap-1.5">
        <Skeleton width={50} height={22} borderRadius={6} />
        <Skeleton width={60} height={22} borderRadius={6} />
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-1">
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Skeleton width={140} height={5} borderRadius={999} />
          <Skeleton width={40} height={16} />
        </div>
        <Skeleton width={60} height={14} />
      </div>
    </div>
  );
}

/**
 * List of skeleton cards
 */
export function TaskListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(320px,1fr))]">
      {Array.from({ length: count }).map((_, i) => (
        <TaskCardSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * Sidebar skeleton
 */
export function SidebarSkeleton() {
  return (
    <div className="flex flex-col gap-1 p-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} height={40} borderRadius={8} />
      ))}
    </div>
  );
}

/**
 * Header skeleton
 */
export function HeaderSkeleton() {
  return (
    <div className="flex min-h-[var(--density-header-min-h)] items-center justify-between px-[var(--density-shell-px)]">
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <Skeleton width={100} height={28} />
        <Skeleton width={60} height={20} borderRadius={999} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <Skeleton width={240} height={36} borderRadius={8} />
        <Skeleton width={100} height={36} borderRadius={8} />
      </div>
    </div>
  );
}
