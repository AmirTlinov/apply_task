/**
 * Projects View - Project management and switching
 */

import {
  FolderOpen,
  Plus,
  CheckCircle2,
  Clock,
  Folder,
  Star,
  RefreshCw,
  ExternalLink,
  Archive,
  Trash2,
} from "lucide-react";
import type { TaskListItem, Namespace } from "@/types/task";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { ProgressBar } from "@/components/common/ProgressBar";
import { cn } from "@/lib/utils";
import { openPath } from "@/lib/tauri";
import { toast } from "@/components/common/toast";
import { useSettingsStore } from "@/stores/settingsStore";

interface ProjectsViewProps {
  tasks: TaskListItem[];
  projectName?: string;
  projectPath?: string;
  namespaces: Namespace[];
  isLoading?: boolean;
  onOpenProject?: () => void;
  onRefresh?: () => void;
  onSelectNamespace?: (namespace: string | null) => void;
}

interface Project {
  id: string;
  name: string;
  path: string;
  taskCount: number;
  completedCount: number;
  lastOpened: Date;
  isActive: boolean;
  isFavorite?: boolean;
  isArchived?: boolean;
}

// Build current project from real API data
function getCurrentProject(
  projectName?: string,
  projectPath?: string,
  tasks: TaskListItem[] = []
): Project | null {
  if (!projectName && !projectPath) return null;

  const completed = tasks.filter((t) => t.status === "DONE").length;

  return {
    id: "current",
    name: projectName || "Current Project",
    path: projectPath || "",
    taskCount: tasks.length,
    completedCount: completed,
    lastOpened: new Date(),
    isActive: true,
    isFavorite: true,
  };
}

function formatDate(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

export function ProjectsView({
  tasks,
  projectName,
  projectPath,
  namespaces,
  isLoading = false,
  onOpenProject,
  onRefresh,
  onSelectNamespace,
}: ProjectsViewProps) {
  const archivedNamespaces = useSettingsStore((s) => s.archivedNamespaces);
  const archiveNamespace = useSettingsStore((s) => s.archiveNamespace);
  const restoreNamespace = useSettingsStore((s) => s.restoreNamespace);

  if (isLoading) {
    return <ProjectsSkeleton />;
  }

  const currentProject = getCurrentProject(projectName, projectPath, tasks);

  // Convert namespaces to Project objects
  const allProjects: Project[] = namespaces.map((ns) => ({
    id: ns.namespace,
    name: ns.namespace,
    path: ns.path,
    taskCount: ns.task_count,
    completedCount: 0, // We don't have this info from backend
    lastOpened: new Date(),
    isActive: ns.namespace === projectName,
    isFavorite: ns.namespace === projectName,
    isArchived: archivedNamespaces.includes(ns.namespace),
  }));

  const archivedProjects = allProjects.filter((p) => p.isArchived);
  const visibleProjects = allProjects.filter((p) => !p.isArchived);
  const otherProjects = visibleProjects.filter((p) => !p.isActive);

  return (
    <div className="flex flex-1 flex-col gap-[var(--density-page-gap)] overflow-y-auto p-[var(--density-page-pad)]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Projects</h2>
          <p className="mt-0.5 text-sm text-foreground-muted">
            Manage and switch between your projects ({allProjects.length} total)
          </p>
        </div>

        {onOpenProject && (
          <Button onClick={onOpenProject} className="gap-2">
            <Plus className="h-4 w-4" />
            Open Project
          </Button>
        )}
      </div>

      {/* Current Project */}
      {currentProject && (
        <section>
          <div className="mb-3 flex items-center gap-2">
            <Star className="h-4 w-4 text-status-warn" />
            <h3 className="text-sm font-semibold text-foreground-muted">
              Current Project
            </h3>
          </div>

          <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(300px,1fr))]">
            <ProjectCard
              project={currentProject}
              onRefresh={onRefresh}
              onSelectNamespace={onSelectNamespace}
              onArchive={archiveNamespace}
              onRestore={restoreNamespace}
            />
          </div>
        </section>
      )}

      {/* All Projects */}
      {otherProjects.length > 0 && (
        <section>
          <div className="mb-3 flex items-center gap-2">
            <Folder className="h-4 w-4 text-foreground-muted" />
            <h3 className="text-sm font-semibold text-foreground-muted">
              All Projects
            </h3>
          </div>

          <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(300px,1fr))]">
            {otherProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onRefresh={onRefresh}
                onSelectNamespace={onSelectNamespace}
                onArchive={archiveNamespace}
                onRestore={restoreNamespace}
              />
            ))}
          </div>
        </section>
      )}

      {/* Archived Projects */}
      {archivedProjects.length > 0 && (
        <section>
          <div className="mb-3 flex items-center gap-2">
            <Archive className="h-4 w-4 text-foreground-muted" />
            <h3 className="text-sm font-semibold text-foreground-muted">
              Archived Projects
            </h3>
          </div>
          <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(300px,1fr))]">
            {archivedProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onRefresh={onRefresh}
                onSelectNamespace={onSelectNamespace}
                onArchive={archiveNamespace}
                onRestore={restoreNamespace}
              />
            ))}
          </div>
        </section>
      )}

      {/* Empty state for no projects */}
      {allProjects.length === 0 && (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 py-12 text-center">
          <Folder className="h-12 w-12 text-foreground-subtle opacity-60" />
          <div className="text-base font-semibold text-foreground">
            No projects yet
          </div>
          <div className="text-sm text-foreground-muted">
            Open a folder to get started
          </div>
          {onOpenProject && (
            <Button onClick={onOpenProject} className="mt-2 gap-2">
              <Plus className="h-4 w-4" />
              Open Project
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

interface ProjectCardProps {
  project: Project;
  onRefresh?: () => void;
  onSelectNamespace?: (namespace: string | null) => void;
  onArchive: (namespace: string) => void;
  onRestore: (namespace: string) => void;
}

function ProjectCard({ project, onRefresh, onSelectNamespace, onArchive, onRestore }: ProjectCardProps) {
  const progress = project.taskCount > 0
    ? Math.round((project.completedCount / project.taskCount) * 100)
    : 0;

  const isClickable = !project.isArchived;

  const menuItems = project.isArchived
    ? [
        {
          label: "Restore",
          icon: <FolderOpen className="h-4 w-4" />,
          onClick: () => onRestore(project.id),
        },
      ]
    : [
        {
          label: "Refresh",
          icon: <RefreshCw className="h-4 w-4" />,
          onClick: () => {
            onRefresh?.();
            toast.info("Projects refreshed");
          },
        },
        {
          label: "Open folder",
          icon: <ExternalLink className="h-4 w-4" />,
          onClick: async () => {
            const resp = await openPath(project.path);
            if (!resp.success) {
              toast.error(resp.error || "Failed to open folder");
            }
          },
        },
        { type: "separator" as const },
        {
          label: "Archive",
          icon: <Archive className="h-4 w-4" />,
          onClick: () => onArchive(project.id),
          disabled: project.isActive,
        },
        {
          label: "Remove from list",
          icon: <Trash2 className="h-4 w-4" />,
          onClick: () => {
            onArchive(project.id);
            toast.info("Project hidden. Delete folder manually to remove steps.");
          },
          danger: true,
          disabled: project.isActive,
        },
      ];

  return (
    <div
      role={isClickable ? "button" : undefined}
      tabIndex={isClickable ? 0 : -1}
      onKeyDown={(e) => {
        if (!isClickable) return;
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelectNamespace?.(project.id);
          toast.success(`Switched to ${project.name}`);
        }
      }}
      onClick={() => {
        if (!isClickable) return;
        onSelectNamespace?.(project.id);
        toast.success(`Switched to ${project.name}`);
      }}
      className={cn(
        "group rounded-xl border p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors transition-shadow duration-200 motion-reduce:transition-none",
        project.isActive
          ? "border-primary/40 bg-primary/5"
          : "border-border bg-background",
        project.isArchived
          ? "cursor-default opacity-75"
          : "cursor-pointer hover:border-foreground/20 hover:shadow-md"
      )}
    >
      {/* Header */}
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
              project.isActive
                ? "bg-primary text-white"
                : "bg-background-muted text-foreground-muted"
            )}
          >
            <FolderOpen className="h-[18px] w-[18px]" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="truncate text-sm font-semibold text-foreground">
                {project.name}
              </span>
              {project.isActive && (
                <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                  Active
                </span>
              )}
            </div>
            <div className="mt-1 truncate font-mono text-[11px] text-foreground-muted">
              {project.path}
            </div>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-lg"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="h-4 w-4 text-foreground-subtle" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            {menuItems.map((item, index) => {
              if ("type" in item && item.type === "separator") {
                return <DropdownMenuSeparator key={`sep-${index}`} />
              }

              return (
                <DropdownMenuItem
                  key={item.label}
                  disabled={item.disabled}
                  onSelect={() => item.onClick()}
                  className={cn(
                    "gap-2",
                    item.danger && "text-status-fail focus:text-status-fail"
                  )}
                >
                  <span className="flex h-4 w-4 items-center justify-center">
                    {item.icon}
                  </span>
                  {item.label}
                </DropdownMenuItem>
              )
            })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="mb-3 flex items-center gap-4 text-xs text-foreground-muted">
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="h-3.5 w-3.5 text-status-ok" />
          <span className="tabular-nums">
            {project.completedCount} / {project.taskCount}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5 text-foreground-subtle" />
          <span>{formatDate(project.lastOpened)}</span>
        </div>
      </div>

      <ProgressBar value={progress} max={100} size="sm" />
    </div>
  );
}

function ProjectsSkeleton() {
  return (
    <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "32px" }}>
      <div>
        <div className="skeleton" style={{ height: "24px", width: "120px", marginBottom: "8px", borderRadius: "4px" }} />
        <div className="skeleton" style={{ height: "16px", width: "250px", borderRadius: "4px" }} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton" style={{ height: "140px", borderRadius: "12px" }} />
        ))}
      </div>
    </div>
  );
}
