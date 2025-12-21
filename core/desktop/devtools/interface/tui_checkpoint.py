"""Checkpoint mode mixin for TUI."""

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from core.desktop.devtools.application.task_manager import TaskManager
    from core.step import Step
    from core.task_detail import TaskDetail


class CheckpointMixin:
    """Mixin providing checkpoint mode operations for TUI."""

    checkpoint_mode: bool
    checkpoint_selected_index: int
    current_task_detail: Optional["TaskDetail"]
    detail_selected_path: str
    manager: "TaskManager"
    task_details_cache: Dict[str, "TaskDetail"]
    navigation_stack: List[Tuple[str, str, int]]

    def _get_step_by_path(self, path: str) -> Optional["Step"]:
        """Get selected step stub - implemented by main class."""
        raise NotImplementedError

    def _get_root_task_context(self) -> Tuple[str, str, str]:
        """Get root task context stub - implemented by main class."""
        raise NotImplementedError

    def _rebuild_detail_flat(self, selected_path: Optional[str] = None) -> None:
        """Rebuild detail stub - implemented by main class."""
        raise NotImplementedError

    def _update_tasks_list_silent(self, skip_sync: bool = False) -> None:
        """Update tasks stub - implemented by main class."""
        raise NotImplementedError

    def _set_footer_height(self, lines: int) -> None:
        """Set footer height stub - implemented by main class."""
        raise NotImplementedError

    def force_render(self) -> None:
        """Force render stub - implemented by main class."""
        raise NotImplementedError

    def _step_to_task_detail(self, step: "Step", root_task_id: str, path_prefix: str) -> "TaskDetail":
        """Convert a nested step to a TaskDetail-like view model (implemented by main class)."""
        raise NotImplementedError

    def enter_checkpoint_mode(self) -> None:
        """Enter checkpoint editing mode for current subtask."""
        self.checkpoint_mode = True
        self.checkpoint_selected_index = 0
        self._set_footer_height(0)
        self.force_render()

    def exit_checkpoint_mode(self) -> None:
        """Exit checkpoint editing mode."""
        self.checkpoint_mode = False
        self.force_render()

    def toggle_checkpoint_state(self) -> None:
        """Toggle the selected checkpoint (criteria/tests)."""
        from core.desktop.devtools.application.context import save_last_task
        from core.desktop.devtools.application.task_manager import _find_step_by_path
        from core.desktop.devtools.application.task_manager import _find_task_by_path
        from core.desktop.devtools.interface.tui_detail_tree import canonical_path, node_kind

        if not self.current_task_detail:
            return
        detail = self.current_task_detail

        checkpoints = ["criteria", "tests"]
        if 0 <= self.checkpoint_selected_index < len(checkpoints):
            key = checkpoints[self.checkpoint_selected_index]
            current = False

            target_kind = "task_detail" if getattr(detail, "kind", "task") == "plan" else ""
            local_key = ""
            target: object | None = None
            full_path: str | None = None

            if target_kind == "task_detail":
                target = detail
            else:
                local_key = str(getattr(self, "detail_selected_path", "") or "")
                if not local_key:
                    return
                node_k = node_kind(local_key)
                canonical = canonical_path(local_key, node_k)
                target_kind = node_k
                # Resolve target in the current (possibly derived) detail model.
                if node_k == "step":
                    target = self._get_step_by_path(canonical)
                elif node_k == "plan":
                    st = self._get_step_by_path(canonical)
                    target = getattr(st, "plan", None) if st else None
                else:  # task node
                    target, _, _ = _find_task_by_path(list(getattr(detail, "steps", []) or []), canonical)
                if not target:
                    return

                # Build full path from root for persistence.
                root_task_id, root_domain, path_prefix = self._get_root_task_context()
                full_path = f"{path_prefix}.{canonical}" if path_prefix else canonical

            if key == "criteria":
                current = bool(getattr(target, "criteria_confirmed", False))
            elif key == "tests":
                current = bool(getattr(target, "tests_confirmed", False))

            root_task_id, root_domain, path_prefix = self._get_root_task_context()

            # Save changes
            try:
                ok, msg = self.manager.update_checkpoint(
                    root_task_id,
                    kind=target_kind,
                    checkpoint=key,
                    value=not current,
                    note="",  # note
                    domain=root_domain,
                    path=full_path,
                )
                if not ok:
                    return
                # Reload root task to get updated state
                updated_root = self.manager.load_task(root_task_id, root_domain, skip_sync=True)
                if updated_root:
                    # Update cache
                    self.task_details_cache[root_task_id] = updated_root

                    # If we're at root level, update current_task_detail directly
                    if not self.navigation_stack:
                        self.current_task_detail = updated_root
                    else:
                        # We're inside nested subtask - rebuild current view from updated root
                        derived = None
                        if hasattr(self, "_derive_nested_detail"):
                            derived = getattr(self, "_derive_nested_detail")(updated_root, root_task_id, path_prefix)
                        else:
                            nested_step, _, _ = _find_step_by_path(updated_root.steps, path_prefix)
                            if nested_step:
                                derived = self._step_to_task_detail(nested_step, root_task_id, path_prefix)
                        if derived:
                            derived.domain = root_domain
                            self.current_task_detail = derived

                    if local_key:
                        self._rebuild_detail_flat(local_key)
                    else:
                        self._rebuild_detail_flat()

                # Update tasks list without resetting view state
                self._update_tasks_list_silent(skip_sync=True)
                save_last_task(root_task_id, root_domain)
                self.force_render()
            except (ValueError, IndexError):
                pass

    def move_checkpoint_selection(self, delta: int) -> None:
        """Move checkpoint selection up/down."""
        self.checkpoint_selected_index = max(0, min(self.checkpoint_selected_index + delta, 1))
        self.force_render()


__all__ = ["CheckpointMixin"]
