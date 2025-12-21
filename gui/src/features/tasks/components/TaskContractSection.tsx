import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Edit3, FileText, Loader2 } from "lucide-react";
import type { Plan, Task } from "@/types/task";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Markdown } from "@/components/common/Markdown";
import { toast } from "@/components/common/toast";
import { resumeEntity, updateContract } from "@/lib/tauri";
import { cn } from "@/lib/utils";

interface TaskContractSectionProps {
  task: Task;
}

export function TaskContractSection({ task }: TaskContractSectionProps) {
  const queryClient = useQueryClient();
  const planId = task.parent ? String(task.parent) : "";
  const hasPlan = planId.startsWith("PLAN-");

  const planQueryKey = useMemo(() => ["plan", planId] as const, [planId]);
  const planQuery = useQuery({
    queryKey: planQueryKey,
    queryFn: async () => {
      const resp = await resumeEntity(planId);
      if (!resp.success || !resp.plan) throw new Error(resp.error || "Failed to load plan");
      return resp.plan;
    },
    enabled: hasPlan,
  });

  const plan = planQuery.data;
  const contractText = String(plan?.contract || "");
  const versions = typeof plan?.contract_versions_count === "number" ? plan.contract_versions_count : 0;

  const [editorOpen, setEditorOpen] = useState(false);
  const [docTab, setDocTab] = useState<"edit" | "preview">("edit");
  const [draftContract, setDraftContract] = useState("");

  const mutation = useMutation({
    mutationFn: async (payload: { current: string }) => {
      const resp = await updateContract({ planId, current: payload.current });
      if (!resp.success) throw new Error(resp.error || "Failed to update contract");
      return resp;
    },
    onSuccess: (resp) => {
      if (resp.plan) {
        queryClient.setQueryData<Plan>(planQueryKey as unknown as readonly unknown[], resp.plan);
      } else {
        queryClient.invalidateQueries({ queryKey: planQueryKey });
      }
      toast.success("Contract updated");
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to update contract");
    },
  });

  const openEditor = () => {
    setDocTab("edit");
    setDraftContract(contractText);
    setEditorOpen(true);
  };

  const save = () => {
    mutation.mutate({ current: String(draftContract ?? "") });
    setEditorOpen(false);
  };

  if (!hasPlan) {
    return (
      <section id="task-contract" className="mb-6 rounded-lg border border-border bg-background-subtle p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 text-status-warn" aria-hidden />
          <div className="text-sm text-foreground-muted">
            This task has no parent plan. Contract lives on the plan (PLAN-###).
          </div>
        </div>
      </section>
    );
  }

  const isLoading = planQuery.isLoading;
  const isError = planQuery.isError;
  const errorText = (planQuery.error as Error | undefined)?.message;
  const empty = !contractText.trim();

  return (
    <>
      <section id="task-contract" className="mb-6">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground-muted">
            <FileText className="h-4 w-4" />
            <span>Contract</span>
            {versions > 0 && (
              <span className="text-xs font-semibold tabular-nums text-foreground-subtle">
                v{versions}
              </span>
            )}
          </div>

          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-2"
            onClick={openEditor}
            disabled={mutation.isPending || isLoading || isError}
          >
            <Edit3 className="h-4 w-4" />
            Edit
          </Button>
        </div>

        <div className="rounded-lg border border-border bg-background-subtle p-[var(--density-card-pad)]">
          {isLoading ? (
            <div className="flex items-center gap-2 text-sm text-foreground-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading…
            </div>
          ) : isError ? (
            <div className="text-sm text-status-fail">{errorText || "Failed to load contract"}</div>
          ) : empty ? (
            <div className="text-sm text-foreground-muted">
              Contract is empty. Capture intent, constraints, and definition of done here.
            </div>
          ) : (
            <Markdown content={contractText} className="text-sm" />
          )}
        </div>
      </section>

      <Dialog open={editorOpen} onOpenChange={(open) => setEditorOpen(open)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Edit Contract</DialogTitle>
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
            <Textarea
              value={draftContract}
              onChange={(e) => setDraftContract(e.target.value)}
              rows={18}
              placeholder="Intent, constraints, definition of done…"
            />
          ) : (
            <div className="max-h-[60vh] overflow-y-auto rounded-md border border-border bg-background-subtle p-4">
              {draftContract.trim().length > 0 ? (
                <Markdown content={draftContract} className="text-sm" />
              ) : (
                <div className="text-sm text-foreground-muted">Nothing to preview.</div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditorOpen(false)} disabled={mutation.isPending}>
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

