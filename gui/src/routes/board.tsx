import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { KanbanBoard } from '@/features/board/components/KanbanBoard'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { useUIStore } from '@/stores/uiStore'
import { useNavigate } from '@tanstack/react-router'
import { useMediaQuery } from '@/hooks/useMediaQuery'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/board',
    component: Board,
})

function Board() {
    const { searchQuery, selectedNamespace } = useUIStore()
    const openDetailPanel = useUIStore((s) => s.openDetailPanel)
    const { tasks, isLoading, updateTaskStatus, deleteTask } = useTasks({
        namespace: selectedNamespace,
        allNamespaces: selectedNamespace === null,
    })
    const { setNewTaskModalOpen } = useUIStore()
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
            <KanbanBoard
                key={selectedNamespace ?? "all"}
                tasks={filteredTasks}
                isLoading={isLoading}
                onTaskClick={openTask}
                onNewTask={() => setNewTaskModalOpen(true)}
                onStatusChange={updateTaskStatus}
                onDelete={deleteTask}
            />
        </div>
    )
}
