import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { SettingsView } from '@/features/settings/components/SettingsView'

export const Route = createRoute({
    getParentRoute: () => rootRoute,
    path: '/settings',
    component: Settings,
})

function Settings() {
    return <SettingsView />
}
