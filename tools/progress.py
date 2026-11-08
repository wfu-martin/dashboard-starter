#!/usr/bin/env python3
"""Show where the project is, in two lines.

Every dashkit skill runs this at each step. It prints:

    PROJECT  ✓ Spec  ✓ Design  ✓ Roadmap  ▶ Build 4 of 12 tasks  ○ Review  ○ Deploy
    TASK #7  ✓ Pick up  ✓ Build  ▶ Tidy  ○ Full suite  ...

The first line is the whole project: ✓ means a stage is done, ▶ is the first
stage that is not, and ○ are the stages after it. The second line is the
skill you are running, with the same marks for its own steps.

Where the first line comes from:

- Spec, Design, Roadmap, and Review are read from the files on the `main`
  branch (`git show main:<file>`), not from your working folder. A stage
  counts only once its pull request is merged, so a half-finished draft on
  a branch never shows as done, and everyone on the team sees the same line.
- Build and Deploy come from GitHub Issues, read with the `gh` command. If
  `gh` is missing or not signed in, the task count is left out and Build
  shows as not done; the script never stops with an error over it.

Run it by hand any time:

    python tools/progress.py --skill build-next --step 3 --issue 7

The script uses only Python's standard library, so it runs in any
environment, before or after `pip install`.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Each skill's steps, in order. The skills' numbered step names must match
# these exactly; the dashkit maintenance check compares them.
STEPS: dict[str, list[str]] = {
    "spec": ["Stakeholder", "Framed questions", "Metrics", "Screens",
             "Acceptance criteria", "Out of scope", "Read and agree", "Merge"],
    "design": ["Charts", "Drawings", "Mockup", "Sign-off", "Merge"],
    "roadmap": ["Phases", "Tasks", "Assign", "Issues", "Roadmap file", "Merge"],
    "tests-first": ["Start clean", "Pick the Issue", "Branch", "Write tests",
                    "Tests red", "Commit and hand off"],
    "build-next": ["Pick up", "Build", "Tidy", "Full suite", "Pull request",
                   "Review", "Decide findings", "Fix", "Merge"],
    "review-dashboard": ["Screens", "Answers", "Design", "Usability",
                         "Findings to Issues", "Merge"],
}

LABELS = {
    "spec": "SPEC",
    "design": "DESIGN",
    "roadmap": "ROADMAP",
    "review-dashboard": "REVIEW",
}
TASK_SKILLS = ("tests-first", "build-next")

SPEC_HEADINGS = [
    "## Stakeholder and decision",
    "## Framed questions",
    "## Metric definitions",
    "## Data sources",
    "## Screens and interactions",
    "## Acceptance criteria",
    "## Out of scope",
]

DONE, CURRENT, LATER = "✓", "▶", "○"


@dataclass
class RepoState:
    spec: bool
    design: bool
    roadmap: bool
    issues_closed: int | None  # None: Issues could not be read
    issues_total: int | None
    review: bool
    deploy: bool

    @property
    def build(self) -> bool:
        return bool(self.issues_total) and self.issues_closed == self.issues_total


def _run(cmd: list[str], cwd: Path) -> str | None:
    """The command's output, or None if it could not run or failed."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def _on_main(root: Path, name: str) -> str:
    return _run(["git", "show", f"main:{name}"], root) or ""


def _section(text: str, heading: str) -> str:
    """The text under `heading`, up to the next `## ` heading."""
    match = re.search(rf"^{re.escape(heading)}[ \t]*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def _read_issues(root: Path) -> list[dict] | None:
    out = _run(["gh", "issue", "list", "--state", "all", "--limit", "500",
                "--json", "state,labels"], root)
    if out is None:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


def _has_label(issue: dict, label: str) -> bool:
    return any(item.get("name") == label for item in issue.get("labels", []))


def read_state(root: Path, issues: list[dict] | None = None) -> RepoState:
    """Read the project's stages from `main` and from GitHub Issues."""
    if issues is None:
        issues = _read_issues(root)

    spec_text = _on_main(root, "spec.md")
    spec = all(re.search(rf"^{re.escape(h)}[ \t]*$", spec_text, re.M) for h in SPEC_HEADINGS)

    screens = _section(_on_main(root, "design.md"), "## Screens")
    design = "```" in screens and "<One text wireframe" not in screens

    roadmap_text = _on_main(root, "ROADMAP.md")
    table = "\n".join(l for l in roadmap_text.splitlines() if l.lstrip().startswith("|"))
    roadmap = bool(re.search(r"#\d+", table))
    review = bool(re.search(r"^- \d{4}-\d{2}-\d{2}",
                            _section(roadmap_text, "## Dashboard review"), re.M))

    if issues is None:
        closed = total = None
        deploy = False
    else:
        total = len(issues)
        closed = sum(1 for i in issues if i.get("state") == "CLOSED")
        phase5 = [i for i in issues if _has_label(i, "phase-5")]
        deploy = ("**Live app:** http" in _on_main(root, "README.md")
                  and bool(phase5)
                  and all(i.get("state") == "CLOSED" for i in phase5))

    return RepoState(spec, design, roadmap, closed, total, review, deploy)


def _marks(done: list[bool]) -> list[str]:
    marks, current_found = [], False
    for is_done in done:
        if is_done:
            marks.append(DONE)
        elif not current_found:
            marks.append(CURRENT)
            current_found = True
        else:
            marks.append(LATER)
    return marks


def project_line(state: RepoState) -> str:
    build = "Build"
    if state.issues_total:
        build = f"Build {state.issues_closed} of {state.issues_total} tasks"
    stages = [("Spec", state.spec), ("Design", state.design), ("Roadmap", state.roadmap),
              (build, state.build), ("Review", state.review), ("Deploy", state.deploy)]
    marks = _marks([done for _, done in stages])
    return "PROJECT  " + "  ".join(f"{m} {name}" for m, (name, _) in zip(marks, stages))


def skill_line(skill: str, step: int, issue: int | None = None) -> str:
    if skill not in STEPS:
        raise ValueError(f"unknown skill: {skill}")
    names = STEPS[skill]
    if not 1 <= step <= len(names):
        raise ValueError(f"{skill} has steps 1 to {len(names)}, not {step}")
    if skill in TASK_SKILLS:
        label = f"TASK #{issue}" if issue is not None else "TASK"
    else:
        label = LABELS[skill]
    marks = [DONE] * (step - 1) + [CURRENT] + [LATER] * (len(names) - step)
    return label + "  " + "  ".join(f"{m} {n}" for m, n in zip(marks, names))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the project and skill progress lines.")
    parser.add_argument("--skill", required=True, choices=sorted(STEPS))
    parser.add_argument("--step", required=True, type=int)
    parser.add_argument("--issue", type=int)
    args = parser.parse_args(argv)

    # Windows pipes default to a legacy encoding that cannot print ✓ ▶ ○.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    root = Path(__file__).resolve().parent.parent
    try:
        line = skill_line(args.skill, args.step, args.issue)
    except ValueError as err:
        parser.error(str(err))
    print(project_line(read_state(root)))
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
