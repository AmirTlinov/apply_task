import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { TimelineView } from '@/features/timeline/components/TimelineView'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { useUIStore } from '@/stores/uiStore'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/timeline',
    component: Timeline,
})

function Timeline() {
    const { searchQuery, setSelectedTaskId } = useUIStore()
    const { tasks, isLoading } = useTasks({ allNamespaces: true })

    // Filter tasks by search query
    const filteredTasks = tasks.filter(t =>
        !searchQuery ||
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.id.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="h-full w-full overflow-hidden bg-background">
            <TimelineView
                tasks={filteredTasks}
                isLoading={isLoading}
                onTaskClick={setSelectedTaskId}
            />
        </div>
    )
}
