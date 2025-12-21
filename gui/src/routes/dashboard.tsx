import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { DashboardView } from '@/features/dashboard/components/DashboardView'
import { useTasks } from '@/features/tasks/hooks/useTasks'

import { useUIStore } from '@/stores/uiStore'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/dashboard',
    component: Dashboard,
})

function Dashboard() {
    const { searchQuery } = useUIStore()
    const { selectedNamespace } = useUIStore()
    const { tasks, isLoading, projectName } = useTasks({
        namespace: selectedNamespace,
        allNamespaces: selectedNamespace === null,
    })

    // Filter tasks by search query
    const filteredTasks = tasks.filter(t =>
        !searchQuery ||
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.id.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="flex flex-1 w-full min-h-0 flex-col overflow-hidden bg-background">
            <DashboardView
                tasks={filteredTasks}
                isLoading={isLoading}
                projectName={projectName || undefined}
            />
        </div>
    )
}
