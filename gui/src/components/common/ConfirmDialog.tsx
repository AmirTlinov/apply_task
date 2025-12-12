import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  isLoading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <AlertDialog open={isOpen} onOpenChange={(open: boolean) => !open && onCancel()}>
      <AlertDialogContent className="max-w-[420px]">
        <AlertDialogHeader>
          <div className="flex items-center gap-2">
            {danger && <AlertTriangle className="h-5 w-5 text-status-fail" />}
            <AlertDialogTitle>{title}</AlertDialogTitle>
          </div>
          {description && (
            <AlertDialogDescription>
              {description}
            </AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading} onClick={onCancel}>
            {cancelLabel}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={(e: React.MouseEvent) => {
              e.preventDefault();
              onConfirm();
            }}
            disabled={isLoading}
            className={cn(
              danger && "bg-status-fail hover:bg-status-fail/90 text-white",
              isLoading && "opacity-50 cursor-not-allowed"
            )}
          >
            {isLoading ? "Working..." : confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
