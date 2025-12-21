import { useCallback, useEffect } from 'react'
import { createRootRoute, Outlet, useLocation, useNavigate } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { useUIStore } from '@/stores/uiStore'
import { CommandPalette } from '@/components/common/CommandPalette'
import { NewTaskModal } from '@/features/tasks/components/NewTaskModal'
import { TaskDetailSidePanel } from '@/features/tasks/components/TaskDetailSidePanel'
import { useAppCommands } from '@/hooks/useAppCommands'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { ToastContainer } from '@/components/common/Toast'
import { toast } from '@/components/common/toast'
import { isEditableTarget, isPlainKeypress } from '@/lib/keyboard'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import { getOperationHistory, redoLastOperation, undoLastOperation } from '@/lib/tauri'
import { OperationHistoryDialog } from '@/components/common/OperationHistoryDialog'
import '../styles/globals.css';

interface RootSearch {
    taskId?: string
}

export const Route = createRootRoute({
    component: RootComponent,
    validateSearch: (search: Record<string, unknown>): RootSearch => {
        return {
            taskId: (search.taskId as string) || undefined
        }
    }
})

function RootComponent() {
    const {
        sidebarOpen,
        setSidebarOpen,
        isPaletteOpen,
        setPaletteOpen,
        historyModalOpen,
        setHistoryModalOpen,
        newTaskModalOpen,
        setNewTaskModalOpen,
        setSearchQuery,
        selectedNamespace,
        setSelectedNamespace,
        openDetailPanel,
    } = useUIStore()

    const location = useLocation()
    const navigate = useNavigate()
    const isMobile = useMediaQuery("(max-width: 767px)")
    const queryClient = useQueryClient()
    const { tasks, refresh, namespaces, isLoading } = useTasks({
        namespace: selectedNamespace,
        allNamespaces: selectedNamespace === null
    })
    const historyDisabledReason =
        selectedNamespace === null ? "Undo/Redo works within a single project. Select a project first." : undefined

    const operationHistoryQueryKey = ['operationHistory', selectedNamespace] as const
    const operationHistoryQuery = useQuery({
        queryKey: operationHistoryQueryKey,
        queryFn: async () => {
            if (!selectedNamespace) return null
            const resp = await getOperationHistory({ limit: 50 })
            if (!resp.success || !resp.history) throw new Error(resp.error || "Failed to load history")
            return resp.history
        },
        enabled: typeof selectedNamespace === 'string',
        staleTime: 1000,
    })

    const refreshAfterUndoRedo = useCallback(async () => {
        await refresh()
        queryClient.invalidateQueries({ queryKey: ['task'] })
        queryClient.invalidateQueries({ queryKey: ['taskPlanMeta'] })
        queryClient.invalidateQueries({ queryKey: operationHistoryQueryKey })
    }, [operationHistoryQueryKey, queryClient, refresh])

    const undoMutation = useMutation({
        mutationFn: async () => {
            if (!selectedNamespace) throw new Error(historyDisabledReason || "Select a project first")
            const resp = await undoLastOperation()
            if (!resp.success) throw new Error(resp.error || "Failed to undo")
            return resp
        },
        onSuccess: async () => {
            toast.success("Undone last operation")
            await refreshAfterUndoRedo()
        },
        onError: (err) => {
            toast.error(err instanceof Error ? err.message : "Failed to undo")
        },
    })

    const redoMutation = useMutation({
        mutationFn: async () => {
            if (!selectedNamespace) throw new Error(historyDisabledReason || "Select a project first")
            const resp = await redoLastOperation()
            if (!resp.success) throw new Error(resp.error || "Failed to redo")
            return resp
        },
        onSuccess: async () => {
            toast.success("Redo last operation")
            await refreshAfterUndoRedo()
        },
        onError: (err) => {
            toast.error(err instanceof Error ? err.message : "Failed to redo")
        },
    })

    const openHistory = useCallback(() => {
        if (!selectedNamespace) {
            toast.error(historyDisabledReason || "Select a project first")
            return
        }
        setHistoryModalOpen(true)
    }, [historyDisabledReason, selectedNamespace, setHistoryModalOpen])

    const undo = useCallback(() => {
        if (!selectedNamespace) {
            toast.error(historyDisabledReason || "Select a project first")
            return
        }
        undoMutation.mutate()
    }, [historyDisabledReason, selectedNamespace, undoMutation])

    const redo = useCallback(() => {
        if (!selectedNamespace) {
            toast.error(historyDisabledReason || "Select a project first")
            return
        }
        redoMutation.mutate()
    }, [historyDisabledReason, redoMutation, selectedNamespace])

    const commands = useAppCommands({
        refreshTasks: refresh,
        undo,
        redo,
        openHistory,
    })

    const openTask = (uiTaskId: string) => {
        const task = tasks.find(t => t.id === uiTaskId)
        const apiTaskId = uiTaskId.split("/").pop() || uiTaskId
        if (isMobile) {
            navigate({
                to: "/task/$taskId",
                params: { taskId: apiTaskId },
                search: {
                    domain: task?.domain || undefined,
                },
            })
            return
        }
        openDetailPanel({
            taskId: apiTaskId,
            domain: task?.domain || undefined,
        })
        if (
            location.pathname !== '/' &&
            !location.pathname.startsWith('/board') &&
            !location.pathname.startsWith('/timeline')
        ) {
            navigate({ to: '/' })
        }
    }

    useEffect(() => {
        if (!isMobile) {
            setSidebarOpen(false)
        }
    }, [isMobile, setSidebarOpen])

    useEffect(() => {
        if (isMobile) {
            setSidebarOpen(false)
        }
    }, [isMobile, location.pathname, location.search, setSidebarOpen])

    useEffect(() => {
        let awaitingGo = false
        let goTimeout: number | null = null

        const clearGo = () => {
            awaitingGo = false
            if (goTimeout !== null) {
                window.clearTimeout(goTimeout)
                goTimeout = null
            }
        }

        const onKeyDown = (e: KeyboardEvent) => {
            const key = e.key.toLowerCase()
            const isCtrl = e.ctrlKey || e.metaKey
            const ui = useUIStore.getState()

            if (key === 'escape') {
                if (ui.isPaletteOpen) {
                    e.preventDefault()
                    ui.setPaletteOpen(false)
                    return
                }
                if (ui.newTaskModalOpen) {
                    e.preventDefault()
                    ui.setNewTaskModalOpen(false)
                    return
                }
                if (ui.sidebarOpen) {
                    e.preventDefault()
                    ui.setSidebarOpen(false)
                    return
                }
                if (ui.detailPanel) {
                    e.preventDefault()
                    ui.closeDetailPanel()
                    return
                }
                clearGo()
                return
            }

            if (ui.isPaletteOpen || ui.newTaskModalOpen) return

            if ((e.metaKey || e.ctrlKey) && key === 'k') {
                e.preventDefault()
                ui.setPaletteOpen(true)
                return
            }

            if ((e.metaKey || e.ctrlKey) && key === 'n') {
                e.preventDefault()
                ui.setNewTaskModalOpen(true)
                return
            }

            if (isEditableTarget(e.target)) return

            // Safe editing shortcuts (global, outside inputs)
            if (isCtrl && key === 'z') {
                e.preventDefault()
                if (e.shiftKey) {
                    redo()
                } else {
                    undo()
                }
                return
            }

            if (awaitingGo) {
                clearGo()
                if (!isPlainKeypress(e)) return
                switch (key) {
                    case 'l':
                        e.preventDefault()
                        navigate({ to: '/' })
                        break
                    case 'b':
                        e.preventDefault()
                        navigate({ to: '/board' })
                        break
                    case 't':
                        e.preventDefault()
                        navigate({ to: '/timeline' })
                        break
                    case 'd':
                        e.preventDefault()
                        navigate({ to: '/dashboard' })
                        break
                    case 'p':
                        e.preventDefault()
                        navigate({ to: '/projects' })
                        break
                    case 's':
                        e.preventDefault()
                        navigate({ to: '/settings' })
                        break
                    default:
                        break
                }
                return
            }

            if (isPlainKeypress(e) && key === 'g') {
                awaitingGo = true
                goTimeout = window.setTimeout(() => {
                    awaitingGo = false
                    goTimeout = null
                }, 1200)
            }
        }

        window.addEventListener('keydown', onKeyDown)
        return () => {
            window.removeEventListener('keydown', onKeyDown)
            clearGo()
        }
    }, [navigate, redo, undo])

    // Determine title based on path
    const getPageTitle = () => {
        const path = location.pathname
        if (path.startsWith('/plan/')) return 'Plan'
        if (path.startsWith('/task/')) return 'Task'
        if (path === '/') return 'Tasks'
        if (path === '/plans') return 'Plans'
        if (path === '/board') return 'Board'
        if (path === '/timeline') return 'Timeline'
        if (path === '/dashboard') return 'Dashboard'
        if (path === '/projects') return 'Projects'
        if (path === '/settings') return 'Settings'
        return 'Apply Task'
    }

    return (
        <div className="flex bg-background font-sans antialiased h-screen w-screen overflow-hidden">
            {!isMobile && (
                <Sidebar
                />
            )}
            <div className="flex flex-1 h-full min-w-0 overflow-hidden">
                <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
                    <Header
                        title={getPageTitle()}
                        taskCount={tasks.length}
                        onMenu={isMobile ? () => setSidebarOpen(true) : undefined}
                        onSearch={setSearchQuery}
                        onNewTask={() => setNewTaskModalOpen(true)}
                        onRefresh={refresh}
                        onCommandPalette={() => setPaletteOpen(true)}
                        isLoading={isLoading}
                        namespaces={namespaces}
                        selectedNamespace={selectedNamespace}
                        onNamespaceChange={setSelectedNamespace}
                        onUndo={undo}
                        onRedo={redo}
                        onOpenHistory={openHistory}
                        canUndo={operationHistoryQuery.data?.can_undo ?? false}
                        canRedo={operationHistoryQuery.data?.can_redo ?? false}
                        historyDisabledReason={historyDisabledReason}
                    />
                    <div className="flex-1 min-h-0 overflow-hidden flex flex-col relative">
                        <Outlet />
                    </div>
                </div>
                {!isMobile && (location.pathname === '/' || location.pathname.startsWith('/board') || location.pathname.startsWith('/timeline')) && (
                    <TaskDetailSidePanel />
                )}
            </div>

            {isMobile && (
                <div
                    className={[
                        "fixed inset-0 z-50 md:hidden",
                        "transition-opacity duration-200 motion-reduce:transition-none",
                        sidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none",
                    ].join(" ")}
                    aria-hidden={!sidebarOpen}
                >
                    <button
                        type="button"
                        className="absolute inset-0 bg-black/40"
                        aria-label="Close menu"
                        onClick={() => setSidebarOpen(false)}
                    />
                    <div
                        role="dialog"
                        aria-modal="true"
                        className={[
                            "absolute inset-y-0 left-0 shadow-xl",
                            "transition-transform duration-200 motion-reduce:transition-none",
                            sidebarOpen ? "translate-x-0" : "-translate-x-full",
                        ].join(" ")}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <Sidebar
                            onNavigate={() => setSidebarOpen(false)}
                        />
                    </div>
                </div>
            )}

            <CommandPalette
                isOpen={isPaletteOpen}
                onClose={() => setPaletteOpen(false)}
                tasks={tasks}
                commands={commands}
                onSelectTask={(taskId) => {
                    openTask(taskId)
                    setPaletteOpen(false)
                }}
            />

            <NewTaskModal
                isOpen={newTaskModalOpen}
                onClose={() => setNewTaskModalOpen(false)}
                onTaskCreated={() => {
                    refresh()
                    setNewTaskModalOpen(false)
                }}
                namespaces={namespaces}
                selectedNamespace={selectedNamespace}
            />

            <OperationHistoryDialog
                isOpen={historyModalOpen}
                onClose={() => setHistoryModalOpen(false)}
                namespace={selectedNamespace}
                disabledReason={historyDisabledReason}
                history={operationHistoryQuery.data ?? undefined}
                isLoading={operationHistoryQuery.isLoading}
                error={(operationHistoryQuery.error as Error | null)?.message ?? null}
                canUndo={operationHistoryQuery.data?.can_undo ?? false}
                canRedo={operationHistoryQuery.data?.can_redo ?? false}
                isBusy={undoMutation.isPending || redoMutation.isPending}
                onUndo={undo}
                onRedo={redo}
                onRefresh={() => operationHistoryQuery.refetch()}
            />

            <ToastContainer />
        </div>
    )
}
