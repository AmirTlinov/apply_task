/**
 * Toast notification component with auto-dismiss
 */

import { useState } from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToastStore, type Toast, type ToastType } from "@/components/common/toast";

const typeConfig: Record<
  ToastType,
  { icon: typeof Info; iconClassName: string; badgeClassName: string }
> = {
  success: {
    icon: CheckCircle2,
    iconClassName: "text-status-ok",
    badgeClassName: "bg-status-ok/10",
  },
  error: {
    icon: AlertTriangle,
    iconClassName: "text-status-fail",
    badgeClassName: "bg-status-fail/10",
  },
  warning: {
    icon: AlertTriangle,
    iconClassName: "text-status-warn",
    badgeClassName: "bg-status-warn/10",
  },
  info: {
    icon: Info,
    iconClassName: "text-primary",
    badgeClassName: "bg-primary/10",
  },
};

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const [isExiting, setIsExiting] = useState(false);
  const config = typeConfig[toast.type];
  const Icon = config.icon;

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(onClose, 200);
  };

  return (
    <div
      className={cn(
        "flex min-w-[280px] max-w-[400px] items-center gap-3 rounded-xl border border-border bg-background px-4 py-3 shadow-lg",
        isExiting
          ? "animate-out fade-out slide-out-to-right-2 duration-200"
          : "animate-in fade-in slide-in-from-right-2 duration-200"
      )}
    >
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-md",
          config.badgeClassName
        )}
      >
        <Icon className={cn("h-4 w-4", config.iconClassName)} />
      </div>
      <span
        className="flex-1 text-sm font-medium leading-snug text-foreground"
      >
        {toast.message}
      </span>
      <button
        onClick={handleClose}
        className="flex shrink-0 items-center justify-center rounded-md p-1 text-foreground-subtle transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        aria-label="Close toast"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div
      className="pointer-events-none fixed bottom-6 right-6 z-[9999] flex flex-col gap-2"
    >
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItem toast={t} onClose={() => removeToast(t.id)} />
        </div>
      ))}
    </div>
  );
}
