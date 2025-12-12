import { useNavigate } from "@tanstack/react-router";
import {
    Plus,
    LayoutList,
    LayoutGrid,
    Clock,
    BarChart3,
    FolderOpen,
    Settings,
    RefreshCw
} from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import type { CommandPaletteCommand } from "@/components/common/CommandPalette";

export function useAppCommands(refreshTasks?: () => void) {
    const navigate = useNavigate();
    const { setNewTaskModalOpen } = useUIStore();

    const commands: CommandPaletteCommand[] = [
        {
            id: "new-task",
            label: "Create new task",
            description: "Create a task in the current project",
            icon: <Plus className="h-3.5 w-3.5 text-primary" />,
            shortcut: "⌘ N",
            keywords: ["create", "new", "task"],
            onSelect: () => setNewTaskModalOpen(true),
        },
        {
            id: "go-list",
            label: "Go to Tasks",
            description: "Task list view",
            icon: <LayoutList className="h-3.5 w-3.5 text-foreground-subtle" />,
            shortcut: "g l",
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
            shortcut: "g t",
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
            keywords: ["projects", "namespace"],
            onSelect: () => navigate({ to: "/projects" }),
        },
        {
            id: "go-settings",
            label: "Go to Settings",
            description: "Appearance & preferences",
            icon: <Settings className="h-3.5 w-3.5 text-foreground-subtle" />,
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
                refreshTasks?.();
            },
        },
    ];

    return commands;
}
