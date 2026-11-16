"""The progress tracker prints the same two lines every skill shows.

These run offline: the repository state is built in a temporary git
repository, and the GitHub Issues are passed in as plain data.
"""

import importlib.util
import io
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# Frozen copies of the blank template files. The project's own ROADMAP.md,
# design.md, and README.md fill in as the team works, so tests about the
# blank template must not read them. Copy the files here again whenever the
# template's versions change.
TEMPLATE = Path(__file__).resolve().parent / "fixtures" / "template"
_spec = importlib.util.spec_from_file_location("progress", ROOT / "tools" / "progress.py")
progress = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(progress)


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd, check=True, capture_output=True,
    )


def commit_on_main(root: Path, files: dict[str, str]) -> None:
    git(root, "init", "-b", "main")
    for name, text in files.items():
        (root / name).write_text(text, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "start")


def flags(state) -> tuple:
    return (state.spec, state.design, state.roadmap, state.review, state.deploy,
            state.make_it_yours)


def test_task_line_marks_done_current_and_later():
    assert progress.skill_line("build-next", 3, 7) == (
        "TASK #7  ✓ Pick up  ✓ Build  ▶ Tidy  ○ Full suite  ○ Pull request"
        "  ○ Review  ○ Decide findings  ○ Fix  ○ Merge")


def test_planning_line_uses_the_skill_label():
    assert progress.skill_line("spec", 1).startswith("SPEC  ▶ Stakeholder  ○ Framed questions")


def test_project_line_mid_build():
    s = progress.RepoState(True, True, True, 4, 12, False, False)
    assert progress.project_line(s) == (
        "PROJECT  ✓ Spec  ✓ Design  ✓ Roadmap  ▶ Build 4 of 12 tasks  ○ Deploy"
        "  ○ Make it yours  ○ Review")


def test_project_line_fresh_template():
    s = progress.RepoState(False, False, False, None, None, False, False)
    assert progress.project_line(s) == (
        "PROJECT  ▶ Spec  ○ Design  ○ Roadmap  ○ Build  ○ Deploy  ○ Make it yours  ○ Review")


def test_unknown_skill_and_bad_step_are_rejected():
    with pytest.raises(ValueError):
        progress.skill_line("nope", 1)
    with pytest.raises(ValueError):
        progress.skill_line("spec", 9)


def test_read_state_on_the_template_is_all_not_done(tmp_path):
    files = {n: (TEMPLATE / n).read_text(encoding="utf-8")
             for n in ("ROADMAP.md", "design.md", "README.md")}
    commit_on_main(tmp_path, files)
    state = progress.read_state(tmp_path, issues=[])
    assert flags(state) == (False,) * 6
    assert (state.issues_closed, state.issues_total) == (0, 0)


def test_template_roadmap_has_an_unfilled_review_section(tmp_path):
    text = (TEMPLATE / "ROADMAP.md").read_text(encoding="utf-8")
    assert "## Dashboard review" in text
    commit_on_main(tmp_path, {"ROADMAP.md": text})
    assert progress.read_state(tmp_path, issues=[]).review is False


def test_read_state_without_main_does_not_crash(tmp_path):
    state = progress.read_state(tmp_path, issues=[])
    assert flags(state) == (False,) * 6


def test_read_state_counts_issues_and_deploy(tmp_path):
    commit_on_main(tmp_path, {"README.md": "**Live app:** https://x.streamlit.app\n"})
    issues = [
        {"state": "CLOSED", "labels": [{"name": "phase-5"}]},
        {"state": "CLOSED", "labels": []},
    ]
    state = progress.read_state(tmp_path, issues=issues)
    assert (state.issues_closed, state.issues_total) == (2, 2)
    assert state.deploy is True


def test_deploy_waits_for_open_phase_5_issues(tmp_path):
    commit_on_main(tmp_path, {"README.md": "**Live app:** https://x.streamlit.app\n"})
    issues = [{"state": "OPEN", "labels": [{"name": "phase-5"}]}]
    assert progress.read_state(tmp_path, issues=issues).deploy is False


def test_read_state_recognizes_finished_documents(tmp_path):
    headings = [
        "Stakeholder and decision", "Framed questions", "Metric definitions",
        "Data sources", "Screens and interactions", "Acceptance criteria", "Out of scope",
    ]
    commit_on_main(tmp_path, {
        "spec.md": "\n".join(f"## {h}\n\ntext\n" for h in headings),
        "design.md": "## Screens\n\n```\n+----+\n```\n\n## Style rules\n",
        "ROADMAP.md": (
            "| Phase | Goal | Issues |\n|---|---|---|\n| 1. Data | x | #3, #4 |\n\n"
            "## Dashboard review\n\n- 2026-11-20: fixes in #9\n"
        ),
    })
    state = progress.read_state(tmp_path, issues=[])
    assert (state.spec, state.design, state.roadmap, state.review) == (True,) * 4


NOTE = "## Make it yours\n\nWe turned it into a transit map.\n"


def test_make_it_yours_done_when_note_on_main_and_phase_6_closed(tmp_path):
    commit_on_main(tmp_path, {"design.md": NOTE})
    issues = [{"state": "CLOSED", "labels": [{"name": "phase-6"}]}]
    assert progress.read_state(tmp_path, issues=issues).make_it_yours is True


def test_make_it_yours_waits_for_open_phase_6_or_none(tmp_path):
    commit_on_main(tmp_path, {"design.md": NOTE})
    assert progress.read_state(tmp_path, issues=[
        {"state": "OPEN", "labels": [{"name": "phase-6"}]}]).make_it_yours is False
    assert progress.read_state(tmp_path, issues=[]).make_it_yours is False


def test_make_it_yours_placeholder_note_is_not_done(tmp_path):
    commit_on_main(tmp_path, {"design.md":
        f"## Make it yours\n\n{progress.MAKE_IT_YOURS_PLACEHOLDER}\n"})
    issues = [{"state": "CLOSED", "labels": [{"name": "phase-6"}]}]
    assert progress.read_state(tmp_path, issues=issues).make_it_yours is False


def test_build_does_not_count_phase_6(tmp_path):
    commit_on_main(tmp_path, {"README.md": "x\n"})
    issues = [{"state": "CLOSED", "labels": [{"name": "phase-1"}]},
              {"state": "OPEN", "labels": [{"name": "phase-6"}]}]
    state = progress.read_state(tmp_path, issues=issues)
    assert (state.issues_closed, state.issues_total, state.build) == (1, 1, True)


def test_unreadable_issues_give_unknown_counts(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("no gh")
    monkeypatch.setattr(progress.subprocess, "run", boom)
    state = progress.read_state(tmp_path)
    assert (state.issues_closed, state.issues_total) == (None, None)


def test_cli_prints_on_a_cp1252_pipe(monkeypatch):
    out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", out)
    fixed = progress.RepoState(False, False, False, None, None, False, False)
    monkeypatch.setattr(progress, "read_state", lambda root, issues=None: fixed)
    assert progress.main(["--skill", "spec", "--step", "1"]) == 0
    out.flush()
    text = out.buffer.getvalue().decode("utf-8")
    assert text.splitlines()[0].startswith("PROJECT  ▶ Spec")
    assert text.splitlines()[1].startswith("SPEC  ▶ Stakeholder")


def test_template_design_has_an_unfilled_make_it_yours_section():
    text = (TEMPLATE / "design.md").read_text(encoding="utf-8")
    assert f"## Make it yours\n\n{progress.MAKE_IT_YOURS_PLACEHOLDER}" in text
    roadmap = (TEMPLATE / "ROADMAP.md").read_text(encoding="utf-8")
    assert ("| 6. Make it yours | The team makes the dashboard its own; "
            "every test still passes. | |") in roadmap
    assert "`phase-1` through `phase-6`" in roadmap


def test_template_make_it_yours_note_is_not_done_even_with_issue_closed(tmp_path):
    commit_on_main(tmp_path, {"design.md": (TEMPLATE / "design.md").read_text(encoding="utf-8")})
    issues = [{"state": "CLOSED", "labels": [{"name": "phase-6"}]}]
    assert progress.read_state(tmp_path, issues=issues).make_it_yours is False
