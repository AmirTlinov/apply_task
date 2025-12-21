import { Search, Plus, RefreshCw, Command, ChevronDown, FolderOpen, Menu, History, Undo2, Redo2 } from "lucide-react";
import { useState, useRef } from "react";
import type { Namespace } from "@/types/task";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
  subtitle?: string;
  taskCount?: number;
  onMenu?: () => void;
  onSearch?: (query: string) => void;
  onNewTask?: () => void;
  onRefresh?: () => void;
  onCommandPalette?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onOpenHistory?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
  historyDisabledReason?: string;
  isLoading?: boolean;
  namespaces?: Namespace[];
  selectedNamespace?: string | null;
  onNamespaceChange?: (namespace: string | null) => void;
}

export function Header({
  title,
  subtitle,
  taskCount,
  onMenu,
  onSearch,
  onNewTask,
  onRefresh,
  onCommandPalette,
  onUndo,
  onRedo,
  onOpenHistory,
  canUndo = false,
  canRedo = false,
  historyDisabledReason,
  isLoading = false,
  namespaces = [],
  selectedNamespace,
  onNamespaceChange,
}: HeaderProps) {
  const [searchValue, setSearchValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Get display name for selected namespace
  const getNamespaceDisplayName = () => {
    if (!selectedNamespace) return "All Projects";
    const ns = namespaces.find((n) => n.namespace === selectedNamespace);
    return ns?.namespace || selectedNamespace;
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    onSearch?.(value);
  };

  return (
    <header className="flex shrink-0 items-center justify-between gap-4 border-b border-border bg-background px-[var(--density-shell-px)] py-[var(--density-header-py)] min-h-[var(--density-header-min-h)]">
      {/* Left: Title & Project Selector */}
      <div className="flex shrink-0 items-center gap-4">
        {onMenu && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenu}
            className="h-8 w-8 rounded-xl border border-border bg-background hover:bg-background-muted md:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-4 w-4 text-foreground-muted" />
          </Button>
        )}
        <div>
          <h1 className="m-0 text-base font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-0.5 text-xs text-foreground-muted">
              {subtitle}
            </p>
          )}
        </div>

        {/* Project/Namespace Selector */}
        {namespaces.length > 0 && onNamespaceChange && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-2 px-3 font-normal bg-background hover:bg-background-muted border-border"
              >
                <FolderOpen className="h-3.5 w-3.5 text-foreground-muted" />
                <span className="max-w-[150px] truncate">
                  {getNamespaceDisplayName()}
                </span>
                <ChevronDown className="h-3.5 w-3.5 text-foreground-muted opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-[240px]">
              <DropdownMenuItem
                onClick={() => onNamespaceChange(null)}
                className={cn(
                    "gap-2",
                    selectedNamespace === null && "bg-primary-subtle text-primary focus:bg-primary-subtle focus:text-primary"
                )}
              >
                <FolderOpen className={cn("h-4 w-4", selectedNamespace === null ? "text-primary" : "text-foreground-muted")} />
                <span className="font-medium">All Projects</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <div className="max-h-[300px] overflow-y-auto">
                {namespaces.map((ns) => (
                  <DropdownMenuItem
                    key={ns.namespace}
                    onClick={() => onNamespaceChange(ns.namespace)}
                    className={cn(
                        "justify-between gap-2",
                        selectedNamespace === ns.namespace && "bg-primary-subtle text-primary focus:bg-primary-subtle focus:text-primary"
                    )}
                  >
                    <div className="flex items-center gap-2 overflow-hidden">
                      <FolderOpen className={cn("h-4 w-4 shrink-0", selectedNamespace === ns.namespace ? "text-primary" : "text-foreground-muted")} />
                      <span className="truncate">{ns.namespace}</span>
                    </div>
                    <span className="rounded bg-background-muted px-1.5 py-0.5 text-[10px] text-foreground-subtle">
                      {ns.task_count}
                    </span>
                  </DropdownMenuItem>
                ))}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Task Count */}
        {typeof taskCount === "number" && (
          <span className="hidden sm:inline-flex rounded-full bg-background-muted px-2 py-0.5 text-xs font-medium text-foreground-muted">
            {taskCount} task{taskCount !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Center: Search / Command Palette Trigger */}
      {(onSearch || onCommandPalette) && (
        <div className="relative flex-1 max-w-[480px]">
          <Search
            className={cn(
              "absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 transition-colors",
              isFocused ? "text-primary" : "text-foreground-subtle"
            )}
          />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search tasks..."
            value={searchValue}
            onChange={handleSearchChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            className={cn(
              "h-8 w-full rounded-xl border bg-background-subtle pl-[42px] pr-[84px] text-sm text-foreground placeholder:text-foreground-subtle outline-none transition-all",
              isFocused
                ? "border-primary ring-2 ring-primary-subtle"
                : "border-border hover:border-foreground-subtle/30"
            )}
          />
          {/* Keyboard shortcut hint */}
          <div
            onClick={() => onCommandPalette?.()}
            className={cn(
                "absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-1",
                onCommandPalette ? "cursor-pointer" : "pointer-events-none"
            )}
          >
            <kbd className="inline-flex h-5 items-center gap-0.5 rounded border border-border bg-background px-1.5 font-mono text-[10px] font-medium text-foreground-subtle shadow-sm">
              <Command className="h-2.5 w-2.5" />
              <span>K</span>
            </kbd>
          </div>
        </div>
      )}

      {/* Right: Actions */}
      <div className="flex shrink-0 items-center gap-2.5">
        {(onUndo || onRedo || onOpenHistory) && (
          <div className="hidden sm:flex items-center gap-2">
            {onUndo && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onUndo}
                disabled={Boolean(historyDisabledReason) || !canUndo || isLoading}
                className="h-8 w-8 rounded-xl border border-border bg-background hover:bg-background-muted"
                title={historyDisabledReason || (!canUndo ? "Nothing to undo" : "Undo (Ctrl/⌘+Z)")}
              >
                <Undo2 className="h-4 w-4 text-foreground-muted" />
              </Button>
            )}
            {onRedo && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onRedo}
                disabled={Boolean(historyDisabledReason) || !canRedo || isLoading}
                className="h-8 w-8 rounded-xl border border-border bg-background hover:bg-background-muted"
                title={historyDisabledReason || (!canRedo ? "Nothing to redo" : "Redo (Ctrl/⌘+Shift+Z)")}
              >
                <Redo2 className="h-4 w-4 text-foreground-muted" />
              </Button>
            )}
            {onOpenHistory && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onOpenHistory}
                disabled={Boolean(historyDisabledReason) || isLoading}
                className="h-8 w-8 rounded-xl border border-border bg-background hover:bg-background-muted"
                title={historyDisabledReason || "Open history"}
              >
                <History className="h-4 w-4 text-foreground-muted" />
              </Button>
            )}
          </div>
        )}

        {onRefresh && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onRefresh}
            disabled={isLoading}
            className="h-8 w-8 rounded-xl border border-border bg-background hover:bg-background-muted"
            title="Refresh (R)"
          >
            <RefreshCw
              className={cn(
                  "h-4 w-4 text-foreground-muted",
                  isLoading && "animate-spin"
              )}
            />
          </Button>
        )}

        {onNewTask && (
          <Button
            onClick={onNewTask}
            className="h-8 gap-2 rounded-xl bg-primary px-3 font-medium text-white shadow-sm hover:bg-primary-hover transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">New Task</span>
          </Button>
        )}
      </div>
    </header>
  );
}
