import { create } from "zustand";

interface DetailPanelTarget {
  taskId: string;
  domain?: string;
  namespace?: string;
  subtaskPath?: string;
}

interface UIState {
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
    toggleSidebarOpen: () => void;

    // Command Palette
    isPaletteOpen: boolean;
    setPaletteOpen: (open: boolean) => void;
    togglePalette: () => void;

    // Operation history (undo/redo)
    historyModalOpen: boolean;
    setHistoryModalOpen: (open: boolean) => void;

    // Modals
    newTaskModalOpen: boolean;
    setNewTaskModalOpen: (open: boolean) => void;

    // Filter State (formerly in App.tsx)
    searchQuery: string;
    setSearchQuery: (query: string) => void;
    selectedNamespace: string | null;
    setSelectedNamespace: (namespace: string | null) => void;

    // Task detail panel (desktop)
    detailPanel: DetailPanelTarget | null;
    openDetailPanel: (target: DetailPanelTarget) => void;
    closeDetailPanel: () => void;
    setDetailSubtaskPath: (subtaskPath?: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
    sidebarOpen: false,
    setSidebarOpen: (open) => set({ sidebarOpen: open }),
    toggleSidebarOpen: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    isPaletteOpen: false,
    setPaletteOpen: (open) => set({ isPaletteOpen: open }),
    togglePalette: () => set((state) => ({ isPaletteOpen: !state.isPaletteOpen })),

    historyModalOpen: false,
    setHistoryModalOpen: (open) => set({ historyModalOpen: open }),

    newTaskModalOpen: false,
    setNewTaskModalOpen: (open) => set({ newTaskModalOpen: open }),

    searchQuery: "",
    setSearchQuery: (query) => set({ searchQuery: query }),
    selectedNamespace: null,
    setSelectedNamespace: (namespace) => set({ selectedNamespace: namespace, detailPanel: null }),

    detailPanel: null,
    openDetailPanel: (target) => set({ detailPanel: target }),
    closeDetailPanel: () => set({ detailPanel: null }),
    setDetailSubtaskPath: (subtaskPath) =>
      set((state) => {
        if (!state.detailPanel) return state;
        return {
          ...state,
          detailPanel: {
            ...state.detailPanel,
            subtaskPath,
          },
        };
      }),
}));
