import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Edit3, FileText } from "lucide-react";
import type { Task } from "@/types/task";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Markdown } from "@/components/common/Markdown";
import { toast } from "@/components/common/toast";
import { editTask } from "@/lib/tauri";
import { cn } from "@/lib/utils";

interface TaskNotesSectionProps {
  task: Task;
}

function extractAIError(raw: unknown): string | null {
  const obj = (raw ?? {}) as Record<string, unknown>;
  const err = (obj.error ?? null) as Record<string, unknown> | null;
  const msg = typeof err?.message === "string" ? err.message : null;
  return msg && msg.trim().length > 0 ? msg : null;
}

export function TaskNotesSection({ task }: TaskNotesSectionProps) {
  const queryClient = useQueryClient();
  const taskId = task.id;

  const taskQueryKey = useMemo(() => ["task", taskId] as const, [taskId]);

  const [editorOpen, setEditorOpen] = useState(false);
  const [docTab, setDocTab] = useState<"edit" | "preview">("edit");
  const [draftDescription, setDraftDescription] = useState("");
  const [draftContext, setDraftContext] = useState("");

  const descriptionText = String(task.description || "");
  const contextText = String(task.context || "");
  const hasNotes = descriptionText.trim().length > 0 || contextText.trim().length > 0;

  const mutation = useMutation({
    mutationFn: async (payload: { description: string; context: string }) => {
      const resp = await editTask({
        taskId,
        description: payload.description,
        context: payload.context,
      });
      if (!resp.success) {
        throw new Error(extractAIError(resp.result) || resp.error || "Failed to update notes");
      }
      return resp;
    },
    onSuccess: (_resp, payload) => {
      queryClient.setQueryData<Task>(taskQueryKey as unknown as readonly unknown[], (old) => {
        if (!old) return old;
        return { ...old, description: payload.description, context: payload.context };
      });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: taskQueryKey as unknown as readonly unknown[] });
      toast.success("Notes updated");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to update notes");
    },
  });

  const openEditor = () => {
    setDocTab("edit");
    setDraftDescription(descriptionText);
    setDraftContext(contextText);
    setEditorOpen(true);
  };

  const closeEditor = () => setEditorOpen(false);

  const save = () => {
    mutation.mutate({
      description: String(draftDescription ?? ""),
      context: String(draftContext ?? ""),
    });
    closeEditor();
  };

  const previewMarkdown = [
    draftDescription.trim().length > 0 ? "### Description\n\n" + draftDescription.trim() : "",
    draftContext.trim().length > 0 ? "### Context\n\n" + draftContext.trim() : "",
  ]
    .filter((part) => part.length > 0)
    .join("\n\n");

  return (
    <>
      <section id="task-notes" className="mb-6">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground-muted">
            <FileText className="h-4 w-4" />
            <span>Notes</span>
          </div>

          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-2"
            onClick={openEditor}
            disabled={mutation.isPending}
          >
            <Edit3 className="h-4 w-4" />
            Edit
          </Button>
        </div>

        <div className="rounded-lg border border-border bg-background-subtle p-[var(--density-card-pad)]">
          {hasNotes ? (
            <div className="space-y-6">
              <div>
                <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                  Description
                </div>
                {descriptionText.trim().length > 0 ? (
                  <Markdown content={descriptionText} className="text-sm" />
                ) : (
                  <div className="text-sm text-foreground-muted">Empty.</div>
                )}
              </div>

              <div>
                <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                  Context
                </div>
                {contextText.trim().length > 0 ? (
                  <Markdown content={contextText} className="text-sm" />
                ) : (
                  <div className="text-sm text-foreground-muted">Empty.</div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-sm text-foreground-muted">
              Keep background, constraints, and implementation notes here. Requirements belong in Contract; execution phases belong in Plan.
            </div>
          )}
        </div>
      </section>

      <Dialog open={editorOpen} onOpenChange={(open) => (open ? setEditorOpen(true) : closeEditor())}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Notes</DialogTitle>
          </DialogHeader>

          <div className="flex items-center gap-2">
            <button
              type="button"
              className={cn(
                "rounded-md px-3 py-1 text-xs font-semibold transition-colors",
                docTab === "edit" ? "bg-background text-foreground" : "text-foreground-muted hover:bg-background-hover"
              )}
              onClick={() => setDocTab("edit")}
            >
              Edit
            </button>
            <button
              type="button"
              className={cn(
                "rounded-md px-3 py-1 text-xs font-semibold transition-colors",
                docTab === "preview" ? "bg-background text-foreground" : "text-foreground-muted hover:bg-background-hover"
              )}
              onClick={() => setDocTab("preview")}
            >
              Preview
            </button>
          </div>

          {docTab === "edit" ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                  Description
                </div>
                <Textarea
                  value={draftDescription}
                  onChange={(e) => setDraftDescription(e.target.value)}
                  rows={5}
                  placeholder="Short overview of the step (optional)"
                />
              </div>
              <div className="space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                  Context
                </div>
                <Textarea
                  value={draftContext}
                  onChange={(e) => setDraftContext(e.target.value)}
                  rows={10}
                  placeholder="Background, constraints, links, decisions, logs…"
                />
              </div>
            </div>
          ) : (
            <div className="max-h-[60vh] overflow-y-auto rounded-md border border-border bg-background-subtle p-4">
              {previewMarkdown.trim().length > 0 ? (
                <Markdown content={previewMarkdown} className="text-sm" />
              ) : (
                <div className="text-sm text-foreground-muted">Nothing to preview.</div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={closeEditor} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button onClick={save} disabled={mutation.isPending}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
