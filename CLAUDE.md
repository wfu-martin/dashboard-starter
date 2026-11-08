# Project: <dashboard name>

<One sentence: who the dashboard is for and the decision it helps them make.>

| | |
|---|---|
| Stakeholder | <name and role, from the brief> |
| Database | `<database name>` on the course server |
| Spec | `spec.md` (the source of truth for what to build) |
| Design | `design.md` (each screen as drawn, and the style rules) |
| Plan | `ROADMAP.md` for phases; GitHub Issues for tasks |
| Team | `ROLES.md` |

---

## Stack

- Streamlit app, entry point `streamlit_app.py`; run with `streamlit run streamlit_app.py`.
- PostgreSQL through `st.connection`. Every connection setting lives in `dashboard/db.py`; keep it as it is (TLS with certifi, pool pre-ping and recycle, a pool of three).
- Every query lives in `dashboard/metrics.py`: one function per figure on screen, taking the engine and returning a small DataFrame.
- Every headline, number tile, and chart goes through `dashboard/charts.py`, which carries the style rules in `design.md`. Build each screen as `design.md` draws it.
- Tests with pytest in `tests/`; run with `pytest`.

## How we work

- One GitHub Issue per branch, and the branch is named for the Issue.
- Tests come first. For each figure, write a reconciliation test (the figure equals an independent SQL answer) and an acceptance test for each spec requirement the Issue covers, and see them fail before building.
- The full suite passes before every pull request. A pull request says `Closes #<issue>`.
- State lives in files and Issues, so a fresh session can pick up any task.

## Rules for a public app on a shared login

- Secrets stay in `.streamlit/secrets.toml` (ignored by Git) and in Community Cloud's Secrets box.
- Viewers choose values with filters (dropdowns, sliders, date pickers) that pass parameters to the queries; the app has no box for typing SQL.
- Aggregate in SQL and cache each loader with `st.cache_data(ttl=600)`: queries on the server stop at 30 seconds, and the whole class shares its connections.

## Talking to us

Explain in plain business language. Report what changed on screen and what we should check, with the numbers.
