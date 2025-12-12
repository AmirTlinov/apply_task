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
    const { tasks, isLoading, projectName } = useTasks({ allNamespaces: true })

    // Filter tasks by search query
    const filteredTasks = tasks.filter(t =>
        !searchQuery ||
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.id.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="h-full w-full overflow-hidden bg-background">
            <DashboardView
                tasks={filteredTasks}
                isLoading={isLoading}
                projectName={projectName || undefined}
            />
        </div>
    )
}
