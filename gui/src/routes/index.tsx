import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { TaskList } from '@/features/tasks/components/TaskList'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { useUIStore } from '@/stores/uiStore'
import { useState, useMemo } from 'react'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: Index,
})

function Index() {
    const { searchQuery, selectedNamespace, setSelectedTaskId } = useUIStore()
    const { tasks, isLoading, updateTaskStatus, deleteTask } = useTasks({
        namespace: selectedNamespace,
        allNamespaces: selectedNamespace === null
    })
    const [focusedTaskId, setFocusedTaskId] = useState<string | null>(null)

    // Filter tasks by search query (namespace filtering is handled by useTasks)
    const filteredTasks = useMemo(() => {
        if (!searchQuery) return tasks
        const lowerQuery = searchQuery.toLowerCase()
        return tasks.filter(t =>
            t.title.toLowerCase().includes(lowerQuery) ||
            t.id.toLowerCase().includes(lowerQuery)
        )
    }, [tasks, searchQuery])

    return (
        <div className="h-full w-full bg-background overflow-hidden relative">
            <TaskList
                tasks={filteredTasks}
                isLoading={isLoading}
                onTaskClick={(id) => setSelectedTaskId(id)}
                focusedTaskId={focusedTaskId}
                onFocusChange={setFocusedTaskId}
                onStatusChange={updateTaskStatus}
                onDelete={deleteTask}
                onNewTask={() => useUIStore.getState().setNewTaskModalOpen(true)}
                searchQuery={searchQuery}
            />
        </div>
    )
}
