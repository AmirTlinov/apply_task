import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { TimelineView } from '@/features/timeline/components/TimelineView'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { useUIStore } from '@/stores/uiStore'
import { useNavigate } from '@tanstack/react-router'
import { useMediaQuery } from '@/hooks/useMediaQuery'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/timeline',
    component: Timeline,
})

function Timeline() {
    const { searchQuery, selectedNamespace } = useUIStore()
    const openDetailPanel = useUIStore((s) => s.openDetailPanel)
    const { tasks, isLoading } = useTasks({
        namespace: selectedNamespace,
        allNamespaces: selectedNamespace === null,
    })
    const navigate = useNavigate()
    const isMobile = useMediaQuery("(max-width: 767px)")

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
    }

    // Filter tasks by search query
    const filteredTasks = tasks.filter(t =>
        !searchQuery ||
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.id.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="flex flex-1 w-full min-h-0 flex-col overflow-hidden bg-background">
            <TimelineView
                key={selectedNamespace ?? "all"}
                tasks={filteredTasks}
                isLoading={isLoading}
                onTaskClick={openTask}
                selectedNamespace={selectedNamespace}
            />
        </div>
    )
}
