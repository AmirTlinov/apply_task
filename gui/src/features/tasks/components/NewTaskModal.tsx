/**
 * New Item Modal
 *
 * Canonical model: Plans → Tasks → Steps.
 * - Plan: PLAN-### (contract + plan checklist)
 * - Task: TASK-### under a Plan (nested steps)
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { aiIntent, createEntity } from "@/lib/tauri";
import type { ContextData } from "@/types/api";
import type { Namespace, Plan } from "@/types/task";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";

interface NewTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTaskCreated?: () => void;
  // Kept for compatibility with callers (project picker UI).
  namespaces?: Namespace[];
  selectedNamespace?: string | null;
  defaultNamespace?: string | null;
}

type CreateKind = "plan" | "task";

function isPlan(value: unknown): value is Plan {
  const obj = (value ?? {}) as Record<string, unknown>;
  return typeof obj.id === "string" && obj.kind === "plan";
}

export function NewTaskModal({
  isOpen,
  onClose,
  onTaskCreated,
}: NewTaskModalProps) {
  const [kind, setKind] = useState<CreateKind>("task");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [context, setContext] = useState("");
  const [contract, setContract] = useState("");
  const [parentPlanId, setParentPlanId] = useState("");

  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoadingPlans, setIsLoadingPlans] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [discardOpen, setDiscardOpen] = useState(false);

  const isDirty = useMemo(() => {
    return (
      title.trim().length > 0 ||
      description.trim().length > 0 ||
      context.trim().length > 0 ||
      contract.trim().length > 0 ||
      (kind === "task" && parentPlanId.trim().length > 0)
    );
  }, [contract, context, description, kind, parentPlanId, title]);

  const resetForm = useCallback(() => {
    setKind("task");
    setTitle("");
    setDescription("");
    setContext("");
    setContract("");
    setParentPlanId("");
    setError(null);
  }, []);

  const closeNow = useCallback(() => {
    resetForm();
    onClose();
  }, [onClose, resetForm]);

  const requestClose = useCallback(() => {
    if (isSubmitting) return;
    if (isDirty) {
      setDiscardOpen(true);
      return;
    }
    closeNow();
  }, [closeNow, isDirty, isSubmitting]);

  useEffect(() => {
    if (!isOpen) return;
    setError(null);
    setIsLoadingPlans(true);
    (async () => {
      try {
        const resp = await aiIntent<ContextData>("context", { include_all: true, compact: true });
        const rawPlans = Array.isArray(resp.result?.plans) ? resp.result.plans : [];
        const nextPlans = rawPlans.filter(isPlan);
        setPlans(nextPlans);
        if (nextPlans.length === 0) {
          setKind("plan");
          setParentPlanId("");
        } else if (!parentPlanId) {
          setParentPlanId(nextPlans[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load plans");
      } finally {
        setIsLoadingPlans(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const canCreateTask = plans.length > 0 && parentPlanId.startsWith("PLAN-");

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    if (kind === "task" && !canCreateTask) {
      setError("Select a parent plan first");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const resp = await createEntity({
        title: title.trim(),
        kind,
        parent: kind === "task" ? parentPlanId : undefined,
        description: description.trim() || undefined,
        context: context.trim() || undefined,
        contract: kind === "plan" ? (contract.trim() || undefined) : undefined,
      });
      if (!resp.success) {
        setError(resp.error || "Failed to create");
        return;
      }
      closeNow();
      onTaskCreated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSubmitting(false);
    }
  }, [canCreateTask, closeNow, contract, context, description, kind, onTaskCreated, parentPlanId, title]);

  if (!isOpen) return null;

  return (
    <>
      <Dialog open={isOpen} onOpenChange={(open) => !open && requestClose()}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="h-4 w-4 text-primary" />
              Create {kind === "plan" ? "Plan" : "Task"}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                className={kind === "task" ? "rounded-md bg-background px-3 py-1 text-xs font-semibold" : "rounded-md px-3 py-1 text-xs font-semibold text-foreground-muted hover:bg-background-hover"}
                onClick={() => setKind("task")}
                disabled={isSubmitting}
              >
                Task
              </button>
              <button
                type="button"
                className={kind === "plan" ? "rounded-md bg-background px-3 py-1 text-xs font-semibold" : "rounded-md px-3 py-1 text-xs font-semibold text-foreground-muted hover:bg-background-hover"}
                onClick={() => setKind("plan")}
                disabled={isSubmitting}
              >
                Plan
              </button>
            </div>

            {kind === "task" && (
              <div className="space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                  Parent plan
                </div>
                {isLoadingPlans ? (
                  <div className="flex items-center gap-2 text-sm text-foreground-muted">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading plans…
                  </div>
                ) : plans.length === 0 ? (
                  <div className="text-sm text-foreground-muted">
                    No plans yet. Create a plan first, then add tasks under it.
                  </div>
                ) : (
                  <select
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={parentPlanId}
                    onChange={(e) => setParentPlanId(e.target.value)}
                    disabled={isSubmitting}
                  >
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.id} — {p.title}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}

            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                Title
              </div>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Short, specific name" />
            </div>

            {kind === "plan" && (
              <div className="space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                  Contract (optional)
                </div>
                <Textarea
                  value={contract}
                  onChange={(e) => setContract(e.target.value)}
                  rows={6}
                  placeholder="Intent, constraints, definition of done…"
                />
              </div>
            )}

            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                Description (optional)
              </div>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="Short overview"
              />
            </div>

            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-foreground-subtle">
                Context (optional)
              </div>
              <Textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                rows={6}
                placeholder="Links, constraints, decisions…"
              />
            </div>

            {error && (
              <div className="rounded-md border border-status-fail/40 bg-status-fail/10 px-3 py-2 text-sm text-status-fail">
                {error}
              </div>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={requestClose} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || (kind === "task" && !canCreateTask)}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating…
                  </>
                ) : (
                  "Create"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        isOpen={discardOpen}
        title="Discard changes?"
        description="You have unsaved edits."
        confirmLabel="Discard"
        cancelLabel="Keep editing"
        danger
        onCancel={() => setDiscardOpen(false)}
        onConfirm={() => {
          setDiscardOpen(false);
          closeNow();
        }}
      />
    </>
  );
}

