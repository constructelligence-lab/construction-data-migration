# Reconciliation: proving the migration

A migration is finished when, for every open job, each figure printed by the old system's own reports at
cutover equals the same figure recomputed from the migrated data. Equal, to the cent. This chapter covers
which figures, where they come from, how to chase a difference, and how to sign off.

## The control totals

Seven figures per job cover every financial obligation on it:

| Figure | How it is recomputed from the migrated data | Take the control from |
| --- | --- | --- |
| `contract_value` | Original contract plus **approved** owner change orders | Contract status report |
| `revised_budget` | Original budget plus approved changes, all lines | Job cost summary |
| `committed_cost` | Original value of every non-void commitment plus its **approved** change orders | Commitment register |
| `cost_to_date` | Every cost line posted on or before the cutover date | Job cost summary |
| `billed_to_date` | Work completed on submitted and approved pay applications; drafts excluded | Billing history |
| `retainage_receivable` | Retainage held by the owner less retainage released | Retainage receivable report |
| `retainage_payable` | Retainage withheld from vendors less retainage released to them | Retainage payable report |

Take the controls **from the old system's own printed reports**, run after the period is closed and before
anyone posts again. Not from a spreadsheet, not from memory, not from the export you are testing. A control
total taken from the export only proves the export agrees with itself. Save each report as a PDF and file it
with the sign-off.

Enter the figures in `control_totals.csv`, one row per job and figure, with the report name and the cutover
date. Every row must carry the same date.

## Why to the cent

Because differences cancel. A duplicated $41,000.00 invoice and a missing $40,999.57 credit on the same job
show up as a $0.43 difference. A tolerance of "under a dollar" would pass it. The reconciliation does not
allow a tolerance, and neither should you. A one-cent difference is a symptom with a cause, and the cause is
almost always cheaper to find now than after cutover.

Amounts are handled as exact decimals throughout the toolkit, never as floating-point numbers, and money
values with more than two decimal places are refused rather than rounded.

## Running it

```bash
python3 -m cdm reconcile samples/clean --markdown out/sign-off.md
```

```text
J-1104  Riverside Clinic Fit-out
  ok   contract_value             2,545,150.00     2,545,150.00          +0.00
  ok   revised_budget             2,208,150.00     2,208,150.00          +0.00
  ok   committed_cost             1,778,350.00     1,778,350.00          +0.00
  ok   cost_to_date               1,213,290.57     1,213,290.57          +0.00
  ok   billed_to_date             1,398,458.66     1,398,458.66          +0.00
  ok   retainage_receivable         139,845.86       139,845.86          +0.00
  ok   retainage_payable             88,151.31        88,151.31          +0.00
...
INFO    R11 [J-1104] 2 pending change order(s) worth 51,500.00; confirm they are pending in the new system too

PASS: every control total ties out  (0 errors, 0 warnings, 2 notes)
```

The same checks apply after go-live: re-run the reconciliation at each month-end for the first quarter, with that
month's control totals ([chapter 12](12-after-go-live.md#the-first-month-end)).

The command exits non-zero on any error, so it can gate a load script. `--markdown` writes a sign-off
document with the tie-out table per job, every finding, and signature lines. `--json` writes the same result
for other tools.

Run it against [`samples/broken`](samples/README.md#the-planted-faults) to see what a failing migration looks
like. Twelve realistic faults are planted there, and every one is caught.

## The checks

Errors block sign-off. Warnings need a person to look and decide. Notes are reminders.

| Check | Severity | What it means | Usual cause |
| --- | --- | --- | --- |
| `R01` | error | The same key appears twice in one file | A record exported twice, or two old records mapped to one new number |
| `R02` | error | A value is missing, malformed or not an allowed option | A sub-cent amount, a date in the wrong format, a status the mapping did not translate |
| `R03` | error | A reference points at a job, cost code, vendor or commitment that is not in the migration | A code renamed without updating the crosswalk; a vendor left out as "inactive" |
| `R04` | warning | Cost is posted to a job, code and cost type with no budget line | Unbudgeted cost in the old system, or a cost type mapped differently from its budget |
| `R05` | error | A transaction or pay application is dated after the cutover date | Next period's entries included in the export |
| `R06` | error | The owner has released more retainage on a job than was held | A release keyed as the wrong amount, or a held amount lost |
| `R07` | warning | A commitment has been invoiced beyond its committed value | A missing commitment change order, or cost coded to the wrong commitment |
| `R08` | warning | A closed job still has open commitments | A job closed before its subcontracts were closed out |
| `R09` | error | A vendor record carries more than the last four digits of a tax ID | A full tax ID in the export. Remove the file from wherever it has been copied |
| `R10` | error | A commitment change order has no commitment, or its commitment is on another job | A change order number that exists on two jobs in the old system |
| `R11` | note | Pending change orders exist | Not a problem in itself. Confirm they arrived as pending, not approved and not dropped |
| `R12` | error | More retainage has been released to a vendor than was withheld | A release loaded twice, or the withholding lines lost |
| `R13` | warning | Two cost lines match on job, code, type, date, amount and vendor under different references | A re-run export appended to the first. Only the tie-out and this check see it, because the keys differ |
| `R14` | error | A cost line is invoiced against a commitment by a different vendor | A vendor number keyed wrongly, or two vendors merged in one system and not the other |
| `R15` | warning | An AP cost line has no vendor | The vendor column dropped from the export or the mapping |
| `R16` | warning | Pay application numbers have a gap or do not start at 1 | Applications renumbered, or one left out of the export. Owners track by number |
| `R17` | warning | A job is billed beyond its contract value | An unapproved change billed, or an approved change order missing |
| `R18` | warning | A closed commitment still has retainage withheld | A subcontract closed before its retainage was released. Someone is still owed it |
| `R19` | warning | An inactive vendor holds an open commitment | The vendor marked inactive in clean-up without checking commitments |
| `R20` | warning | Two vendor records look like the same business | A vendor set up twice. Merge before cutover, or history splits between them |
| `R21` | warning | An approved change order sits on a void commitment | The change should move to the replacement commitment |
| `R22` | warning | A closed job still has pending change orders | Exposure nobody is chasing |
| `R23` | warning | Cost is posted to a cost code marked inactive | A code deactivated in the new list while still in use, or a crosswalk row pointing at an old code |
| `T01` | error | A recomputed figure does not equal the old system's control total | See [chasing a difference](#chasing-a-difference) |
| `T02` | error | A job has control totals but is not in the migration, or an open job has no control totals | A job left out of the export, or out of the controls |
| `T03` | error | The control totals are missing, incomplete, or carry more than one cutover date | Controls pulled from reports run on different days |

## Chasing a difference

The size and shape of a difference usually says what caused it:

| The difference is… | Look for |
| --- | --- |
| Exactly one line's amount | That line duplicated (a re-run export appended to the first) or missing |
| Exactly the sum of the credits | A filter that kept positive amounts only, or a sign convention flipped |
| A round number on `contract_value` | A change order in the wrong status: pending loaded as approved, or approved as pending |
| On `cost_to_date` but not the budget | Transactions from the wrong period included or excluded; check `R05` |
| On retainage but not on cost or billing | A release keyed as the wrong amount; retainage mapped to the wrong column |
| On `committed_cost` equal to one commitment's value | A commitment loaded twice (`R01`), or a void one loaded as open |
| Spread across many jobs by small amounts | Rounding: a system that stores more decimals than it prints. Take this to the controller. It is a policy decision, not a mapping fix |
| Different on every job in the same direction | The control reports and the export were run at different times |

Work the largest difference first. Fix the cause in the **mapping or the source data** and re-run. Never
correct the loaded data by hand, because the next trial load will not include the correction.

## Beyond the ledger

The same principle applies to everything else that moves:

- **Documents:** counts per project and type (RFIs, submittals, drawings, change events), open versus closed,
  and attachment counts. See [chapter 8](08-project-records-and-documents.md#reconciling-documents).
- **Schedules:** activities, relationships, dates and data date. See [chapter 9](09-schedules.md).
- **Vendors:** every vendor with an open commitment, open retainage or year-to-date reportable payments is
  present and active.

## Signing off

Use the generated sign-off, or [`templates/reconciliation-sign-off.md`](templates/reconciliation-sign-off.md)
if you are reconciling by other means. Three people sign: the controller, the PM lead and the migration data
owner. Attach the printed control reports. A sign-off without them is an opinion.

Sign off each trial load as well as the final one. The discipline is the same, and it is how you learn
whether the final load will take one evening or three days.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
