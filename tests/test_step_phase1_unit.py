from core import Step


def test_step_computed_status_pending():
    st = Step(completed=False, title="T", success_criteria=["c"], tests=["t"], blockers=["b"])
    assert st.computed_status == "pending"


def test_step_computed_status_in_progress_on_notes():
    st = Step(completed=False, title="T", success_criteria=["c"], tests=["t"], blockers=["b"], progress_notes=["started"])
    assert st.computed_status == "in_progress"


def test_step_computed_status_blocked():
    st = Step(completed=False, title="T", success_criteria=["c"], tests=["t"], blockers=["b"], blocked=True, block_reason="Waiting")
    assert st.computed_status == "blocked"


def test_step_computed_status_completed():
    st = Step(completed=True, title="T", success_criteria=["c"], tests=["t"], blockers=["b"])
    assert st.computed_status == "completed"

