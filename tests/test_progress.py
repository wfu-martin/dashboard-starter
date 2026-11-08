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
    return (state.spec, state.design, state.roadmap, state.review, state.deploy)


def test_task_line_marks_done_current_and_later():
    assert progress.skill_line("build-next", 3, 7) == (
        "TASK #7  ✓ Pick up  ✓ Build  ▶ Tidy  ○ Full suite  ○ Pull request"
        "  ○ Review  ○ Decide findings  ○ Fix  ○ Merge")


def test_planning_line_uses_the_skill_label():
    assert progress.skill_line("spec", 1).startswith("SPEC  ▶ Stakeholder  ○ Framed questions")


def test_project_line_mid_build():
    s = progress.RepoState(True, True, True, 4, 12, False, False)
    assert progress.project_line(s) == (
        "PROJECT  ✓ Spec  ✓ Design  ✓ Roadmap  ▶ Build 4 of 12 tasks  ○ Review  ○ Deploy")


def test_project_line_fresh_template():
    s = progress.RepoState(False, False, False, None, None, False, False)
    assert progress.project_line(s) == (
        "PROJECT  ▶ Spec  ○ Design  ○ Roadmap  ○ Build  ○ Review  ○ Deploy")


def test_unknown_skill_and_bad_step_are_rejected():
    with pytest.raises(ValueError):
        progress.skill_line("nope", 1)
    with pytest.raises(ValueError):
        progress.skill_line("spec", 9)


def test_read_state_on_the_template_is_all_not_done(tmp_path):
    files = {n: (ROOT / n).read_text(encoding="utf-8")
             for n in ("ROADMAP.md", "design.md", "README.md")}
    commit_on_main(tmp_path, files)
    state = progress.read_state(tmp_path, issues=[])
    assert flags(state) == (False,) * 5
    assert (state.issues_closed, state.issues_total) == (0, 0)


def test_read_state_without_main_does_not_crash(tmp_path):
    state = progress.read_state(tmp_path, issues=[])
    assert flags(state) == (False,) * 5


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
