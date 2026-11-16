# Team roles

Everyone builds, everyone tests. A role is the person who makes sure a part
of the project gets done well, not the only person who works on it. The
skills read this file, so keep the names current.

| Role | Owns | Runs | Build tasks lean toward |
|---|---|---|---|
| Spec Lead | Writes the stakeholder brief; the framed questions, `spec.md` and its acceptance criteria; approves any spec change during the build | `/dashkit:spec` | Data layer, filters |
| Design Lead | Chart choice, layout, labels, the takeaway on every screen; `design.md`; the dashboard's identity; leads Make it yours | `/dashkit:design`, `/dashkit:make-it-yours` | Views, polish, Make it yours |
| Delivery Lead | The repository and collaborators, the roadmap and task assignments, reassignments, the final deploy | `/dashkit:roadmap` | Filters, final deploy |
| Data Lead | The database connection, the data layer, the reconciliation tests; keeping the full suite green | Phase 1: the connection and the early hello-world deploy | Data layer |
| Pitch Lead | The stakeholder's point of view at the end: the final review and the Demo Day pitch | `/dashkit:review-dashboard` | Views |

Make it yours, the open step after the dashboard is finished, is led by a
Design Lead (or the Design Lead side-quest holder), and the whole team is
welcome in the session.

The role that owns a planning skill runs it, the team reads the pull request,
and that person merges it. Task skills are run by the Issue's assignee, who
merges their own pull request. A change to `spec.md` during the build needs
the OK of a Spec Lead (or the Spec Lead side-quest holder), named below.

## Lineup rules

- **Exactly one Delivery Lead.** They own the repository.
- **Every other role: zero to three people.** Two or three people may share
  a role; any one of them may run its skill or give its OK.
- **A role nobody holds is a side quest.** Name one teammate for it under
  `## Side quests`. They take on that role's job: its skill (for the Data
  Lead, the first phase), its OK, and its build tasks. Anyone may hold more
  than one side quest.

## Our team

One row per person. The same role may appear on more than one row.

| Name | GitHub username | Role |
|---|---|---|
| | | |

## Side quests

One row for each role nobody above holds. Leave empty if every role is held.

| Role | Held by (GitHub username) |
|---|---|
| | |
