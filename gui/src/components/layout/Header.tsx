import { Search, Plus, RefreshCw, Command, ChevronDown, FolderOpen, Play, Pause, Square, SkipForward, Send } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import type { Namespace } from "@/types/task";
import type { AIStatusSnapshot } from "@/hooks/useAIStatus";
import { sendAISignal } from "@/lib/tauri";
import { toast } from "@/components/common/Toast";
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
  onSearch?: (query: string) => void;
  onNewTask?: () => void;
  onRefresh?: () => void;
  onCommandPalette?: () => void;
  isLoading?: boolean;
  namespaces?: Namespace[];
  selectedNamespace?: string | null;
  onNamespaceChange?: (namespace: string | null) => void;
  aiStatus?: AIStatusSnapshot;
}

export function Header({
  title,
  subtitle,
  taskCount,
  onSearch,
  onNewTask,
  onRefresh,
  onCommandPalette,
  isLoading = false,
  namespaces = [],
  selectedNamespace,
  onNamespaceChange,
  aiStatus,
}: HeaderProps) {
  const [searchValue, setSearchValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [signalMessage, setSignalMessage] = useState("");
  const [isSendingSignal, setIsSendingSignal] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Get display name for selected namespace
  const getNamespaceDisplayName = () => {
    if (!selectedNamespace) return "All Projects";
    const ns = namespaces.find((n) => n.namespace === selectedNamespace);
    return ns?.namespace || selectedNamespace;
  };

  // Keyboard shortcut: Cmd/Ctrl + K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (onCommandPalette) {
          onCommandPalette();
        } else {
          inputRef.current?.focus();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onCommandPalette]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    onSearch?.(value);
  };

  const handleAiSignal = async (
    signal: "pause" | "resume" | "stop" | "skip" | "message",
    message?: string
  ) => {
    if (isSendingSignal) return;
    setIsSendingSignal(true);
    try {
      await sendAISignal(signal, message);
      if (signal === "message") {
        setSignalMessage("");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to send AI signal");
    } finally {
      setIsSendingSignal(false);
    }
  };

  return (
    <header className="flex shrink-0 items-center justify-between gap-5 border-b border-border bg-background px-6 py-3.5 min-h-[60px]">
      {/* Left: Title & Project Selector */}
      <div className="flex shrink-0 items-center gap-4">
        <div>
          <h1 className="m-0 text-[17px] font-semibold tracking-tight text-foreground">
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
          <span className="rounded-full bg-background-muted px-2.5 py-1 text-xs font-medium text-foreground-muted">
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
              "h-10 w-full rounded-xl border bg-background-subtle pl-[42px] pr-[90px] text-sm text-foreground placeholder:text-foreground-subtle outline-none transition-all",
              isFocused
                ? "border-primary ring-4 ring-primary-subtle"
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
        {aiStatus && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                    "h-10 gap-2 px-2.5 font-semibold",
                     aiStatus.status === "paused"
                      ? "text-status-warn border-status-warn/30 bg-status-warn-subtle/50"
                      : aiStatus.status === "error"
                        ? "text-status-fail border-status-fail/30 bg-status-fail-subtle/50"
                        : "text-foreground"
                )}
              >
                <span>AI</span>
                <span className="font-medium text-foreground-muted">{aiStatus.status}</span>
                {aiStatus.current?.op && (
                    <span className="font-medium hidden sm:inline-block">· {aiStatus.current.op}</span>
                )}
                {aiStatus.plan && (
                    <span className="font-medium text-foreground-muted hidden md:inline-block">({aiStatus.plan.progress})</span>
                )}
                <ChevronDown className="h-3 w-3 text-foreground-subtle opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[320px] p-0">
               <div className="flex flex-col gap-2 p-3">
                  <div className="text-xs text-foreground-muted">
                    Status: <span className="font-medium text-foreground">{aiStatus.status}</span>
                    {aiStatus.current?.task ? ` · ${aiStatus.current.task}` : ""}
                  </div>

                  <div className="flex flex-wrap gap-1.5">
                    {aiStatus.status === "paused" ? (
                      <Button
                        size="sm"
                        variant="default"
                        className="h-7 bg-status-ok hover:bg-status-ok/90 text-white"
                        onClick={() => handleAiSignal("resume")}
                        disabled={isSendingSignal}
                      >
                        <Play className="mr-1.5 h-3 w-3" /> Resume
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-7 bg-status-warn-subtle text-status-warn hover:bg-status-warn-subtle/80"
                        onClick={() => handleAiSignal("pause")}
                        disabled={isSendingSignal}
                      >
                        <Pause className="mr-1.5 h-3 w-3" /> Pause
                      </Button>
                    )}
                    <Button
                         size="sm"
                         variant="ghost"
                         className="h-7"
                         onClick={() => handleAiSignal("skip")}
                         disabled={isSendingSignal}
                    >
                         <SkipForward className="mr-1.5 h-3 w-3" /> Skip
                    </Button>
                     <Button
                         size="sm"
                         variant="ghost"
                         className="h-7 text-status-fail hover:text-status-fail hover:bg-status-fail-subtle"
                         onClick={() => handleAiSignal("stop")}
                         disabled={isSendingSignal}
                    >
                         <Square className="mr-1.5 h-3 w-3 fill-current" /> Stop
                    </Button>
                  </div>

                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={signalMessage}
                      onChange={(e) => setSignalMessage(e.target.value)}
                      placeholder="Message to AI..."
                      disabled={isSendingSignal}
                      className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-xs outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                      onKeyDown={(e) => {
                          if (e.key === "Enter" && signalMessage.trim() && !isSendingSignal) {
                              handleAiSignal("message", signalMessage.trim());
                          }
                      }}
                    />
                    <Button
                        size="sm"
                        variant="secondary"
                        className="h-[30px] px-2"
                        onClick={() => handleAiSignal("message", signalMessage.trim())}
                        disabled={!signalMessage.trim() || isSendingSignal}
                    >
                        <Send className="h-3 w-3" />
                    </Button>
                  </div>

                  {aiStatus.signal?.pending && (
                     <div className="rounded bg-background-muted px-2 py-1 text-[11px] text-foreground-muted">
                        Pending: {aiStatus.signal.pending}
                        {aiStatus.signal.message ? ` · ${aiStatus.signal.message}` : ""}
                     </div>
                  )}
               </div>

               {aiStatus.plan && (
                 <>
                   <DropdownMenuSeparator />
                   <div className="p-3">
                      <div className="mb-2 text-xs font-semibold">
                        Plan ({aiStatus.plan.progress})
                      </div>
                      <div className="flex flex-col gap-1 max-h-[200px] overflow-y-auto pr-1 custom-scrollbar">
                        {aiStatus.plan.steps.map((step, idx) => (
                          <div
                            key={`${idx}-${step}`}
                            className={cn(
                                "rounded px-2 py-1 text-xs",
                                idx < aiStatus.plan!.current
                                  ? "bg-status-ok-subtle text-status-ok opacity-70"
                                  : idx === aiStatus.plan!.current
                                    ? "bg-primary-subtle text-primary font-medium border border-primary/20"
                                    : "text-foreground-muted"
                            )}
                          >
                            <span className="mr-1.5 opacity-50">{idx + 1}.</span>
                            {step}
                          </div>
                        ))}
                      </div>
                   </div>
                 </>
               )}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {onRefresh && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onRefresh}
            disabled={isLoading}
            className="h-10 w-10 rounded-xl border border-border bg-background hover:bg-background-muted"
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
            className="h-10 gap-2 rounded-xl bg-gradient-to-br from-primary to-blue-600 px-4 font-medium text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:translate-y-[-1px] transition-all"
          >
            <Plus className="h-4 w-4" />
            <span>New Task</span>
          </Button>
        )}
      </div>
    </header>
  );
}