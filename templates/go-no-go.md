# Cutover go / no-go

Held on the last working day before the new system opens, with the controller, the PM lead and the migration data owner.
Every line is a yes or a no. **One "no" in the first section is a no-go.** Lines in the second section can be accepted,
but only with a named owner and a date, written here.

Cutover date: ____________  Load: final  Meeting date: ____________

## Must be yes

| # | Question | Yes / No | Evidence |
| --- | --- | --- | --- |
| 1 | The period is closed in the old system and the control reports are printed and filed | | |
| 2 | The final load reconciles with zero errors (`cdm reconcile` exit 0 on the loaded data) | | Sign-off document |
| 3 | Every reconciliation warning has a recorded decision | | Issue log |
| 4 | Pending change orders are confirmed as pending in the new system (`R11`) | | |
| 5 | Every open job, including warranty jobs with retainage, is in the new system | | |
| 6 | Job cost ties to the general ledger at cutover | | |
| 7 | Vendor tax IDs and bank details are entered and verified through the new system's own process | | |
| 8 | Schedules for open jobs pass the conversion check, or remain in their contractual format | | |
| 9 | Document counts agree and the archive manifest matches the export | | |
| 10 | Payroll and tax reporting cutover is agreed with the payroll provider and accountant | | |
| 11 | The old system is read-only and still accessible | | |
| 12 | There is a rollback plan: what happens if the new system cannot be used on day one | | |

## Can be accepted with an owner and a date

| # | Question | Yes / No | If no: owner and date |
| --- | --- | --- | --- |
| 13 | Every integration (bank, payroll import, field time, portals) is switched and tested | | |
| 14 | The reports people rely on have been rebuilt and signed off by their users | | |
| 15 | Everyone who enters data on day one has been trained on their own jobs | | |
| 16 | Owners, lenders and subcontractors know about anything they will see change | | |
| 17 | Hypercare is staffed for the first two weeks | | |

## Decision

| | |
| --- | --- |
| Decision | Go / No-go |
| If no-go: what must change, and when we meet again | |

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Controller | | | |
| Project management lead | | | |
| Migration data owner | | | |

A no-go is not a failure. Opening a new system on data that does not reconcile is.
