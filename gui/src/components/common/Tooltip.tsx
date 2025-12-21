/**
 * Simple tooltip component
 */

import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { cn } from "@/lib/utils";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  shortcut?: string;
  position?: "top" | "bottom" | "left" | "right";
  delay?: number;
}

export function Tooltip({
  content,
  children,
  shortcut,
  position = "top",
  delay = 300,
}: TooltipProps) {
  return (
    <TooltipPrimitive.Provider delayDuration={delay}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          <span className="inline-flex">{children}</span>
        </TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={position}
            sideOffset={8}
            className={cn(
              "z-50 flex select-none items-center gap-2 rounded-md bg-foreground px-2.5 py-1.5 text-xs font-medium text-background shadow-lg",
              "data-[state=delayed-open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=delayed-open]:fade-in-0",
              "data-[side=top]:slide-in-from-bottom-1 data-[side=bottom]:slide-in-from-top-1 data-[side=left]:slide-in-from-right-1 data-[side=right]:slide-in-from-left-1"
            )}
          >
            <span>{content}</span>
            {shortcut && (
              <KeyboardHint
                shortcut={shortcut}
                className="bg-white/15 text-white/90"
              />
            )}
            <TooltipPrimitive.Arrow className="fill-foreground" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}

/**
 * Keyboard shortcut hint badge (standalone)
 */
export function KeyboardHint({
  shortcut,
  className,
}: {
  shortcut: string
  className?: string
}) {
  return (
    <kbd
      className={cn(
        "inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-mono text-[10px] font-medium tracking-wide shadow-sm",
        className ?? "border border-border bg-background text-foreground-subtle"
      )}
    >
      {shortcut}
    </kbd>
  );
}
