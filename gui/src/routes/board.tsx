import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { KanbanBoard } from '@/features/board/components/KanbanBoard'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { useUIStore } from '@/stores/uiStore'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/board',
    component: Board,
})

function Board() {
    const { searchQuery } = useUIStore()
    const { tasks, isLoading, updateTaskStatus, deleteTask } = useTasks({ allNamespaces: true })
    const { setNewTaskModalOpen, setSelectedTaskId } = useUIStore()

    // Filter tasks by search query
    const filteredTasks = tasks.filter(t =>
        !searchQuery ||
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.id.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="h-full w-full overflow-hidden bg-background">
            <KanbanBoard
                tasks={filteredTasks}
                isLoading={isLoading}
                onTaskClick={setSelectedTaskId}
                onNewTask={() => setNewTaskModalOpen(true)}
                onStatusChange={updateTaskStatus}
                onDelete={deleteTask}
            />
        </div>
    )
}
