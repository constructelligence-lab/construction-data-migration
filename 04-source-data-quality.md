# Source data quality: clean before you map

Every old system holds years of small compromises: the vendor set up twice, the job nobody closed, the purchase
order from 2019 that is still technically open, the unapplied payment sitting in a suspense account. None of them
matters much day to day. In a migration, every one of them becomes a mapping exception, a reconciliation
difference or, worst of all, a false obligation that the new system faithfully reminds everyone about for years.

The cheapest point to fix them is before the first export.

## Where to fix a problem

| Fix it in | When | Why |
| --- | --- | --- |
| **The old system** | Whenever you can | The old system's reports, the control totals and the export all agree afterwards. Nothing needs explaining |
| **The mapping** | When the old system cannot be changed (a closed period, a locked record) | The fix is written down and runs identically in every trial and in the final load |
| **The loaded data** | Never | The next trial load will not include the fix, and nobody will remember it was made |

Every fix made in the old system after the control reports have been printed means reprinting them. Do the
clean-up before trial load 1, and freeze it before the final load.

## Profile every export first

Before writing a mapping for an export, run the profiler over it:

```bash
python3 -m cdm profile samples/legacy-export/vendor-list.csv
```

```text
vendor-list.csv: 12 data rows, 7 columns, cp1252

  column         filled  blank distinct  kind       detail / most common
  Vendor No          12      0       11  code       '002011'×2, '002001'×1, '002002'×1
  Name               12      0       11  text       'Sample Démolition Société'×2, 'Sample Drywall Co'×1, ...
  Tax ID             12      0       11  sensitive  (values withheld)
  Type               12      0        3  text       'Sub'×10, 'Supplier'×1, 'Service'×1
  1099               12      0        2  text       'N'×9, 'Y'×3
  Last Payment       12      0       11  date       ambiguous
  YTD Paid           12      0       11  money      total 872,288.98, 0 negative

ERROR   P10 [Tax ID] looks like full tax IDs: drop this column at export, keep the last four digits at most
WARNING P01 decoded as Windows-1252; pass the right encoding to the mapping if names look wrong
WARNING P04 1 row(s) are exact copies of another row
WARNING P07 [Last Payment] every value has day and month of 12 or less; confirm the format from the source system's settings
WARNING P12 [YTD Paid] 2 value(s) such as '2.51E+04': re-export from the source system, not from a spreadsheet
WARNING P13 [Vendor No] code lengths vary (4, 6), e.g. '2003': leading zeros may have been dropped
WARNING P14 [Name] 1 group(s), e.g. 'SAMPLE DRYWALL CO.' / 'Sample Drywall Co': merge before mapping
```

That one sample file shows most of what goes wrong with exports:

- **The tax ID column should never have been exported.** Re-run the export without it.
- **The file has passed through a spreadsheet.** Scientific notation (`2.51E+04`) and missing leading zeros
  (`2003` for `002003`) are what Excel does to numbers it thinks it understands. Export straight from the source
  system to CSV, and never open an export in a spreadsheet and save it again.
- **The dates cannot be read unambiguously.** Every value has a day and month of 12 or less, so `03/04/2026`
  could be March or April. Find out the format from the source system's settings, not by guessing from the data.
- **The vendor is set up twice.** Merge the two records in the old system before the export, or history splits
  between them for ever.

Every check the profiler makes is listed in the [check catalogue](CHECKS.md#profile-checks-before-mapping).

## The clean-up list

Work through this with the controller and the PM lead before trial load 1. Each item is phrased as the question
to ask of the old system. The [check catalogue](CHECKS.md) lists them again with who owns each one.

### Vendors

- Are any vendors set up twice, under different numbers or spellings? Merge them.
- Does every vendor with an open commitment, open retainage or payments this year have a current W-9 or local
  equivalent, and a correct tax reporting flag?
- Are insurance certificates current for every vendor with an open commitment? The new system will enforce
  expiry dates the old one may have ignored.
- Are there vendors marked inactive that still hold open commitments or retainage?

### Jobs

- Are there jobs that finished long ago but were never closed? Close them, or confirm why they are open.
- Are there closed jobs that still carry open commitments, retainage, unbilled cost or pending change orders?
- Does every open job have a contract value that matches the signed contract plus approved change orders?

### Cost codes and budgets

- Are there codes with no postings in years? Make them inactive; do not migrate them as active.
- Are there codes that mean the same thing? Decide the merges now ([chapter 5](05-cost-codes-and-crosswalks.md)).
- Are there negative budget lines, or budget lines on codes that no longer exist?
- Is cost posted to codes that have no budget line? Decide whether to add the budget line or recode the cost.

### Commitments and change orders

- Are there purchase orders or subcontracts that are fully invoiced, or years old, but still open? Close them.
- Has any commitment been invoiced beyond its value? There is a missing change order or a miscoded invoice.
- Where are pending change orders really kept? If the answer is a spreadsheet, that spreadsheet is a source system.
- Are there pending change orders older than 90 days? Chase them to a decision before cutover if you can.

### Receivables, payables and cash

- Are there unapplied payments or credit memos? Apply them.
- Are there open AP or AR invoices that are years old? Resolve them.
- Are there unposted batches, or entries in a suspense or clearing account? Clear them.
- Does job cost tie to the general ledger? Fix any difference before cutover, while it is still yours alone.

### Documents

- Are RFI, submittal and change event numbers unique per project, with no gaps nobody can explain?
- Do records have their attachments, or were files stored separately on a shared drive?
- Are open items genuinely open, or just never closed in the system?

## When to stop cleaning

Data quality work can expand to fill any timeline. A useful rule: **clean anything that affects an open
obligation or a control total, and leave cosmetic history alone.** A misspelled vendor name on a job closed in
2019 goes to the archive as it is. A duplicate vendor with an open subcontract gets merged.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
