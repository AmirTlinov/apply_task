import { createRouter } from '@tanstack/react-router'
import { Route as rootRoute } from './routes/__root'
import { Route as indexRoute } from './routes/index'
import { Route as boardRoute } from './routes/board'
import { Route as timelineRoute } from './routes/timeline'
import { Route as dashboardRoute } from './routes/dashboard'
import { Route as projectsRoute } from './routes/projects'
import { Route as settingsRoute } from './routes/settings'

// Build the route tree
const routeTree = rootRoute.addChildren([
    indexRoute,
    boardRoute,
    timelineRoute,
    dashboardRoute,
    projectsRoute,
    settingsRoute,
])

// Create the router
export const router = createRouter({ routeTree })

// Register the router for type safety
declare module '@tanstack/react-router' {
    interface Register {
        router: typeof router
    }
}
