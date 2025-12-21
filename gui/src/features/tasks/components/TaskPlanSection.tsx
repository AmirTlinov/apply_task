import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Edit3, ListOrdered, Plus, Trash2 } from "lucide-react";
import type { Plan, PlanChecklist, Task } from "@/types/task";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Markdown } from "@/components/common/Markdown";
import { toast } from "@/components/common/toast";
import { resumeEntity, updatePlan } from "@/lib/tauri";
import { cn } from "@/lib/utils";
import { buildPlanDocTemplate } from "@/features/tasks/lib/planDocTemplate";
import { TaskPlanView } from "@/features/tasks/components/TaskPlanView";

interface TaskPlanSectionProps {
  task: Task;
}

function clampInt(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, Math.trunc(value)));
}

function splitPlanSteps(text: string): string[] {
  return String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function extractPlanChecklist(plan?: Plan | null): PlanChecklist {
  const raw = plan?.plan;
  return {
    steps: Array.isArray(raw?.steps) ? raw!.steps : [],
    current: typeof raw?.current === "number" ? raw!.current : 0,
    doc: typeof raw?.doc === "string" ? raw!.doc : "",
  };
}

export function TaskPlanSection({ task }: TaskPlanSectionProps) {
  const queryClient = useQueryClient();
  const planId = task.parent ? String(task.parent) : "";
  const hasPlan = planId.startsWith("PLAN-");

  const planQueryKey = useMemo(() => ["plan", planId] as const, [planId]);
  const planQuery = useQuery({
    queryKey: planQueryKey,
    queryFn: async () => {
      const resp = await resumeEntity(planId);
      if (!resp.success || !resp.plan) {
        throw new Error(resp.error || "Failed to load plan");
      }
      return resp.plan;
    },
    enabled: hasPlan,
  });

  const checklist = extractPlanChecklist(planQuery.data);
  const planStepsCount = checklist.steps.length;
  const planCurrent = clampInt(checklist.current, 0, planStepsCount);
  const planDoc = checklist.doc;
  const hasAnyPlan = planDoc.trim().length > 0 || planStepsCount > 0;

  const [docEditorOpen, setDocEditorOpen] = useState(false);
  const [docTab, setDocTab] = useState<"edit" | "preview">("edit");
  const [draftDoc, setDraftDoc] = useState<string>("");

  const [stepsEditorOpen, setStepsEditorOpen] = useState(false);
  const [draftSteps, setDraftSteps] = useState("");
  const [draftCurrent, setDraftCurrent] = useState<string>("0");

  const [clearConfirmOpen, setClearConfirmOpen] = useState(false);

  const mutation = useMutation({
    mutationFn: async (payload: { doc?: string; steps?: string[]; current?: number; advance?: boolean }) => {
      const resp = await updatePlan({
        planId,
        doc: payload.doc,
        steps: payload.steps,
        current: payload.current,
        advance: payload.advance,
      });
      if (!resp.success) throw new Error(resp.error || "Failed to update plan");
      return resp;
    },
    onSuccess: (resp) => {
      if (resp.plan) {
        queryClient.setQueryData(planQueryKey, resp.plan);
      } else {
        queryClient.invalidateQueries({ queryKey: planQueryKey });
      }
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("Plan updated");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to update plan");
    },
  });

  const openDocEditor = (opts?: { seedTemplate?: boolean }) => {
    setDocTab("edit");
    setDraftDoc(opts?.seedTemplate ? buildPlanDocTemplate(task) : planDoc);
    setDocEditorOpen(true);
  };

  const saveDoc = () => {
    mutation.mutate({ doc: String(draftDoc ?? "") });
    setDocEditorOpen(false);
  };

  const openStepsEditor = () => {
    setDraftSteps(checklist.steps.join("\n"));
    setDraftCurrent(String(planCurrent));
    setStepsEditorOpen(true);
  };

  const saveSteps = () => {
    const nextSteps = splitPlanSteps(draftSteps);
    const rawCurrent = Number(draftCurrent);
    const nextCurrent = clampInt(Number.isFinite(rawCurrent) ? rawCurrent : 0, 0, nextSteps.length);
    mutation.mutate({ steps: nextSteps, current: nextCurrent });
    setStepsEditorOpen(false);
  };

  const advance = () => mutation.mutate({ advance: true });

  const clearPlan = () => {
    mutation.mutate({ doc: "", steps: [], current: 0 });
    setClearConfirmOpen(false);
  };

  if (!hasPlan) {
    return (
      <section id="task-plan" className="mb-6 rounded-lg border border-border bg-background-subtle p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 text-status-warn" aria-hidden />
          <div className="text-sm text-foreground-muted">
            This task has no parent plan. Create a plan (PLAN-###) and re-create the task under it.
          </div>
        </div>
      </section>
    );
  }

  return (
    <>
      <section id="task-plan" className="mb-6 rounded-lg border border-border bg-background-subtle p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground-muted">
            <ListOrdered className="h-4 w-4 text-primary" />
            <span>Plan</span>
            <span className="text-xs font-semibold tabular-nums text-foreground-subtle">
              {planCurrent}/{planStepsCount}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-2"
              onClick={() => openDocEditor({ seedTemplate: !hasAnyPlan })}
              disabled={mutation.isPending}
            >
              <Edit3 className="h-4 w-4" />
              Edit doc
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-2"
              onClick={openStepsEditor}
              disabled={mutation.isPending}
            >
              <Edit3 className="h-4 w-4" />
              Edit steps
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-2"
              onClick={advance}
              disabled={mutation.isPending || planStepsCount === 0}
              title="Advance plan current index"
            >
              <Plus className="h-4 w-4" />
              Advance
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-2 text-status-fail hover:text-status-fail"
              onClick={() => setClearConfirmOpen(true)}
              disabled={mutation.isPending || !hasAnyPlan}
            >
              <Trash2 className="h-4 w-4" />
              Clear
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          <TaskPlanView plan={checklist} showHeader={false} className="mb-0 border-none bg-transparent p-0" />

          <div className="rounded-lg border border-border bg-background p-3">
            {planQuery.isLoading ? (
              <div className="text-sm text-foreground-muted">Loading…</div>
            ) : planQuery.isError ? (
              <div className="text-sm text-status-fail">{String((planQuery.error as Error)?.message || "Failed to load plan")}</div>
            ) : planDoc.trim().length > 0 ? (
              <Markdown content={planDoc} className="text-sm" />
            ) : (
              <div className="text-sm text-foreground-muted">
                Plan doc is empty. Keep intent + definition of done in Contract; use Plan doc for architecture and rollout.
              </div>
            )}
          </div>
        </div>
      </section>

      <Dialog open={docEditorOpen} onOpenChange={(open) => setDocEditorOpen(open)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Edit Plan doc</DialogTitle>
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
            <Textarea value={draftDoc} onChange={(e) => setDraftDoc(e.target.value)} rows={18} placeholder="Architecture, rollout, observability…" />
          ) : (
            <div className="max-h-[60vh] overflow-y-auto rounded-md border border-border bg-background-subtle p-4">
              {draftDoc.trim().length > 0 ? (
                <Markdown content={draftDoc} className="text-sm" />
              ) : (
                <div className="text-sm text-foreground-muted">Nothing to preview.</div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setDocEditorOpen(false)} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button onClick={saveDoc} disabled={mutation.isPending}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={stepsEditorOpen} onOpenChange={(open) => setStepsEditorOpen(open)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Plan steps</DialogTitle>
          </DialogHeader>

          <div className="space-y-3">
            <Textarea
              value={draftSteps}
              onChange={(e) => setDraftSteps(e.target.value)}
              rows={10}
              placeholder="One step per line…"
            />
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">Current index</div>
              <input
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={draftCurrent}
                onChange={(e) => setDraftCurrent(e.target.value)}
                inputMode="numeric"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setStepsEditorOpen(false)} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button onClick={saveSteps} disabled={mutation.isPending}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        isOpen={clearConfirmOpen}
        title="Clear plan?"
        description="This will remove plan doc and plan steps."
        confirmLabel="Clear"
        cancelLabel="Cancel"
        danger
        onCancel={() => setClearConfirmOpen(false)}
        onConfirm={clearPlan}
      />
    </>
  );
}

