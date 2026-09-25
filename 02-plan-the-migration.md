# Plan the migration

Most of a migration's risk is decided before anything is exported. This chapter covers the seven
decisions that set it: what exists, what moves, when, who owns it, how it is rehearsed, how it is proven,
and what happens to the old system afterwards.

## Step 1: inventory what you actually have

List every system that holds job data, not just the one being replaced. In most contractors the real
list is longer than anyone expects: the accounting system, a project management platform, a document
store, a scheduling tool, a payroll provider, an estimating database, and a set of spreadsheets that the
business quietly depends on. The spreadsheets matter most, because they usually hold the thing the
official system could not: the real change order log, the real WIP schedule, the real retainage tracker.

Use [`templates/migration-inventory.csv`](templates/migration-inventory.csv). For each system record who
owns it, which records it holds, roughly how many, and **how the data gets out**: a standard report, a
CSV export, a documented API, a database extract, or copy and paste. If nobody knows how the data gets
out, find out now. That is the longest lead time in the whole project.

## Step 2: decide the scope, record by record

For each record type, choose one of four treatments and write down the rule:

| Treatment | Meaning | Use it for |
| --- | --- | --- |
| **Detail** | Every open record, line by line, with its own ID | Anything someone will act on after cutover |
| **Balance** | One summarised figure per job, cost code and cost type, dated at cutover | History you need for reporting but will not act on line by line |
| **Archive** | Exported to a read-only store with an index, not loaded | Closed jobs, closed documents, prior years |
| **Leave** | Not moved at all | Data nobody has used in years and nobody is obliged to keep. Confirm that with your accountant and your counsel first |

The defaults that work for most contractors:

| Record | Open and warranty jobs | Closed jobs |
| --- | --- | --- |
| Jobs and contracts | Detail | Archive |
| Budgets | Detail: original and approved changes kept separate | Archive |
| Owner change orders | Detail, **including pending and rejected** | Archive |
| Commitments (subcontracts, POs) | Detail: original, changes, invoiced, paid, retainage | Archive |
| Commitment change orders | Detail, including pending | Archive |
| Cost to date | Balance per job, code and type, plus current-year detail if reports need it | Archive |
| Owner billing | Schedule of values with previously billed and retainage per line | Archive |
| Open AP and AR invoices | Detail | Not applicable |
| Vendors | Active vendors, plus any vendor with open retainage or year-to-date tax-reportable payments | Archive |
| RFIs and submittals | Open items in detail; closed items archived with an index | Archive |
| Drawings and specs | Current set in detail; superseded revisions archived | Archive |
| Schedules | Latest update and the baseline, native files kept | Archive |

Record the decisions in [`templates/scope-decisions.csv`](templates/scope-decisions.csv) and get the
controller and the PM lead to agree them in writing. Scope creep in a migration always goes the same
way: someone asks for "just the last three years" of closed jobs, and the timeline doubles.

**Warranty jobs are open jobs.** A job in its warranty period usually still has retainage owed to you
and by you, and warranty claims to track. Migrate it in detail.

## Step 3: choose the cutover date

The cutover date is the date on which the old system stops being the book of record. Choose it by these
rules, in order:

1. **A period end, after the period is closed** in the old system. Never mid-month.
2. **Between pay application cycles.** The owner billing for the period should be submitted from the old
   system, and the next one produced from the new system, with the application number continuing.
3. **Not in the same weeks as year-end close, an audit or a major bid.** The same people are needed for all
   of them.
4. **With payroll and tax reporting in mind.** A quarter start is often easiest for payroll. A mid-year
   cutover means year-to-date vendor payments must be carried forward for year-end tax reporting. Take the
   date to your payroll provider and your accountant before you fix it.
5. **With at least two trial loads before it.** Count backwards from the date. If the trial loads do not
   fit, move the date, not the trial loads.

## Step 4: name the people

| Role | Who | What they own |
| --- | --- | --- |
| **Migration data owner** | Someone inside the company, with time given to them | The inventory, the mappings, the trial loads, the issue log. Not the software vendor's consultant |
| **Controller** | Finance | The financial scope, the control totals and the financial sign-off |
| **PM lead** | Operations | Open job scope, commitments, change orders, documents, and the PM sign-off |
| **Field lead** | Operations | Daily logs, photos, field forms, and what the field needs on day one |
| **Scheduler** | Operations | The schedule conversion and its check |
| **IT or systems** | IT | Access, security of the exports, and the archive |
| **Vendor implementation lead** | The new system's vendor | How the new system loads data. They advise; the data owner decides |

If the only person who understands the mappings works for the vendor, the company does not own its
migration. Keep every mapping in a file, in your own repository or document store, and have the data
owner walk the controller through it.

## Step 5: rehearse it

Plan for **at least two full trial loads** before the final one. Each trial:

1. exports from the old system as of a recent period end, using the same reports and mappings the final
   load will use;
2. loads into a test copy of the new system;
3. is reconciled to the cent against that period's control totals ([chapter 6](06-reconciliation.md));
4. produces an issue log, and each issue is fixed in the **mapping or the source data**, never by hand in
   the loaded data.

That last rule is what makes the final load safe. A fix made by hand in trial 1 is forgotten in the final
load. A fix made in the mapping file runs every time.

## Step 6: run in parallel for one period

For one period after cutover, key the essentials in both systems: cost, commitments, billing. At period end
compare job by job, using [`templates/parallel-run-log.csv`](templates/parallel-run-log.csv). The two most
useful comparisons are **cost to date** and **over/under billing on the WIP schedule**. If those agree for
every job, the new system is producing the same picture of the business as the old one.

A parallel run is expensive. It is still cheaper than finding out at year-end that the new system has been
recognising revenue differently for six months.

## Step 7: decide what happens to the old system

Do not switch it off at cutover. Decide, with your accountant and your counsel, how long the old records
must stay available. Tax, audit, lender, warranty, claims and statute-of-repose periods all apply, and
they differ by jurisdiction and contract. Then choose one of:

- **Keep the old system read-only** for the retention period, if the licence allows it; or
- **Export a complete archive** before switching it off: standard reports as PDF (job cost detail, commitment
  registers, billing history, vendor history) plus the raw data as CSV, with an index that lets someone
  find a job in five years' time.

If any job is in a dispute, or a dispute is reasonably expected, speak to counsel **before** moving or deleting
anything connected to it.

## A typical shape

For a contractor with a few dozen open jobs, a realistic plan runs twelve to sixteen weeks from inventory to
the end of the parallel run. Treat this as a shape, not a promise. The biggest variable is how much of the
source data needs fixing before it can be mapped.

| Weeks | Work |
| --- | --- |
| 1-2 | Inventory, scope decisions, cutover date, roles |
| 3-5 | Cost code crosswalk, field mappings, first exports |
| 6-7 | Trial load 1 and reconciliation; fix the mappings and the source data |
| 8-9 | Trial load 2 and reconciliation; training starts |
| 10 | Cutover: close the period, print the control reports, final load, reconcile, sign off |
| 11-14 | Parallel run for one period, then compare and sign off again |

The day-by-day version is in the [cutover runbook](09-cutover-runbook.md).

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
