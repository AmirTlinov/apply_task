import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { FileText, Search, X } from "lucide-react";
import type { TaskListItem } from "@/types/task";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

export interface CommandPaletteCommand {
  id: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  shortcut?: string;
  keywords?: string[];
  onSelect: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  tasks: TaskListItem[];
  commands: CommandPaletteCommand[];
  onSelectTask: (taskId: string) => void;
  onClose: () => void;
}

function normalize(text: string): string {
  return text.trim().toLowerCase();
}

function matchesQuery(haystack: string, query: string): boolean {
  if (!query) return true;
  return haystack.includes(query);
}

type PaletteItem =
  | { kind: "command"; id: string; command: CommandPaletteCommand }
  | { kind: "task"; id: string; task: TaskListItem };

export function CommandPalette({
  isOpen,
  tasks,
  commands,
  onSelectTask,
  onClose,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const normalizedQuery = useMemo(() => normalize(query), [query]);

  const filteredCommands = useMemo(() => {
    const base = normalizedQuery;
    return commands.filter((c) => {
      const keywords = c.keywords?.join(" ") ?? "";
      const hay = normalize(`${c.label} ${c.description ?? ""} ${keywords}`);
      return matchesQuery(hay, base);
    });
  }, [commands, normalizedQuery]);

  const filteredTasks = useMemo(() => {
    const base = normalizedQuery;
    const sorted = tasks
      .slice()
      .sort((a, b) => (b.updated_at ?? "").localeCompare(a.updated_at ?? ""));
    const matched = sorted.filter((t) => {
      const hay = normalize(`${t.title} ${t.id} ${(t.tags ?? []).join(" ")}`);
      return matchesQuery(hay, base);
    });
    if (base) return matched.slice(0, 30);
    return matched.slice(0, 8);
  }, [tasks, normalizedQuery]);

  const items = useMemo<PaletteItem[]>(() => {
    const out: PaletteItem[] = [];
    for (const c of filteredCommands) out.push({ kind: "command", id: `cmd:${c.id}`, command: c });
    for (const t of filteredTasks) out.push({ kind: "task", id: `task:${t.id}`, task: t });
    return out;
  }, [filteredCommands, filteredTasks]);

  const safeActiveIndex = Math.min(
    Math.max(activeIndex, 0),
    Math.max(0, items.length - 1)
  );

  useEffect(() => {
    if (!isOpen) return;
    const timer = window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => window.clearTimeout(timer);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const el = listRef.current?.querySelector<HTMLElement>(`[data-idx="${safeActiveIndex}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [isOpen, safeActiveIndex]);

  const handleClose = () => {
    setQuery("");
    setActiveIndex(0);
    onClose();
  };

  if (!isOpen) return null;

  const showCommands = filteredCommands.length > 0;
  const showTasks = filteredTasks.length > 0;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent
        hideClose
        className="max-w-[640px] overflow-hidden rounded-2xl"
      >
        <div className="flex items-center gap-2 border-b border-border bg-background-subtle px-4 py-3">
          <Search className="h-4 w-4 text-foreground-subtle" />
          <input
            ref={inputRef}
            autoFocus
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                e.preventDefault();
                handleClose();
                return;
              }

              const isCtrl = e.ctrlKey || e.metaKey;
              const next =
                e.key === "ArrowDown" || (isCtrl && e.key.toLowerCase() === "n");
              const prev =
                e.key === "ArrowUp" || (isCtrl && e.key.toLowerCase() === "p");

              if (next) {
                e.preventDefault();
                setActiveIndex((i) => Math.min(items.length - 1, i + 1));
                return;
              }
              if (prev) {
                e.preventDefault();
                setActiveIndex((i) => Math.max(0, i - 1));
                return;
              }
              if (e.key === "Enter") {
                e.preventDefault();
                const item = items[safeActiveIndex];
                if (!item) return;
                if (item.kind === "command") item.command.onSelect();
                if (item.kind === "task") onSelectTask(item.task.id);
                handleClose();
              }
            }}
            placeholder="Type a command or search tasks…"
            className="h-8 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-foreground-muted"
          />
          <button
            type="button"
            onClick={handleClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-foreground-muted transition-colors hover:bg-background-hover hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div
          ref={listRef}
          className="max-h-[52vh] overflow-y-auto p-2"
          role="listbox"
          aria-label="Results"
        >
          {!showCommands && !showTasks && (
            <div className="px-3 py-[var(--density-page-pad)] text-center text-sm text-foreground-muted">
              No matches
            </div>
          )}

          {showCommands && (
            <Section title="Commands">
              {filteredCommands.map((c, idx) => (
                <Row
                  key={c.id}
                  idx={idx}
                  isActive={idx === safeActiveIndex}
                  icon={c.icon}
                  title={c.label}
                  description={c.description}
                  shortcut={c.shortcut}
                  onClick={() => {
                    c.onSelect();
                    handleClose();
                  }}
                />
              ))}
            </Section>
          )}

          {showTasks && (
            <Section title={normalizedQuery ? "Tasks" : "Recent tasks"}>
              {filteredTasks.map((t, i) => {
                const idx = filteredCommands.length + i;
                return (
                  <TaskRow
                    key={t.id}
                    idx={idx}
                    isActive={idx === safeActiveIndex}
                    task={t}
                    onClick={() => {
                      onSelectTask(t.id);
                      handleClose();
                    }}
                  />
                );
              })}
            </Section>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-border bg-background-subtle px-4 py-2 text-xs text-foreground-muted">
          <span>↑/↓ · Enter to open · Esc to close</span>
          <span className="font-mono">{items.length} results</span>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="py-1">
      <div className="px-3 pb-1 pt-2 text-[11px] font-bold uppercase tracking-widest text-foreground-subtle">
        {title}
      </div>
      <div className="flex flex-col gap-1 px-1 pb-1">{children}</div>
    </div>
  );
}

function Row({
  idx,
  isActive,
  icon,
  title,
  description,
  shortcut,
  onClick,
}: {
  idx: number;
  isActive: boolean;
  icon?: ReactNode;
  title: string;
  description?: string;
  shortcut?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      data-idx={idx}
      onClick={onClick}
      role="option"
      aria-selected={isActive}
      className={cn(
        "flex w-full items-center gap-3 rounded-xl border px-3 py-2 text-left transition-colors",
        isActive
          ? "border-primary/40 bg-primary/10"
          : "border-transparent hover:bg-background-muted"
      )}
    >
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-background-muted">
        {icon ?? <FileText className="h-3.5 w-3.5 text-foreground-subtle" />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <div className="min-w-0 flex-1 truncate text-sm font-semibold text-foreground">
            {title}
          </div>
          {shortcut && (
            <kbd className="shrink-0 rounded-md border border-border bg-background px-1.5 py-0.5 font-mono text-[10px] font-medium text-foreground-subtle shadow-sm">
              {shortcut}
            </kbd>
          )}
        </div>
        {description && (
          <div className="mt-0.5 truncate text-xs text-foreground-muted">
            {description}
          </div>
        )}
      </div>
    </button>
  );
}

function TaskRow({
  idx,
  isActive,
  task,
  onClick,
}: {
  idx: number;
  isActive: boolean;
  task: TaskListItem;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      data-idx={idx}
      onClick={onClick}
      role="option"
      aria-selected={isActive}
      className={cn(
        "flex w-full items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left transition-colors",
        isActive
          ? "border-primary/40 bg-primary/10"
          : "border-transparent hover:bg-background-muted"
      )}
    >
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <span className="shrink-0 font-mono text-[11px] text-foreground-subtle">
          {task.id}
        </span>
        <span className="min-w-0 flex-1 truncate text-sm font-semibold text-foreground">
          {task.title}
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <StatusBadge status={task.status} size="sm" />
        {typeof task.progress === "number" && (
          <span className="font-mono text-[11px] text-foreground-subtle">
            {task.progress}%
          </span>
        )}
      </div>
    </button>
  );
}
