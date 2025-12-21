import { useEffect, useRef } from "react";
import { useUIStore } from "@/stores/uiStore";
import { isEditableTarget, isPlainKeypress } from "@/lib/keyboard";

interface UseKeyboardListNavigationOptions {
  enabled?: boolean;
  itemIds: string[];
  activeId: string | null | undefined;
  onActiveChange: (id: string | null) => void;
  onActivate?: (id: string) => void;
}

export function useKeyboardListNavigation({
  enabled = true,
  itemIds,
  activeId,
  onActiveChange,
  onActivate,
}: UseKeyboardListNavigationOptions) {
  const enabledRef = useRef(enabled);
  const itemIdsRef = useRef(itemIds);
  const activeIdRef = useRef(activeId ?? null);
  const onActiveChangeRef = useRef(onActiveChange);
  const onActivateRef = useRef(onActivate);

  useEffect(() => {
    enabledRef.current = enabled;
  }, [enabled]);

  useEffect(() => {
    itemIdsRef.current = itemIds;
  }, [itemIds]);

  useEffect(() => {
    activeIdRef.current = activeId ?? null;
  }, [activeId]);

  useEffect(() => {
    onActiveChangeRef.current = onActiveChange;
  }, [onActiveChange]);

  useEffect(() => {
    onActivateRef.current = onActivate;
  }, [onActivate]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!enabledRef.current) return;

      const ui = useUIStore.getState();
      if (ui.isPaletteOpen || ui.newTaskModalOpen) return;
      if (!isPlainKeypress(e)) return;
      if (isEditableTarget(e.target)) return;

      const ids = itemIdsRef.current;
      if (ids.length === 0) return;

      const key = e.key.toLowerCase();
      if (key === "enter") {
        const current = activeIdRef.current;
        const targetId = current && ids.includes(current) ? current : ids[0];
        onActivateRef.current?.(targetId);
        return;
      }

      if (key !== "j" && key !== "k" && key !== "arrowdown" && key !== "arrowup") {
        return;
      }

      e.preventDefault();
      const delta = key === "j" || key === "arrowdown" ? 1 : -1;
      const currentId = activeIdRef.current;
      const currentIndex = currentId ? ids.indexOf(currentId) : -1;
      const nextIndex =
        currentIndex < 0
          ? delta > 0
            ? 0
            : ids.length - 1
          : Math.min(ids.length - 1, Math.max(0, currentIndex + delta));

      onActiveChangeRef.current(ids[nextIndex]);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}

