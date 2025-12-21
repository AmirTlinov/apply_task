import { cn } from "@/lib/utils";

export function FatalErrorScreen({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : String(error);
  const stack = error instanceof Error ? error.stack : undefined;

  return (
    <div className="flex h-full w-full items-center justify-center bg-background p-[var(--density-page-pad)]">
      <div className="w-full max-w-2xl rounded-xl border border-border bg-card p-[var(--density-card-pad)] shadow-sm">
        <div className="text-sm font-semibold text-status-fail">Failed to start UI</div>
        <div className="mt-2 text-base font-semibold text-foreground">{message}</div>
        {stack && (
          <pre
            className={cn(
              "mt-4 max-h-[340px] overflow-auto rounded-lg bg-background-muted p-3",
              "text-xs text-foreground"
            )}
          >
            {stack}
          </pre>
        )}
        <div className="mt-4 text-sm text-foreground-muted">
          Try rebuilding the GUI (`pnpm -C gui tauri build`) or running dev mode (`apply_task gui --dev`).
        </div>
      </div>
    </div>
  );
}
