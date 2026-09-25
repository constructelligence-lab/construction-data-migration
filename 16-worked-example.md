# A worked example, end to end

This chapter runs one trial load from start to finish on the synthetic samples in this repository, with the real
commands and their real output. Everything here can be repeated on your own machine in about ten minutes. Clone the
repository, and run each command from its root.

The company is invented. It runs three jobs: J-1104 Riverside Clinic Fit-out and J-1107 Harbor Street Retail Shell, both
open, and J-1098 Oak Avenue Office Refresh, finished but in its warranty period with retainage still held. The cutover
date is 31 August 2026.

## 1. Profile the exports

Two files have come out of the old system: a job cost detail report for J-1104, and the vendor list. Before anyone writes
a mapping, profile both ([chapter 4](04-source-data-quality.md#profile-every-export-first)).

```text
$ python3 -m cdm profile samples/legacy-export/job-cost-detail.csv
job-cost-detail.csv: 69 data rows, 11 columns, utf-8

  column       filled  blank distinct  kind       detail / most common
  Job              58      0        1  text       'J-1104'×58
  Phase            58      0       11  code       '0707.00'×8, '0106.00'×7, '0107.00'×7
  Cat              58      0        4  text       'S'×22, 'M'×15, 'L'×14
  Date             58      0       28  date       month-first
  ...
  Amount           58      0       58  money      total 1,213,290.57, 1 negative
  Ret              19     39       19  money      total 88,151.31, 0 negative

INFO    P05 11 row(s) look like subtotals or totals (first on line 9); add a skip_if rule

OK: 0 errors, 0 warnings
```

The job cost export is usable. It has subtotal lines to skip, month-first dates, and one credit (the `1 negative`). The
amount total, 1,213,290.57, already equals the job cost summary for J-1104, so no rows have been lost on the way out.

The vendor list is a different story:

```text
$ python3 -m cdm profile samples/legacy-export/vendor-list.csv
...
ERROR   P10 [Tax ID] looks like full tax IDs: drop this column at export, keep the last four digits at most
WARNING P01 decoded as Windows-1252; pass the right encoding to the mapping if names look wrong
WARNING P04 1 row(s) are exact copies of another row
WARNING P07 [Last Payment] every value has day and month of 12 or less; confirm the format from the source system's settings
WARNING P12 [YTD Paid] 2 value(s) such as '2.51E+04': re-export from the source system, not from a spreadsheet
WARNING P13 [Vendor No] code lengths vary (4, 6), e.g. '2003': leading zeros may have been dropped
WARNING P14 [Name] 1 group(s), e.g. 'SAMPLE DRYWALL CO.' / 'Sample Drywall Co': merge before mapping
```

**Decisions made:** the controller re-runs the vendor export without the tax ID column, straight to CSV without opening it in
a spreadsheet, and confirms the system's date setting is month-first. The two Sample Drywall records are merged in the old
system before the next export. None of these fixes is made by editing the file.

## 2. Map the job cost export

The mapping file ([`mappings/legacy-job-cost-detail.json`](mappings/legacy-job-cost-detail.json)) skips subtotal rows, sends
the old phase codes through the crosswalk, translates the one-letter categories and sources, and reads dates month-first.

```text
$ python3 -m cdm map mappings/legacy-job-cost-detail.json samples/legacy-export/job-cost-detail.csv --out out/cost_transactions.csv
cost_transactions: 58 rows read, 58 written, 0 rejected, 11 skipped by skip_if
  amount: 1,213,290.57 parsed, 1,213,290.57 written
  retainage_withheld: 88,151.31 parsed, 88,151.31 written
written to out/cost_transactions.csv
```

58 rows in, 58 out, none rejected, and both money totals unchanged. Two old codes, `0902.00` and `0902.10`, both landed on
`09-020`, as the crosswalk says they should.

## 3. Validate, then reconcile

The first trial load is in `samples/broken`. It validates almost cleanly:

```text
$ python3 -m cdm validate samples/broken
...
ERROR   R01 duplicate key PO-1107-01 (first seen on line 13)  (commitments.csv line 20)

FAIL: 1 errors
```

That is the point of the next step. Validation checks that the files are well formed. Only reconciliation checks that they
are **right**:

```text
$ python3 -m cdm reconcile samples/broken
...
J-1107  Harbor Street Retail Shell
  FAIL contract_value               976,600.00       989,250.00     +12,650.00
  ok   revised_budget               840,450.00       840,450.00          +0.00
  FAIL committed_cost               632,380.00       663,860.00     +31,480.00
  FAIL cost_to_date                 477,171.62       456,768.18     -20,403.44
  ok   billed_to_date               554,471.78       554,471.78          +0.00
  ok   retainage_receivable          27,723.60        27,723.60          +0.00
  FAIL retainage_payable             15,008.14        13,963.17      -1,044.97
...
FAIL: do not cut over  (13 errors, 3 warnings, 1 notes)
```

## 4. Chase the differences

Take J-1107 figure by figure, using the patterns in [chapter 7](07-reconciliation.md#chasing-a-difference).

| Difference | Pattern | What it turned out to be | Fixed in |
| --- | --- | --- | --- |
| Contract value +12,650.00 | A round number on contract value | OCO-1107-002, the grease interceptor relocation, is **pending** in the old system and was mapped as approved | The status mapping |
| Committed cost +31,480.00 | Exactly one commitment's value | PO-1107-01 loaded twice (`R01` says so too) | The export: the report was run with a page break that repeated the last line |
| Cost to date −20,403.44 | Two causes netted together | A September invoice in an August load (`R05`), and a credit dropped by a positive-only filter | The export date range, and the filter |
| Retainage payable −1,044.97 | Retainage without a matching cost difference | The retainage on that September invoice | Fixed by the same export date range |

J-1104 shows the case the tie-out exists for. Its cost to date is out by +16,735.45, and there is **no duplicate key**,
because the payroll line was exported twice under a new reference. Only two checks see it: the tie-out, and `R13`, which
spots lines that match on everything but their reference:

```text
WARNING R13 [J-1104] B2602-030-R matches B2602-030 (line 31) on job, code, type, date, amount and vendor: a re-run export, or two genuine charges
```

A person decides which it is. Here it was a re-run export appended to the first, and the fix went into the export
procedure.

J-1098, the warranty job, shows why warranty jobs are migrated in detail: retainage receivable is out by −50,845.00 because a
release was keyed at three times the amount actually released (`R06`). Had J-1098 been left behind as "finished", that
retainage would have had no home in the new system at all.

Every fix above is made in the mapping, the export or the old system, and the load is re-run. **Nothing is edited in the
loaded files.**

## 5. The second trial load

After the fixes, the second trial (here, `samples/clean`) ties out:

```text
$ python3 -m cdm reconcile samples/clean --markdown out/sign-off.md
...
INFO    R11 [J-1104] 2 pending change order(s) worth 51,500.00; confirm they are pending in the new system too
INFO    R11 [J-1107] 1 pending change order(s) worth 12,650.00; confirm they are pending in the new system too

PASS: every control total ties out  (0 errors, 0 warnings, 2 notes)
sign-off report written to out/sign-off.md
```

The two notes are real work: someone opens the new system and confirms that the pending change orders are pending there
too. Then the controller, the PM lead and the data owner sign `out/sign-off.md`, with the printed control reports attached.
It starts like this:

```text
# Migration reconciliation sign-off

**Cutover date:** 2026-08-31
**Result:** PASS: every control total ties out to the cent

## J-1098 Oak Avenue Office Refresh

| Figure | Old system | Migrated | Difference | Source report |
| --- | ---: | ---: | ---: | --- |
| Original contract plus approved owner change orders | 508,450.00 | 508,450.00 | +0.00 | Contract status report |
...
```

## 6. The schedule

The J-1104 schedule is being moved from P6 to Microsoft Project. The converted file looks right when opened. The check
says otherwise:

```text
$ python3 -m cdm schedule-compare samples/schedules/fitout.xer samples/schedules/fitout-lossy-conversion.xml --match name
fitout.xer: 16 activities, 19 relationships, 2026-02-02 to 2026-11-06
fitout-lossy-conversion.xml: 16 activities (+3 summary rows), 18 relationships, 2026-02-02 to 2026-11-06
ERROR   relationship hang and finish board -> prime and first coat paint (FF) is missing from fitout-lossy-conversion.xml
ERROR   relationship hang and finish board -> ceiling grid: lag 120h became 16h
```

A finish-to-finish link has gone and a 15-day lag has become 2 days. Neither changes a single date today. Both change the
forecast the next time the schedule is updated. The scheduler redoes the conversion with the lag calendar set correctly
and re-runs the check until it passes ([chapter 9](09-schedules.md)).

## 7. The documents

Before the document export is copied to the archive, the data owner takes a manifest, and compares it after the copy
([chapter 8](08-project-records-and-documents.md#reconciling-documents)):

```bash
python3 -m cdm manifest exports/documents --out out/documents-at-export.csv
python3 -m cdm manifest-compare out/documents-at-export.csv archive/documents
```

A `PASS` here, and the document counts agreeing with the old system's logs, closes the documents.

## 8. Go or no go

On the Friday of cutover week, the three signatories run through the
[go/no-go checklist](templates/go-no-go.md). In this example, every trial and the final load reconciled, the schedule
comparison passed, the document manifests matched, and the pending change orders were confirmed as pending. It's a go.

## What the example shows

- **Validation is not reconciliation.** The broken load had one validation error and thirteen reconciliation errors.
- **Differences net off.** J-1107's cost difference was two faults in opposite directions.
- **The dangerous faults don't break anything.** A duplicated line with a new reference, a pending change order
  marked approved, and a lost schedule link all load without complaint.
- **Every fix goes upstream.** Mapping, export, old system. Never the loaded data.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
