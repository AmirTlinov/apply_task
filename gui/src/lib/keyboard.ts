export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    target.isContentEditable
  );
}

export function isPlainKeypress(e: KeyboardEvent): boolean {
  return !e.metaKey && !e.ctrlKey && !e.altKey && !e.shiftKey;
}

