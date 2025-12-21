/**
 * Settings View - Application preferences and configuration
 * Uses zustand store for persistent settings
 */

import { useState, useCallback, useEffect } from "react";
import {
  Settings,
  Palette,
  Bell,
  Keyboard,
  Database,
  Info,
  ChevronRight,
  Moon,
  Sun,
  Monitor,
  Check,
  ExternalLink,
  Download,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { useSettingsStore, formatBytes, type ThemeMode, type StorageMode } from "@/stores/settingsStore";
import { setBackendStorageMode } from "@/lib/tauri";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { toast } from "@/components/common/toast";

interface SettingsViewProps {
  isLoading?: boolean;
}

// App version (would come from package.json in production)
const APP_VERSION = "0.1.0";
const GITHUB_URL = "https://github.com/anthropics/apply-task";
const LICENSE_URL = "https://opensource.org/licenses/MIT";

interface SettingsSectionProps {
  title: string;
  description?: string;
  icon: typeof Settings;
  children: React.ReactNode;
}

function SettingsSection({ title, description, icon: Icon, children }: SettingsSectionProps) {
  return (
    <div className="rounded-xl border border-border bg-background p-[var(--density-card-pad)]">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-[18px] w-[18px]" />
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {description && (
            <p className="mt-0.5 text-xs text-foreground-muted">{description}</p>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

interface ToggleProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function Toggle({ label, description, checked, onChange }: ToggleProps) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border/60 py-2.5 last:border-b-0">
      <div className="min-w-0">
        <div className="text-sm font-medium text-foreground">{label}</div>
        {description && (
          <div className="mt-0.5 text-xs text-foreground-muted">{description}</div>
        )}
      </div>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        aria-pressed={checked}
        className={cn(
          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          checked ? "bg-primary" : "bg-background-muted"
        )}
      >
        <span
          className={cn(
            "absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-5" : "translate-x-0"
          )}
        />
      </button>
    </div>
  );
}

interface SettingsRowProps {
  label: string;
  value?: string;
  icon?: typeof ChevronRight;
  onClick?: () => void;
  danger?: boolean;
}

function SettingsRow({ label, value, icon: Icon = ChevronRight, onClick, danger }: SettingsRowProps) {
  const content = (
    <>
      <span
        className={cn(
          "text-sm font-medium",
          danger ? "text-status-fail" : "text-foreground"
        )}
      >
        {label}
      </span>
      <div className="flex items-center gap-2">
        {value && <span className="text-sm text-foreground-muted">{value}</span>}
        {onClick && (
          <Icon
            className={cn(
              "h-4 w-4",
              danger ? "text-status-fail" : "text-foreground-subtle"
            )}
          />
        )}
      </div>
    </>
  );

  return onClick ? (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "-mx-2 flex w-full items-center justify-between gap-3 rounded-lg px-2 py-3 text-left transition-colors hover:bg-background-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "border-b border-border/60 last:border-b-0"
      )}
    >
      {content}
    </button>
  ) : (
    <div className="flex items-center justify-between gap-3 border-b border-border/60 py-3 last:border-b-0">
      {content}
    </div>
  );
}

// Keyboard shortcuts modal
interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function ShortcutsModal({ isOpen, onClose }: ShortcutsModalProps) {
	  const shortcuts = [
	    { key: "⌘ K", action: "Open command palette" },
	    { key: "⌘ N", action: "Create new step" },
	    { key: "j / k", action: "Navigate steps (List)" },
	    { key: "Enter", action: "Open selected step (List)" },
	    { key: "Esc", action: "Close modal" },
	    { key: "g b", action: "Go to Board" },
	    { key: "g l", action: "Go to List" },
    { key: "g t", action: "Go to Timeline" },
    { key: "g d", action: "Go to Dashboard" },
  ];

  return (
      <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="max-w-[440px]">
          <DialogHeader>
            <DialogTitle>Keyboard shortcuts</DialogTitle>
            <DialogDescription>
              Fast navigation without leaving the keyboard.
            </DialogDescription>
          </DialogHeader>
        <div className="max-h-[60vh] overflow-y-auto px-[var(--density-page-pad)] pb-[var(--density-page-pad)]">
          <div className="flex flex-col">
            {shortcuts.map(({ key, action }) => (
              <div
                key={key}
                className="flex items-center justify-between gap-4 border-b border-border/60 py-2 last:border-b-0"
              >
                <span className="text-sm text-foreground-muted">{action}</span>
                <kbd className="shrink-0 rounded-md border border-border bg-background-muted px-2 py-1 font-mono text-xs font-medium text-foreground">
                  {key}
                </kbd>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function SettingsView({ isLoading = false }: SettingsViewProps) {
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [storageModeSaving, setStorageModeSaving] = useState(false);

  // Get settings from store
  const {
    theme,
    compactMode,
    notifications,
    soundEffects,
    autoSave,
    vimMode,
    storageMode,
    cacheSize,
    setTheme,
    setCompactMode,
    setNotifications,
    setSoundEffects,
    setAutoSave,
    setVimMode,
    setStorageMode,
    setCacheSize,
    clearCache,
    exportData,
  } = useSettingsStore();

  // Calculate cache size on mount and after clear
  useEffect(() => {
    let total = 0;
    for (const key in localStorage) {
      if (Object.prototype.hasOwnProperty.call(localStorage, key)) {
        total += localStorage[key].length * 2; // UTF-16 = 2 bytes per char
      }
    }
    setCacheSize(total);
  }, [setCacheSize]);

  const handleStorageModeChange = useCallback(async (nextMode: StorageMode) => {
    const previous = storageMode;
    setStorageMode(nextMode);

    setStorageModeSaving(true);
    try {
      const resp = await setBackendStorageMode(nextMode);
      if (!resp.success) {
        setStorageMode(previous);
        toast.error(resp.error || "Failed to apply storage mode");
        return;
      }
      const label = nextMode === "local" ? "Local (.tasks)" : "Global (~/.tasks)";
      toast.success(`Storage mode set to ${label}${resp.restarted ? " (backend restarted)" : ""}`);
    } finally {
      setStorageModeSaving(false);
    }
  }, [storageMode, setStorageMode]);

  const handleClearCache = useCallback(async () => {
    setIsClearing(true);
    try {
      await clearCache();
    } finally {
      setIsClearing(false);
    }
  }, [clearCache]);

  const handleExportData = useCallback(async () => {
    setIsExporting(true);
    try {
      await exportData();
    } finally {
      setIsExporting(false);
    }
  }, [exportData]);

  const handleOpenLink = useCallback((url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  }, []);

  if (isLoading) {
    return <SettingsSkeleton />;
  }

  const themeOptions: { mode: ThemeMode; icon: typeof Sun; label: string }[] = [
    { mode: "light", icon: Sun, label: "Light" },
    { mode: "dark", icon: Moon, label: "Dark" },
    { mode: "system", icon: Monitor, label: "System" },
  ];

  return (
    <>
      <div className="mx-auto flex w-full max-w-[920px] flex-1 flex-col gap-[var(--density-page-gap)] overflow-y-auto p-[var(--density-page-pad)]">
        {/* Header */}
        <div>
          <h2 className="text-lg font-semibold text-foreground">Settings</h2>
          <p className="mt-0.5 text-sm text-foreground-muted">
            Manage your preferences and app configuration
          </p>
        </div>

        <div className="grid grid-cols-1 gap-[var(--density-page-gap)] lg:grid-cols-2">
          {/* Appearance */}
          <SettingsSection
            title="Appearance"
            description="Customize how the app looks"
            icon={Palette}
          >
            <div className="mb-4">
              <div className="mb-2.5 text-xs font-medium text-foreground-muted">
                Theme
              </div>
              <div className="flex gap-2">
                {themeOptions.map(({ mode, icon: Icon, label }) => (
                  <button
                    key={mode}
                    onClick={() => setTheme(mode)}
                    type="button"
                    className={cn(
                      "flex flex-1 flex-col items-center gap-2 rounded-lg border-2 p-2.5 transition-colors",
                      theme === mode
                        ? "border-primary bg-primary/5"
                        : "border-border hover:bg-background-muted/60"
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-5 w-5",
                        theme === mode ? "text-primary" : "text-foreground-muted"
                      )}
                    />
                    <span
                      className={cn(
                        "text-xs font-medium",
                        theme === mode ? "text-primary" : "text-foreground-muted"
                      )}
                    >
                      {label}
                    </span>
                    {theme === mode && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            <Toggle
              label="Compact mode"
              description="Reduce spacing and show more content"
              checked={compactMode}
              onChange={setCompactMode}
            />
          </SettingsSection>

          {/* Notifications */}
          <SettingsSection
            title="Notifications"
            description="Manage notification preferences"
            icon={Bell}
          >
              <Toggle
                label="Enable notifications"
              description="Get notified about step updates"
                checked={notifications}
                onChange={setNotifications}
              />
            <Toggle
              label="Sound effects"
              description="Play sounds for actions"
              checked={soundEffects}
              onChange={setSoundEffects}
            />
          </SettingsSection>

          {/* Keyboard */}
          <SettingsSection
            title="Keyboard Shortcuts"
            description="Customize keyboard navigation"
            icon={Keyboard}
          >
            <SettingsRow
              label="View all shortcuts"
              value="⌘ /"
              onClick={() => setShowShortcuts(true)}
            />
            <Toggle
              label="Vim mode"
              description="Enable vim-style navigation (h/j/k/l)"
              checked={vimMode}
              onChange={setVimMode}
            />
          </SettingsSection>

          {/* Data */}
          <SettingsSection title="Data & Storage" description="Manage your data" icon={Database}>
            <div className="flex items-center justify-between gap-4 border-b border-border/60 py-2.5 last:border-b-0">
              <div className="min-w-0">
                <div className="text-sm font-medium text-foreground">Storage mode</div>
                <div className="mt-0.5 text-xs text-foreground-muted">
                  Global keeps steps in your home folder; Local uses this project's <code>.tasks</code>
                </div>
              </div>
              <select
                value={storageMode}
                onChange={(e) => {
                  const next = e.target.value as StorageMode;
                  if (next !== "global" && next !== "local") return;
                  void handleStorageModeChange(next);
                }}
                disabled={storageModeSaving}
                className="flex h-8 w-[160px] rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="global">Global</option>
                <option value="local">Local</option>
              </select>
            </div>
            <Toggle
              label="Auto-save"
              description="Automatically save changes"
              checked={autoSave}
              onChange={setAutoSave}
            />
            <SettingsRow
              label="Export data"
              icon={Download}
              value={isExporting ? "Exporting..." : undefined}
              onClick={handleExportData}
            />
            <SettingsRow
              label="Clear cache"
              icon={isClearing ? RefreshCw : Trash2}
              value={formatBytes(cacheSize)}
              onClick={handleClearCache}
            />
          </SettingsSection>

          {/* About */}
          <div className="lg:col-span-2">
            <SettingsSection title="About" description="Application information" icon={Info}>
              <SettingsRow label="Version" value={APP_VERSION} />
              <SettingsRow
                label="View on GitHub"
                icon={ExternalLink}
                onClick={() => handleOpenLink(GITHUB_URL)}
              />
              <SettingsRow
                label="View license"
                icon={ExternalLink}
                onClick={() => handleOpenLink(LICENSE_URL)}
              />
              <SettingsRow
                label="Report an issue"
                icon={ExternalLink}
                onClick={() => handleOpenLink(`${GITHUB_URL}/issues/new`)}
              />
            </SettingsSection>
          </div>
        </div>
      </div>

      {/* Shortcuts Modal */}
      <ShortcutsModal isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
    </>
  );
}

function SettingsSkeleton() {
  return (
    <div
      style={{
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        maxWidth: "640px",
      }}
    >
      <div>
        <div
          className="skeleton"
          style={{ height: "24px", width: "100px", marginBottom: "8px", borderRadius: "4px" }}
        />
        <div className="skeleton" style={{ height: "16px", width: "280px", borderRadius: "4px" }} />
      </div>
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="skeleton" style={{ height: "160px", borderRadius: "12px" }} />
      ))}
    </div>
  );
}
