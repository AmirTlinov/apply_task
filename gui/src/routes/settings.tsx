import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/settings',
    component: Settings,
})

function Settings() {
    return <div className="p-4">Settings View (Coming Soon)</div>
}
