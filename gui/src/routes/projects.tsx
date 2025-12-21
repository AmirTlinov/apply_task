import { createRoute, useNavigate } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { ProjectsView } from '@/features/projects/components/ProjectsView'
import { useTasks } from '@/features/tasks/hooks/useTasks'
import { useUIStore } from '@/stores/uiStore'
import { openProject } from '@/lib/tauri'
import { toast } from '@/components/common/toast'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/projects',
    component: Projects,
})

function Projects() {
    const {
        tasks,
        isLoading,
        namespaces,
        projectName,
        projectPath,
        refresh
    } = useTasks({ allNamespaces: true })

    const { setSelectedNamespace } = useUIStore()
    const navigate = useNavigate()

    const handleOpenProject = async () => {
        const result = await openProject();
        if (result.success && result.path) {
            toast.success(`Opened project: ${result.path}`);
            refresh();
        } else if (result.error) {
            toast.error(result.error);
        }
    }

    return (
        <div className="flex flex-1 w-full min-h-0 flex-col bg-background overflow-hidden relative">
            <ProjectsView
                tasks={tasks}
                projectName={projectName || undefined}
                projectPath={projectPath || undefined}
                namespaces={namespaces}
                isLoading={isLoading}
                onOpenProject={handleOpenProject}
                onRefresh={refresh}
                onSelectNamespace={(ns) => {
                    setSelectedNamespace(ns);
                    navigate({ to: '/' })
                }}
            />
        </div>
    )
}
