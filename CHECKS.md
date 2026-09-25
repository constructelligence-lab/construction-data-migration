# Check catalogue

Every check in this guide in one place: the ones the toolkit runs, and the ones a person has to make. Use it to
build the plan, to run each trial load, and as the list an agent or a reviewer works through
([`AGENTS.md`](AGENTS.md)).

**When** says which stage the check belongs to: **P** planning, **S** source data (before mapping), **T** every
trial load and the final load, **C** cutover week, **G** after go-live.

## Automated checks

### Profile checks: before mapping

Run `python3 -m cdm profile EXPORT.csv` on every raw export before writing its mapping
([chapter 4](04-source-data-quality.md#profile-every-export-first)).

| Check | Severity | Finds | What to do |
| --- | --- | --- | --- |
| `P01` | warning | The file is not UTF-8 and was read as Windows-1252 | Check accented names; set `encoding` in the mapping |
| `P02` | error | Two columns share a header | Re-export, or rename in the export settings |
| `P03` | error | Rows with the wrong number of columns | An unquoted comma or a line break inside a value. Re-export with quoting |
| `P04` | warning | Whole rows duplicated | A report that repeats rows, or an export appended twice |
| `P05` | info | Subtotal and total rows | Add a `skip_if` rule |
| `P06` | info | Leading or trailing spaces | The mapper strips them; lookups built elsewhere may not |
| `P07` | warning | Dates readable both month-first and day-first | Confirm the format from the system settings; set `date_format` |
| `P08` | warning | Money or date values that do not parse | Find the rows; usually text in a number column |
| `P09` | info | A column with no values | Confirm it is not meant to hold data |
| `P10` | error | Full tax IDs or social security numbers | Re-export without the column ([chapter 13](13-handling-migration-data-safely.md)) |
| `P11` | warning | A money column with no negative amounts | Check that credits were not filtered out |
| `P12` | warning | Scientific notation or spreadsheet errors | The file went through a spreadsheet. Export straight from the source |
| `P13` | warning | Codes with varying lengths and leading zeros | Leading zeros lost in a spreadsheet |
| `P14` | warning | Names that look like the same business | Merge the records in the source system |

### Reconciliation checks: every trial and the final load

Run `python3 -m cdm reconcile DIR` ([chapter 7](07-reconciliation.md#the-checks)). Errors block sign-off;
warnings need a decision; notes are reminders.

| Check | Severity | Finds |
| --- | --- | --- |
| `R01` | error | Duplicate keys |
| `R02` | error | Missing, malformed or disallowed values |
| `R03` | error | References to jobs, codes, vendors or commitments that are not in the migration |
| `R04` | warning | Cost with no budget line |
| `R05` | error | Transactions or pay applications after the cutover date |
| `R06` | error | Owner retainage released beyond what was held |
| `R07` | warning | Commitments invoiced beyond their value |
| `R08` | warning | Open commitments on closed jobs |
| `R09` | error | Full tax IDs in the vendor file |
| `R10` | error | Commitment change orders with no commitment, or on the wrong job |
| `R11` | note | Pending change orders to confirm |
| `R12` | error | Vendor retainage released beyond what was withheld |
| `R13` | warning | Cost lines that look duplicated under different references |
| `R14` | error | Invoices against a commitment from a different vendor |
| `R15` | warning | AP cost lines with no vendor |
| `R16` | warning | Gaps in pay application numbering |
| `R17` | warning | Billing beyond contract value |
| `R18` | warning | Closed commitments still holding retainage |
| `R19` | warning | Inactive vendors holding open commitments |
| `R20` | warning | Vendor records that look like the same business |
| `R21` | warning | Approved change orders on void commitments |
| `R22` | warning | Pending change orders on closed jobs |
| `R23` | warning | Cost posted to inactive cost codes |
| `T01` | error | A recomputed figure that does not equal the control total |
| `T02` | error | A job missing from the migration or from the control totals |
| `T03` | error | Missing or inconsistent control totals |

### Schedule conversion checks

Run `python3 -m cdm schedule-compare SOURCE TARGET` ([chapter 9](09-schedules.md#checking-a-conversion)). It fails on
any activity missing, changed in type, date, actual date or duration; any relationship missing or with a different
lag; and a changed data date. It warns on new activities or links, percent complete differences, calendar changes,
and anything the readers could not interpret. `python3 -m cdm schedule FILE` lists open starts and open ends.

### Archive checks

Run `python3 -m cdm manifest EXPORT_DIR --out before.csv` when files leave the old system, then
`python3 -m cdm manifest-compare before.csv ARCHIVE_DIR` after the copy. It fails on any file missing, added or
changed in content, and reports files that moved folder.

## Manual checks

### Planning

| Check | Owner | When |
| --- | --- | --- |
| A migration data owner inside the company is named and has time allocated | GM | P |
| Every system and spreadsheet holding job data is inventoried, with its export route | Data owner | P |
| Scope decisions are agreed in writing, record by record | Controller, PM lead | P |
| Every job with retainage outstanding is treated as open | Controller | P |
| The cutover date is a period end, between pay application cycles, agreed with payroll and the accountant | Controller | P |
| Open jobs' contracts are checked for scheduling software, schedule format and document storage requirements | PM lead | P |
| Jobs in or near a dispute are identified with counsel | GM | P |
| Retention periods for the old system are agreed with the accountant and counsel | Controller | P |
| The statement of work defines loads, trial loads, returned exports and mapping ownership | Data owner | P |

### Source data

The full list is in [chapter 4](04-source-data-quality.md#the-clean-up-list).

| Check | Owner | When |
| --- | --- | --- |
| Duplicate vendors merged | Controller | S |
| Current tax forms and insurance for every vendor with open commitments | Controller | S |
| Finished jobs closed; closed jobs have no open balances | Controller | S |
| Dead cost codes made inactive; merges decided | Controller | S |
| Stale open POs and subcontracts closed | PM lead | S |
| Pending change orders located, including spreadsheets, and chased | PM lead | S |
| Unapplied cash, credit memos, unposted batches and suspense accounts cleared | Controller | S |
| Job cost tied to the general ledger | Controller | S |
| Document numbering unique and attachments present | PM lead | S |

### Every load

| Check | Owner | When |
| --- | --- | --- |
| Control reports printed from the old system after period close, saved as PDF | Controller | T |
| Every export profiled; every error resolved at source | Data owner | T |
| Mapping totals (parsed and written) equal the source report totals | Data owner | T |
| Reconciliation passes with zero errors; every warning reviewed and decided | Data owner, Controller | T |
| Document counts by project, type and status agree | PM lead | T |
| Highest document number per sequence agrees, so new numbers continue | PM lead | T |
| Schedule comparison passes; the rescheduled finish date and critical path agree | Scheduler | T |
| Every fix made in the mapping or the source data, none in the loaded data | Data owner | T |
| Issue log updated | Data owner | T |
| Sign-off by controller, PM lead and data owner | All three | T |

### Cutover week

| Check | Owner | When |
| --- | --- | --- |
| Old system frozen for new commitments and change orders at the agreed time | Controller | C |
| Period posted and closed; AP run paid; pay applications submitted | Controller | C |
| Integrations switched to the new system and new codes | Data owner | C |
| Vendor tax IDs and bank details entered in the new system through its own secure process and verified | Controller | C |
| Old system set to read-only | IT | C |
| Go/no-go held and signed; every must-be-yes line is yes ([template](templates/go-no-go.md)) | Controller, PM lead, data owner | C |
| Owners, lenders and subcontractors told about anything they will see change | PM lead, Controller | C |

### After go-live

The full list is in [chapter 12](12-after-go-live.md).

| Check | Owner | When |
| --- | --- | --- |
| First period close: cost, commitments and retainage roll forward from the cutover balances | Controller | G |
| First pay application continues the numbering and agrees with the owner's copy | Controller | G |
| Every integration delivered for the whole period | Data owner | G |
| Rebuilt reports agree with the parallel run and are signed off by their users | Report users | G |
| Reconciliation re-run at month-end; `R04`, `R20` and `R23` reviewed | Data owner | G |
| Archive verified with `manifest-compare` before the old system is switched off | IT | G |
| Staging copies of exports deleted, and the deletion recorded | IT | G |

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
