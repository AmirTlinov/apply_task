import { History, Loader2, Redo2, RefreshCw, Undo2 } from "lucide-react";
import type { OperationHistoryEntry, OperationHistoryState } from "@/lib/tauri";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface OperationHistoryDialogProps {
  isOpen: boolean;
  onClose: () => void;

  namespace?: string | null;
  disabledReason?: string;

  history?: OperationHistoryState;
  isLoading?: boolean;
  error?: string | null;

  canUndo?: boolean;
  canRedo?: boolean;
  isBusy?: boolean;

  onUndo?: () => void;
  onRedo?: () => void;
  onRefresh?: () => void;
}

function formatTimestamp(datetime?: string, timestamp?: number): string {
  if (datetime) {
    const d = new Date(datetime);
    if (!Number.isNaN(d.getTime())) return d.toLocaleString();
  }
  if (typeof timestamp === "number" && Number.isFinite(timestamp)) {
    const d = new Date(timestamp * 1000);
    if (!Number.isNaN(d.getTime())) return d.toLocaleString();
  }
  return "";
}

function formatOperationLabel(op: OperationHistoryEntry): string {
  const base = op.intent ? op.intent : "operation";
  if (op.task_id) return `${base} · ${op.task_id}`;
  return base;
}

export function OperationHistoryDialog({
  isOpen,
  onClose,
  namespace,
  disabledReason,
  history,
  isLoading = false,
  error,
  canUndo = false,
  canRedo = false,
  isBusy = false,
  onUndo,
  onRedo,
  onRefresh,
}: OperationHistoryDialogProps) {
  const showDisabled = !namespace || Boolean(disabledReason);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-[740px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="h-4 w-4 text-foreground-subtle" />
            History
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-xs text-foreground-muted">
            {namespace ? (
              <span>
                Project: <span className="font-mono">{namespace}</span>
              </span>
            ) : (
              <span>Project: —</span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-2"
              onClick={onUndo}
              disabled={showDisabled || !canUndo || isBusy}
              title={disabledReason || (!canUndo ? "Nothing to undo" : "Undo last operation")}
            >
              <Undo2 className="h-4 w-4" aria-hidden />
              Undo
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-2"
              onClick={onRedo}
              disabled={showDisabled || !canRedo || isBusy}
              title={disabledReason || (!canRedo ? "Nothing to redo" : "Redo")}
            >
              <Redo2 className="h-4 w-4" aria-hidden />
              Redo
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-xl border border-border bg-background hover:bg-background-muted"
              onClick={onRefresh}
              disabled={showDisabled || isBusy}
              title={disabledReason || "Refresh history"}
            >
              <RefreshCw className={cn("h-4 w-4 text-foreground-muted", isBusy && "animate-spin")} aria-hidden />
            </Button>
          </div>
        </div>

        <div className="min-h-[220px] rounded-xl border border-border bg-background-subtle">
          {showDisabled ? (
            <div className="flex h-[220px] items-center justify-center px-6 text-sm text-foreground-muted">
              {disabledReason || "Select a project to view history."}
            </div>
          ) : isLoading ? (
            <div className="flex h-[220px] items-center justify-center gap-2 text-sm text-foreground-muted">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              Loading history…
            </div>
          ) : error ? (
            <div className="flex h-[220px] items-center justify-center px-6 text-sm text-status-fail">
              {error}
            </div>
          ) : (
            <div className="max-h-[360px] overflow-y-auto p-2 scrollbar-thin">
              {(history?.operations ?? []).length === 0 ? (
                <div className="flex h-[220px] items-center justify-center text-sm text-foreground-muted">
                  No operations yet.
                </div>
              ) : (
                <ul className="space-y-1">
                  {(history?.operations ?? []).map((op) => {
                    const undone = op.undone === true;
                    return (
                      <li
                        key={op.id}
                        className={cn(
                          "flex items-start justify-between gap-3 rounded-lg border border-border bg-background px-3 py-2 text-sm",
                          undone && "opacity-70"
                        )}
                      >
                        <div className="min-w-0">
                          <div className={cn("font-medium text-foreground", undone && "line-through")}>
                            {formatOperationLabel(op)}
                          </div>
                          <div className="text-xs text-foreground-muted">
                            {formatTimestamp(op.datetime, op.timestamp)}
                          </div>
                        </div>
                        <div className="shrink-0 text-xs text-foreground-subtle font-mono">
                          {op.id}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          )}
        </div>

        <div className="text-xs text-foreground-muted">
          Undo/Redo restores the last recorded snapshot. It does not re-run the original command.
        </div>
      </DialogContent>
    </Dialog>
  );
}

