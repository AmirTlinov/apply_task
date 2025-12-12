import { create } from "zustand";

interface UIState {
    // Sidebar
    sidebarCollapsed: boolean;
    toggleSidebar: () => void;
    setSidebarCollapsed: (collapsed: boolean) => void;

    // Command Palette
    isPaletteOpen: boolean;
    setPaletteOpen: (open: boolean) => void;
    togglePalette: () => void;

    // Modals
    newTaskModalOpen: boolean;
    setNewTaskModalOpen: (open: boolean) => void;

    // Task Detail
    selectedTaskId: string | null;
    setSelectedTaskId: (taskId: string | null) => void;

    // Filter State (formerly in App.tsx)
    searchQuery: string;
    setSearchQuery: (query: string) => void;
    selectedNamespace: string | null;
    setSelectedNamespace: (namespace: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
    sidebarCollapsed: false,
    toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

    isPaletteOpen: false,
    setPaletteOpen: (open) => set({ isPaletteOpen: open }),
    togglePalette: () => set((state) => ({ isPaletteOpen: !state.isPaletteOpen })),

    newTaskModalOpen: false,
    setNewTaskModalOpen: (open) => set({ newTaskModalOpen: open }),

    selectedTaskId: null,
    setSelectedTaskId: (taskId) => set({ selectedTaskId: taskId }),

    searchQuery: "",
    setSearchQuery: (query) => set({ searchQuery: query }),
    selectedNamespace: null,
    setSelectedNamespace: (namespace) => set({ selectedNamespace: namespace }),
}));
