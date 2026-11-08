# Roadmap

Phases in critical-path order: each one needs the one before it. Every task
is a GitHub Issue small enough to finish in one fresh session, with its
acceptance criteria and the tests that prove it.

| Phase | Goal | Issues |
|---|---|---|
| 1. Data connection | The app reads the team's database, locally and on Community Cloud | |
| 2. Data layer | Every metric in the spec has a tested function in `dashboard/metrics.py` | |
| 3. Views | Each stakeholder question has a screen section that answers it, built as `design.md` draws it | |
| 4. Filters | The interactions the spec lists work, and the numbers still reconcile | |
| 5. Polish and deploy | The app follows every rule in `design.md`; `mockup.py` is gone; the live app link is in the README | |

## Critical path

<Which Issues block which; filled in from the spec.>

---

## Dashboard review

When the dashboard is finished, the Pitch Lead runs the final review. Each fix
becomes a GitHub Issue labeled `phase-1` through `phase-5`, for the phase it
belongs to, and each review adds one line below.

<Filled in by /dashkit:review-dashboard: one line per review, "- YYYY-MM-DD: fixes in #n, #n".>
