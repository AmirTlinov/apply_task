import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { TaskList } from '@/features/tasks/components/TaskList'
import { TaskTableView } from '@/features/tasks/components/TaskTableView'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { useUIStore } from '@/stores/uiStore'
import { useState, useMemo } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { useSettingsStore } from '@/stores/settingsStore'
import type { TaskStatus } from '@/types/task'
import { useMediaQuery } from '@/hooks/useMediaQuery'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: Index,
})

function Index() {
    const { searchQuery, selectedNamespace } = useUIStore()
    const openDetailPanel = useUIStore((s) => s.openDetailPanel)
    const [statusFilter, setStatusFilter] = useState<"ALL" | TaskStatus>("ALL")
    const { tasks, isLoading, updateTaskStatus, deleteTask } = useTasks({
        namespace: selectedNamespace,
        allNamespaces: selectedNamespace === null,
        status: statusFilter === "ALL" ? undefined : statusFilter,
    })
    const [focusedTaskId, setFocusedTaskId] = useState<string | null>(null)
    const tasksView = useSettingsStore((s) => s.tasksViewMode)
    const setTasksView = useSettingsStore((s) => s.setTasksViewMode)
    const navigate = useNavigate()
    const isMobile = useMediaQuery("(max-width: 767px)")

    const openTask = (uiTaskId: string, subtaskPath?: string) => {
        const task = tasks.find(t => t.id === uiTaskId)
        const apiTaskId = uiTaskId.split("/").pop() || uiTaskId
        if (isMobile) {
            navigate({
                to: "/task/$taskId",
                params: { taskId: apiTaskId },
                search: {
                    domain: task?.domain || undefined,
                    subtask: subtaskPath,
                },
            })
            return
        }
        openDetailPanel({
            taskId: apiTaskId,
            domain: task?.domain || undefined,
            subtaskPath,
        })
    }

    // Filter tasks by search query (namespace filtering is handled by useTasks).
    // Tree view needs the full list to keep parent/child context (ancestors).
    const filteredTasks = useMemo(() => {
        if (!searchQuery) return tasks
        const lowerQuery = searchQuery.toLowerCase()
        return tasks.filter(t =>
            t.title.toLowerCase().includes(lowerQuery) ||
            t.id.toLowerCase().includes(lowerQuery)
        )
    }, [tasks, searchQuery])

    return (
        <div className="flex flex-1 w-full min-h-0 flex-col bg-background">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-background px-[var(--density-shell-px)] py-2">
                <div className="flex flex-wrap items-center gap-2">
                    <div className="inline-flex rounded-lg border border-border bg-background-subtle p-1">
                        <button
                            type="button"
                            onClick={() => setStatusFilter("ALL")}
                            className={cn(
                                "rounded-md px-2 py-0.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                statusFilter === "ALL"
                                    ? "bg-background text-foreground"
                                    : "text-foreground-muted hover:bg-background-hover"
                            )}
                            aria-pressed={statusFilter === "ALL"}
                        >
                            All
                        </button>
                        <button
                            type="button"
                            onClick={() => setStatusFilter("TODO")}
                            className={cn(
                                "rounded-md px-2 py-0.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                statusFilter === "TODO"
                                    ? "bg-background text-foreground"
                                    : "text-foreground-muted hover:bg-background-hover"
                            )}
                            aria-pressed={statusFilter === "TODO"}
                        >
                            TODO
                        </button>
                        <button
                            type="button"
                            onClick={() => setStatusFilter("ACTIVE")}
                            className={cn(
                                "rounded-md px-2 py-0.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                statusFilter === "ACTIVE"
                                    ? "bg-background text-foreground"
                                    : "text-foreground-muted hover:bg-background-hover"
                            )}
                            aria-pressed={statusFilter === "ACTIVE"}
                        >
                            ACTIVE
                        </button>
                        <button
                            type="button"
                            onClick={() => setStatusFilter("DONE")}
                            className={cn(
                                "rounded-md px-2 py-0.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                statusFilter === "DONE"
                                    ? "bg-background text-foreground"
                                    : "text-foreground-muted hover:bg-background-hover"
                            )}
                            aria-pressed={statusFilter === "DONE"}
                        >
                            DONE
                        </button>
                    </div>

                    <div className="inline-flex rounded-lg border border-border bg-background-subtle p-1">
                        <button
                            type="button"
                            onClick={() => setTasksView("table")}
                            className={cn(
                                "rounded-md px-2 py-0.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                tasksView === "table"
                                    ? "bg-background text-foreground"
                                    : "text-foreground-muted hover:bg-background-hover"
                            )}
                            aria-pressed={tasksView === "table"}
                        >
                            Table
                        </button>
                        <button
                            type="button"
                            onClick={() => setTasksView("cards")}
                            className={cn(
                                "rounded-md px-2 py-0.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                tasksView === "cards"
                                    ? "bg-background text-foreground"
                                    : "text-foreground-muted hover:bg-background-hover"
                            )}
                            aria-pressed={tasksView === "cards"}
                        >
                            Cards
                        </button>
                    </div>
                </div>
            </div>

            {tasksView === 'cards' ? (
                <TaskList
                    tasks={filteredTasks}
                    isLoading={isLoading}
                    onTaskClick={(id) => openTask(id)}
                    focusedTaskId={focusedTaskId}
                    onFocusChange={setFocusedTaskId}
                    onStatusChange={updateTaskStatus}
                    onDelete={deleteTask}
                    onNewTask={() => useUIStore.getState().setNewTaskModalOpen(true)}
                    searchQuery={searchQuery}
                />
            ) : (
                <TaskTableView
                    tasks={filteredTasks}
                    isLoading={isLoading}
                    onTaskClick={(id) => openTask(id)}
                    focusedTaskId={focusedTaskId}
                    onFocusChange={setFocusedTaskId}
                    onNewTask={() => useUIStore.getState().setNewTaskModalOpen(true)}
                    searchQuery={searchQuery}
                />
            )}
        </div>
    )
}
