import { useNavigate } from "@tanstack/react-router";
import {
    Plus,
    LayoutList,
    LayoutGrid,
    Clock,
    BarChart3,
    FolderOpen,
    Settings,
    RefreshCw,
    History,
    Undo2,
    Redo2
} from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import type { CommandPaletteCommand } from "@/components/common/CommandPalette";

export function useAppCommands(opts?: {
    refreshTasks?: () => void;
    undo?: () => void;
    redo?: () => void;
    openHistory?: () => void;
}) {
    const navigate = useNavigate();
    const { setNewTaskModalOpen } = useUIStore();

    const commands: CommandPaletteCommand[] = [
        {
            id: "new-task",
            label: "Create new plan/task",
            description: "Create a plan or task in the current project",
            icon: <Plus className="h-3.5 w-3.5 text-primary" />,
            shortcut: "⌘ N",
            keywords: ["create", "new", "plan", "task"],
            onSelect: () => setNewTaskModalOpen(true),
        },
        {
            id: "go-plans",
            label: "Go to Plans",
            description: "Plans list view",
            icon: <LayoutList className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g l",
            keywords: ["plans", "list"],
            onSelect: () => navigate({ to: "/plans" }),
        },
        {
            id: "go-tasks",
            label: "Go to Tasks",
            description: "Task list view",
            icon: <LayoutList className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g t",
            keywords: ["tasks", "list"],
            onSelect: () => navigate({ to: "/" }),
        },
        {
            id: "go-board",
            label: "Go to Board",
            description: "Kanban view",
            icon: <LayoutGrid className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g b",
            keywords: ["board", "kanban"],
            onSelect: () => navigate({ to: "/board" }),
        },
        {
            id: "go-timeline",
            label: "Go to Timeline",
            description: "Activity feed",
            icon: <Clock className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g i",
            keywords: ["timeline", "activity"],
            onSelect: () => navigate({ to: "/timeline" }),
        },
        {
            id: "go-dashboard",
            label: "Go to Dashboard",
            description: "Summary & analytics",
            icon: <BarChart3 className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g d",
            keywords: ["dashboard", "stats"],
            onSelect: () => navigate({ to: "/dashboard" }),
        },
        {
            id: "go-projects",
            label: "Go to Projects",
            description: "Switch active project",
            icon: <FolderOpen className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g p",
            keywords: ["projects", "namespace"],
            onSelect: () => navigate({ to: "/projects" }),
        },
        {
            id: "go-settings",
            label: "Go to Settings",
            description: "Appearance & preferences",
            icon: <Settings className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g s",
            keywords: ["settings", "preferences"],
            onSelect: () => navigate({ to: "/settings" }),
        },
        {
            id: "refresh",
            label: "Refresh data",
            description: "Reload tasks and storage info",
            icon: <RefreshCw className="h-3.5 w-3.5 text-foreground-subtle" />,
            keywords: ["refresh", "reload"],
            onSelect: () => {
                opts?.refreshTasks?.();
            },
        },
        {
            id: "history-open",
            label: "Open history",
            description: "View operation history (undo/redo)",
            icon: <History className="h-3.5 w-3.5 text-foreground-subtle" />,
            keywords: ["history", "undo", "redo"],
            onSelect: () => {
                opts?.openHistory?.();
            },
        },
        {
            id: "undo",
            label: "Undo",
            description: "Undo last operation (safe snapshot restore)",
            icon: <Undo2 className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "⌘ Z",
            keywords: ["undo", "rollback"],
            onSelect: () => {
                opts?.undo?.();
            },
        },
        {
            id: "redo",
            label: "Redo",
            description: "Redo last undone operation (snapshot restore)",
            icon: <Redo2 className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "⇧ ⌘ Z",
            keywords: ["redo"],
            onSelect: () => {
                opts?.redo?.();
            },
        },
    ];

    return commands;
}
