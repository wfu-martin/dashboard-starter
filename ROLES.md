# Team roles

Everyone builds, everyone tests. A role is the person who makes sure a part
of the project gets done well, not the only person who works on it. A team of
five has one role each. The skills read this file, so keep the names current.

| Role | Owns | Runs | Build tasks lean toward |
|---|---|---|---|
| Spec Lead | The brief, framed questions, `spec.md` and its acceptance criteria; approves any spec change during the build | `/dashkit:spec` | Data layer, filters |
| Design Lead | Chart choice, layout, labels, the takeaway on every screen; `design.md` | `/dashkit:design` | Views, polish |
| Delivery Lead | The repository and collaborators, the roadmap and task assignments, reassignments, the final deploy | `/dashkit:roadmap` | Filters, final deploy |
| Data Lead | The database connection, the data layer, the reconciliation tests; keeping the full suite green | Phase 1: the connection and the early hello-world deploy | Data layer |
| Pitch Lead | The stakeholder's point of view at the end: the final review and the Demo Day pitch | `/dashkit:review-dashboard` | Views |

**Teams of four:** the Spec Lead and Pitch Lead merge into a **Stakeholder
Lead**. They own the stakeholder from the brief and `spec.md` to the final
review and the pitch, and run both `/dashkit:spec` and
`/dashkit:review-dashboard`. The Design, Delivery, and Data Leads are as above.

The role that owns a planning skill runs it, the team reads the pull request,
and that person merges it. Task skills are run by the Issue's assignee, who
merges their own pull request. A change to `spec.md` during the build needs
the Spec Lead's (or Stakeholder Lead's) OK, named below.

## Our team

| Name | GitHub username | Role |
|---|---|---|
| | | |
