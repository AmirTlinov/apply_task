/**
 * Settings Store - Persistent application settings with zustand
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { toast } from "@/components/common/toast";

export type ThemeMode = "light" | "dark" | "system";
export type TasksViewMode = "cards" | "table";
export type StorageMode = "global" | "local";

interface SettingsState {
  // Appearance
  theme: ThemeMode;
  compactMode: boolean;
  tasksViewMode: TasksViewMode;
  subtasksViewMode: TasksViewMode;

  // Projects
  archivedNamespaces: string[];

  // Notifications
  notifications: boolean;
  soundEffects: boolean;

  // Data
  autoSave: boolean;
  vimMode: boolean;
  storageMode: StorageMode;

  // Computed/cached
  cacheSize: number; // in bytes

  // Actions
  setTheme: (theme: ThemeMode) => void;
  setCompactMode: (enabled: boolean) => void;
  setTasksViewMode: (mode: TasksViewMode) => void;
  setSubtasksViewMode: (mode: TasksViewMode) => void;
  setNotifications: (enabled: boolean) => void;
  setSoundEffects: (enabled: boolean) => void;
  setAutoSave: (enabled: boolean) => void;
  setVimMode: (enabled: boolean) => void;
  setStorageMode: (mode: StorageMode) => void;
  archiveNamespace: (namespace: string) => void;
  restoreNamespace: (namespace: string) => void;
  setCacheSize: (size: number) => void;
  clearCache: () => Promise<void>;
  exportData: () => Promise<void>;
  resetSettings: () => void;
}

const DEFAULT_SETTINGS = {
  theme: "system" as ThemeMode,
  compactMode: true,
  tasksViewMode: "table" as TasksViewMode,
  subtasksViewMode: "table" as TasksViewMode,
  archivedNamespaces: [] as string[],
  notifications: true,
  soundEffects: true,
  autoSave: true,
  vimMode: false,
  storageMode: "global" as StorageMode,
  cacheSize: 0,
};

type ResolvedTheme = Exclude<ThemeMode, "system">;

function resolveTheme(theme: ThemeMode): ResolvedTheme {
  if (theme === "dark") return "dark";
  if (theme === "light") return "light";

  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return "light";
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyResolvedTheme(resolved: ResolvedTheme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", resolved === "dark");
  root.setAttribute("data-theme", resolved);
}

// Calculate localStorage cache size
function calculateCacheSize(): number {
  let total = 0;
  for (const key in localStorage) {
    if (Object.prototype.hasOwnProperty.call(localStorage, key)) {
      total += localStorage[key].length * 2; // UTF-16 = 2 bytes per char
    }
  }
  return total;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      ...DEFAULT_SETTINGS,

      setTheme: (theme) => {
        set({ theme });
        const state = get();
        applyResolvedTheme(resolveTheme(state.theme));
        const themeNames = { light: "Light", dark: "Dark", system: "System" };
        toast.success(`Theme changed to ${themeNames[theme]}`);
      },

      setCompactMode: (compactMode) => {
        document.documentElement.setAttribute(
          "data-compact",
          compactMode ? "true" : "false"
        );
        set({ compactMode });
        toast.info(compactMode ? "Compact mode enabled" : "Compact mode disabled");
      },

      setTasksViewMode: (tasksViewMode) => {
        set({ tasksViewMode });
      },

      setSubtasksViewMode: (subtasksViewMode) => {
        set({ subtasksViewMode });
      },

      setNotifications: (notifications) => {
        set({ notifications });
        toast.info(notifications ? "Notifications enabled" : "Notifications disabled");
      },
      setSoundEffects: (soundEffects) => {
        set({ soundEffects });
        toast.info(soundEffects ? "Sound effects enabled" : "Sound effects disabled");
      },
      setAutoSave: (autoSave) => {
        set({ autoSave });
        toast.info(autoSave ? "Auto-save enabled" : "Auto-save disabled");
      },
      setVimMode: (vimMode) => {
        set({ vimMode });
        toast.info(vimMode ? "Vim mode enabled" : "Vim mode disabled");
      },
      setStorageMode: (storageMode) => {
        set({ storageMode });
      },

      archiveNamespace: (namespace) => {
        const current = get().archivedNamespaces;
        if (current.includes(namespace)) return;
        set({ archivedNamespaces: [...current, namespace] });
        toast.info(`Project ${namespace} archived`);
      },

      restoreNamespace: (namespace) => {
        const current = get().archivedNamespaces;
        set({ archivedNamespaces: current.filter((n) => n !== namespace) });
        toast.success(`Project ${namespace} restored`);
      },
      setCacheSize: (cacheSize) => set({ cacheSize }),

      clearCache: async () => {
        // Clear all localStorage except settings
        const settingsKey = "apply-task-settings";
        const settings = localStorage.getItem(settingsKey);

        // Clear caches (in a real app, would also clear IndexedDB, etc.)
        const keysToRemove: string[] = [];
        for (const key in localStorage) {
          if (key !== settingsKey && Object.prototype.hasOwnProperty.call(localStorage, key)) {
            keysToRemove.push(key);
          }
        }
        const clearedCount = keysToRemove.length;
        keysToRemove.forEach((key) => localStorage.removeItem(key));

        // Restore settings
        if (settings) {
          localStorage.setItem(settingsKey, settings);
        }

        set({ cacheSize: calculateCacheSize() });
        toast.success(`Cache cleared (${clearedCount} items removed)`);
      },

      exportData: async () => {
        try {
          // Collect all app data
          const data = {
            settings: get(),
            exportedAt: new Date().toISOString(),
            version: "0.1.0",
          };

          // Create and download JSON file
          const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: "application/json",
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `apply-task-export-${new Date().toISOString().split("T")[0]}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          toast.success("Data exported successfully");
        } catch (err) {
          toast.error("Failed to export data");
          throw err;
        }
      },

      resetSettings: () => {
        set(DEFAULT_SETTINGS);
        const state = get();
        applyResolvedTheme(resolveTheme(state.theme));
        document.documentElement.setAttribute("data-compact", state.compactMode ? "true" : "false");
        toast.success("Settings reset to defaults");
      },
    }),
    {
      name: "apply-task-settings",
      version: 1,
      migrate: (persistedState) => {
        if (!persistedState || typeof persistedState !== "object") return persistedState as SettingsState;
        const migrated = { ...(persistedState as Record<string, unknown>) };
        delete migrated.pajamaMode;
        delete migrated.pajamaStartMinutes;
        delete migrated.pajamaEndMinutes;
        if (migrated.tasksViewMode === "tree") migrated.tasksViewMode = "table";
        if (migrated.subtasksViewMode === "tree") migrated.subtasksViewMode = "table";
        return migrated as unknown as SettingsState;
      },
    }
  )
);

// Apply settings after hydration from localStorage
if (typeof window !== "undefined") {
  // Use a small delay to ensure store is hydrated
  setTimeout(() => {
    const state = useSettingsStore.getState();
    applyResolvedTheme(resolveTheme(state.theme));
    document.documentElement.setAttribute("data-compact", state.compactMode ? "true" : "false");
    state.setCacheSize(calculateCacheSize());
  }, 0);
}

// Subscribe to system theme changes
if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    const state = useSettingsStore.getState();
    if (state.theme === "system") {
      applyResolvedTheme(resolveTheme(state.theme));
    }
  });
}

// Helper to format bytes
export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}
