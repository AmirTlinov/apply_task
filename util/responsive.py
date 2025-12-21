from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ColumnLayout:
    """Responsive table layout definition."""
    min_width: int
    columns: List[str]
    stat_w: int = 3
    id_w: int = 6
    marks_w: int = 5
    prog_w: int = 6
    subt_w: int = 7
    title_min: int = 16
    notes_w: int = 12
    context_w: int = 12

    def has_column(self, name: str) -> bool:
        return name in self.columns

    def _base_min_widths(self, desired: Optional[Dict[str, int]] = None) -> Dict[str, int]:
        base = {
            'idx': 3,
            'id': self.id_w,
            'stat': self.stat_w,
            'marks': self.marks_w,
            'progress': self.prog_w,
            'children': self.subt_w,
            'title': self.title_min,
            'notes': self.notes_w,
            'context': self.context_w,
        }
        result: Dict[str, int] = {}
        for col in self.columns:
            width = base.get(col, 8)
            if desired and col in desired:
                width = max(width, desired[col])
            result[col] = max(1, width)
        return result

    def required_width(self, desired: Optional[Dict[str, int]] = None) -> int:
        widths = self._base_min_widths(desired)
        return sum(widths.values()) + len(self.columns) + 1

    def calculate_widths(self, term_width: int, desired: Optional[Dict[str, int]] = None) -> Dict[str, int]:
        """Compute column widths that fit into the terminal."""
        separators = len(self.columns) + 1
        usable_width = max(len(self.columns), term_width - separators)
        widths = self._base_min_widths(desired)
        min_total = sum(widths.values())

        if min_total <= usable_width:
            remaining = usable_width - min_total
            # Keep metric columns (% / done/total / marks) tight; send extra width to content columns.
            flex_cols = [c for c in self.columns if c in ('title', 'notes', 'context')] or list(self.columns)
            weights = {col: (3 if col == 'title' else 1) for col in flex_cols}
            total_weight = max(1, sum(weights.values()))
            distributed = 0
            for col in flex_cols:
                share = (remaining * weights[col]) // total_weight
                widths[col] += share
                distributed += share
            leftover = remaining - distributed
            if leftover and flex_cols:
                widths[flex_cols[0]] += leftover
        else:
            deficit = min_total - usable_width
            shrink_order = [c for c in self.columns if c != 'stat'] or list(self.columns)
            min_limits = {
                'stat': max(2, self.stat_w - 1),
                'id': 3,
                'marks': max(3, self.marks_w - 2),
                'progress': 2,
                'children': 3,
                'title': 6,
                'notes': 6,
                'context': 6,
            }
            while deficit > 0 and shrink_order:
                progressed = False
                for col in shrink_order:
                    limit = min_limits.get(col, 2)
                    if widths[col] > limit:
                        widths[col] -= 1
                        deficit -= 1
                        progressed = True
                        if deficit == 0:
                            break
                if not progressed:
                    break

        total = sum(widths.values()) + separators
        if total > term_width:
            overflow = total - term_width
            min_limits = {'idx': 1, 'id': 1, 'stat': 1, 'marks': 3, 'progress': 2, 'children': 2, 'title': 2, 'notes': 2, 'context': 2}
            for col in reversed(self.columns):
                reducible = max(0, widths[col] - min_limits.get(col, 1))
                if reducible <= 0:
                    continue
                take = min(reducible, overflow)
                widths[col] -= take
                overflow -= take
                if overflow == 0:
                    break

        return widths


class ResponsiveLayoutManager:
    """Responsive layout selector for TUI tables."""

    LAYOUTS = [
        ColumnLayout(min_width=140, columns=['idx', 'id', 'stat', 'title', 'progress', 'children', 'marks'], stat_w=4, id_w=6, prog_w=8, subt_w=8, title_min=22),
        ColumnLayout(min_width=110, columns=['idx', 'id', 'stat', 'title', 'progress', 'children', 'marks'], stat_w=3, id_w=6, prog_w=7, subt_w=7, title_min=18),
        ColumnLayout(min_width=90, columns=['idx', 'id', 'stat', 'title', 'progress', 'children', 'marks'], stat_w=3, id_w=6, prog_w=6, subt_w=6, title_min=16),
        ColumnLayout(min_width=72, columns=['idx', 'id', 'stat', 'title', 'progress', 'children', 'marks'], stat_w=2, id_w=5, prog_w=5, subt_w=5, title_min=12),
        ColumnLayout(min_width=56, columns=['idx', 'id', 'stat', 'title', 'progress', 'marks'], stat_w=2, id_w=5, prog_w=5, title_min=12),
        ColumnLayout(min_width=0, columns=['idx', 'id', 'title'], id_w=4, title_min=10),
    ]

    @classmethod
    def select_layout(cls, term_width: int) -> ColumnLayout:
        for layout in cls.LAYOUTS:
            effective_min = max(layout.min_width, layout.required_width())
            if term_width >= effective_min:
                return layout
        return cls.LAYOUTS[-1]


def detail_content_width(term_width: int) -> int:
    """Adaptive content width for detail/single-subtask views."""
    # Detail views render their own frame borders (+...+), so a full-width content
    # block is `term_width - 2`. Keeping the width close to the terminal edge is
    # intentional for flagship density: the user expects the UI to use the space.
    tw = max(20, term_width)
    return max(0, tw - 2)
