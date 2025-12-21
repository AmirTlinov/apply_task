import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Edit3, Link2, Tag, TriangleAlert } from "lucide-react";
import type { Task } from "@/types/task";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "@/components/common/toast";
import { editTask } from "@/lib/tauri";

interface TaskMetaSectionProps {
  task: Task;
}

function extractAIError(raw: unknown): string | null {
  const obj = (raw ?? {}) as Record<string, unknown>;
  const err = (obj.error ?? null) as Record<string, unknown> | null;
  const msg = typeof err?.message === "string" ? err.message : null;
  return msg && msg.trim().length > 0 ? msg : null;
}

function splitCSV(value: string): string[] {
  return String(value || "")
    .split(",")
    .map((v) => v.trim())
    .filter((v) => v.length > 0);
}

export function TaskMetaSection({ task }: TaskMetaSectionProps) {
  const queryClient = useQueryClient();
  const taskId = task.id;

  const taskQueryKey = useMemo(() => ["task", taskId] as const, [taskId]);

  const currentTags = Array.isArray(task.tags) ? task.tags : [];
  const currentDeps = Array.isArray(task.depends_on) ? task.depends_on : [];
  const currentPriority = typeof task.priority === "string" ? task.priority : "MEDIUM";

  const [editorOpen, setEditorOpen] = useState(false);
  const [draftTags, setDraftTags] = useState("");
  const [draftDeps, setDraftDeps] = useState("");
  const [draftPriority, setDraftPriority] = useState<"LOW" | "MEDIUM" | "HIGH">(
    currentPriority === "LOW" || currentPriority === "HIGH" ? currentPriority : "MEDIUM"
  );

  const mutation = useMutation({
    mutationFn: async (payload: { tags: string[]; dependsOn: string[]; priority: "LOW" | "MEDIUM" | "HIGH" }) => {
      const resp = await editTask({
        taskId,
        tags: payload.tags,
        dependsOn: payload.dependsOn,
        priority: payload.priority,
      });
      if (!resp.success) {
        throw new Error(extractAIError(resp.result) || resp.error || "Failed to update meta");
      }
      return resp;
    },
    onSuccess: (_resp, payload) => {
      queryClient.setQueryData<Task>(taskQueryKey as unknown as readonly unknown[], (old) => {
        if (!old) return old;
        return { ...old, tags: payload.tags, depends_on: payload.dependsOn, priority: payload.priority };
      });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: taskQueryKey as unknown as readonly unknown[] });
      toast.success("Meta updated");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to update meta");
    },
  });

  const openEditor = () => {
    setDraftTags(currentTags.join(", "));
    setDraftDeps(currentDeps.join(", "));
    setDraftPriority(currentPriority === "LOW" || currentPriority === "HIGH" ? currentPriority : "MEDIUM");
    setEditorOpen(true);
  };

  const closeEditor = () => setEditorOpen(false);

  const save = () => {
    mutation.mutate({
      tags: splitCSV(draftTags),
      dependsOn: splitCSV(draftDeps),
      priority: draftPriority,
    });
    closeEditor();
  };

  return (
    <>
      <section id="task-meta" className="mb-6 rounded-lg border border-border bg-background-subtle p-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground-muted">
            <span>Meta</span>
          </div>
          <Button variant="outline" size="sm" className="h-8 gap-2" onClick={openEditor} disabled={mutation.isPending}>
            <Edit3 className="h-4 w-4" />
            Edit
          </Button>
        </div>

        <div className="flex flex-wrap gap-3 text-sm text-foreground-muted">
          {task.priority && (
            <div className="inline-flex items-center gap-2">
              <TriangleAlert className="h-4 w-4 text-status-warn" />
              <span>{task.priority}</span>
            </div>
          )}
          {task.domain && (
            <div className="inline-flex items-center gap-2">
              <Tag className="h-4 w-4 text-primary" />
              <span>{task.domain}</span>
            </div>
          )}
          {task.updated_at && (
            <div className="inline-flex items-center gap-2">
              <span>Updated {new Date(task.updated_at).toLocaleDateString()}</span>
            </div>
          )}
          {currentDeps.length > 0 && (
            <div className="inline-flex items-center gap-2">
              <Link2 className="h-4 w-4" />
              <span className="font-mono text-xs">{currentDeps.join(", ")}</span>
            </div>
          )}
        </div>

        {currentTags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {currentTags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </section>

      <Dialog open={editorOpen} onOpenChange={(open) => (open ? setEditorOpen(true) : closeEditor())}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit Meta</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                Priority
              </div>
              <select
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={draftPriority}
                onChange={(e) => setDraftPriority(e.target.value as "LOW" | "MEDIUM" | "HIGH")}
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
              </select>
            </div>

            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                Tags (comma-separated)
              </div>
              <Input value={draftTags} onChange={(e) => setDraftTags(e.target.value)} placeholder="ux, mcp, docs" />
            </div>

            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                Depends on (comma-separated task IDs)
              </div>
              <Input value={draftDeps} onChange={(e) => setDraftDeps(e.target.value)} placeholder="TASK-001, TASK-002" />
            </div>
          </div>

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
