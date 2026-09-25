# Financial cutover

The financial rule is simple to state: **every open obligation must exist in the new system in a form that
can be acted on.** A subcontractor's next invoice can be matched to its commitment. Retainage can be
released. The next owner pay application picks up exactly where the last one stopped. A change order still
under negotiation is still visible as exposure.

This chapter goes through each financial record in turn. None of it is accounting or tax advice. It is the
set of questions to settle with your controller, your accountant and your payroll provider before the date
is fixed.

## Detail or balance

For open and warranty jobs:

| Figure | Bring as | Why |
| --- | --- | --- |
| Contract and owner change orders | Detail | Contract value must be rebuilt from the original plus each change, including pending ones |
| Budget | Detail: original and approved changes per line | Cost-to-complete and budget history depend on it |
| Commitments and their change orders | Detail | The next invoice has to be matched to the commitment and its remaining balance |
| Invoiced and paid to date per commitment | Detail, as opening lines against each commitment | Remaining-to-bill and retainage per subcontractor depend on it |
| Cost to date | **Balance** per job, code and cost type, dated at cutover, with current-year detail only if a report needs it | Line-by-line history is rarely acted on, and costs far more to reconcile |
| Owner billing | Schedule of values per line with previously billed, stored materials and retainage | The next pay application must continue from it |
| Open AP invoices | Detail, unpaid ones only | They have to be paid from the new system |
| Open AR invoices | Detail | They have to be collected and applied in the new system |

Opening balance lines use `source = opening_balance` in the neutral model, so they are always
distinguishable from costs posted after cutover.

## Owner contracts and billing

- **Continue the application numbering.** If the last application from the old system was number 7, the
  first one from the new system is number 8. Owners, lenders and inspectors track by number. Restarting at
  1 causes confusion that takes weeks to unwind.
- **Load the schedule of values as the owner has it**, line by line, with previously billed and retainage
  per line. The first new application must show the same "work completed from previous application" as the
  owner's copy of the last one.
- **Bring pending owner change orders as pending.** They are not in contract value, but they are real
  exposure, and they will be approved, rejected or argued about after cutover.
- **Stored materials** billed but not yet installed must be carried as stored, or the next application will
  bill them twice.

## Commitments

For each open subcontract and purchase order, the new system needs:

- original value, and each change order separately with its status;
- invoiced to date, paid to date and retainage withheld to date;
- the remaining balance, which must equal committed cost less invoiced to date;
- the compliance status the new system will enforce: insurance, lien waivers and any required documents.

Migrating only "balance remaining" is the most common shortcut and the most expensive one. It saves a few
days before cutover and costs weeks afterwards, every time someone has to reconstruct a subcontractor's
billing history to answer a question.

## Retainage in both directions

Retainage is the balance most often lost in a migration, because it sits on jobs that look finished.

- **Receivable:** retainage held by owners, per job, reduced by any releases. It must equal the old system's
  retainage receivable report for each job.
- **Payable:** retainage withheld from each subcontractor and supplier, per commitment, reduced by releases.
  It must equal the old system's retainage payable report.

Every job with retainage outstanding in either direction is an open job for migration purposes, including
warranty jobs and jobs waiting on closeout paperwork. The reconciliation's `R06` and `R12` checks catch
releases that exceed what was held.

## Payroll and tax reporting

Payroll is regulated and runs on its own calendar. Take the cutover to your payroll provider and your
accountant before you fix the date:

- **Year-to-date wages, taxes and deductions** for each employee must be carried correctly, or year-end forms
  will be wrong. A quarter start is often the easiest point to switch.
- **Certified payroll and prevailing wage records** must stay producible on request for the period your
  contracts and regulators require. Archive them from the old system in a form someone can print.
- **Union fringe and benefit reporting** has its own remittance cycle. Do not change systems in the middle of
  a reporting period without a plan.
- **Vendor tax reporting** (in the US, [Form 1099-NEC](https://www.irs.gov/forms-pubs/about-form-1099-nec) and
  related forms; other countries have their own equivalents) is based on payments made in the calendar year.
  After a mid-year cutover, year-end reporting needs the payments from both systems. Either carry year-to-date
  payments per reportable vendor into the new system, or plan to report from both.

## WIP and revenue recognition

If your financial statements recognise revenue on a percentage-of-completion basis, the **WIP schedule** is
where a migration shows up first.

1. Run the WIP schedule from the old system at cutover: contract value, estimated cost at completion, cost to
   date, percent complete, earned revenue, billed to date, and over or under billing per job.
2. Rebuild the same schedule from the new system after the load.
3. Over and under billing must agree job by job. If they do not, the difference is almost always one of three
   things: a different estimated cost at completion, pending change orders treated differently, or a
   different method of computing percent complete.

The new system must compute percent complete the same way your accountant does. Confirm this in writing
before cutover, not at year-end.

## Tie the job cost ledger to the general ledger

The job cost subledger and the general ledger must agree at cutover, as they should at every period end.
Total cost to date across all jobs, including closed jobs in the current year, must equal the job cost and
work-in-progress accounts in the GL trial balance, allowing for any reconciling items your controller already
tracks. Do this in the old system before the export. A difference found after cutover could be a migration
error or a pre-existing one, and you will not be able to tell which.

## Sequence for cutover week

1. Stop entering new commitments and change orders in the old system at an agreed time.
2. Post everything for the period. Pay the AP run that is due. Submit the owner pay applications for the period.
3. Close the period in the old system.
4. Print the control reports: contract status, job cost summary, commitment register, billing history,
   retainage receivable and payable, open AP and AR, WIP. Save them as PDFs. These are the
   `control_totals`.
5. Tie job cost to the GL.
6. Export, map, load.
7. Reconcile to the cent ([chapter 6](06-reconciliation.md)) and sign off.
8. Open the new system for entries.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
