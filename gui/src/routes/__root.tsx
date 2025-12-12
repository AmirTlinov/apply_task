import { createRootRoute, Outlet, useLocation } from '@tanstack/react-router'
import { Sidebar } from '@/components/layout/Sidebar'
import { useUIStore } from '@/stores/uiStore'
import { CommandPalette } from '@/components/common/CommandPalette'
import { NewTaskModal } from '@/features/tasks/components/NewTaskModal'
import { TaskDetailModal } from '@/features/tasks/components/TaskDetailModal'
import { useAppCommands } from '@/hooks/useAppCommands'
import { useTasks } from '@/features/tasks/hooks/useTasks'
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

import { Header } from '@/components/layout/Header'
import { useAIStatus } from '@/hooks/useAIStatus'

// ... imports

function RootComponent() {
    const {
        sidebarCollapsed,
        toggleSidebar,
        isPaletteOpen,
        setPaletteOpen,
        newTaskModalOpen,
        setNewTaskModalOpen,
        selectedTaskId,
        setSelectedTaskId,
        setSearchQuery,
        selectedNamespace,
        setSelectedNamespace
    } = useUIStore()

    const location = useLocation()
    const { tasks, refresh, namespaces, isLoading } = useTasks({
        namespace: selectedNamespace,
        allNamespaces: selectedNamespace === null
    })
    const commands = useAppCommands(refresh)
    const { data: aiStatus } = useAIStatus()

    // ... deep linking effects ...

    // ... global keyboard shortcuts ...

    // Determine title based on path
    const getPageTitle = () => {
        const path = location.pathname
        if (path === '/') return 'Tasks'
        if (path === '/board') return 'Board'
        if (path === '/timeline') return 'Timeline'
        if (path === '/dashboard') return 'Dashboard'
        if (path === '/projects') return 'Projects'
        if (path === '/settings') return 'Settings'
        return 'Apply Task'
    }

    return (
        <div className="flex bg-background font-sans antialiased h-screen w-screen overflow-hidden">
            <Sidebar
                collapsed={sidebarCollapsed}
                onToggle={toggleSidebar}
                projectName="Apply Task"
            />
            <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
                <Header
                    title={getPageTitle()}
                    taskCount={tasks.length}
                    onSearch={setSearchQuery}
                    onNewTask={() => setNewTaskModalOpen(true)}
                    onRefresh={refresh}
                    onCommandPalette={() => setPaletteOpen(true)}
                    isLoading={isLoading}
                    namespaces={namespaces}
                    selectedNamespace={selectedNamespace}
                    onNamespaceChange={setSelectedNamespace}
                    aiStatus={aiStatus}
                />
                <div className="flex-1 overflow-hidden flex flex-col relative">
                    <Outlet />
                </div>
            </div>

            <CommandPalette
                isOpen={isPaletteOpen}
                onClose={() => setPaletteOpen(false)}
                tasks={tasks}
                commands={commands}
                onSelectTask={(taskId) => {
                    setSelectedTaskId(taskId)
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

            {/* Global Task Detail Logic */}
            {(() => {
                const selectedTask = selectedTaskId ? tasks.find(t => t.id === selectedTaskId) : null;

                if (!selectedTaskId) return null;

                return (
                    <TaskDetailModal
                        taskId={selectedTask?.task_id || selectedTaskId}
                        domain={selectedTask?.domain}
                        namespace={selectedTask?.namespace}
                        onClose={() => setSelectedTaskId(null)}
                        onDelete={() => {
                            setSelectedTaskId(null)
                            refresh()
                        }}
                    />
                )
            })()}
        </div>
    )
}
