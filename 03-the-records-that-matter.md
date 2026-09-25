# The records that matter

Every construction system names things differently. One calls it a phase, the next a cost code, a third a
cost item. A commitment is a subcontract in one system and a PO in the next. This guide uses a small
**neutral model**: nine record types that carry every financial obligation on an open job. Map each old
system's exports into it, then out of it into the new system. Keeping the model in the middle means the
reconciliation in [chapter 7](07-reconciliation.md) works the same whichever two systems you are moving
between.

The full field list, with types, allowed values and a description of every field, is in
[`schema/fields.csv`](schema/fields.csv). The [samples](samples/README.md) show a complete, reconciled
example.

## The nine records

| Record | One row is | Why it matters | The trap |
| --- | --- | --- | --- |
| `jobs` | A job | Everything hangs off it | Reusing a job number that meant a different job in the old system |
| `cost_codes` | A cost code in the new numbering | The spine of every cost report | Renaming codes that already carry postings ([chapter 5](05-cost-codes-and-crosswalks.md)) |
| `budgets` | A job, code and cost type budget line | Budget-to-actual and cost-to-complete | Loading the revised budget as the original, which erases the history of every change |
| `vendors` | A subcontractor or supplier | Commitments, payments, tax reporting | Leaving behind inactive vendors that still hold retainage, or carrying full tax IDs in the file |
| `commitments` | A subcontract or purchase order | What you owe and will owe | Migrating the balance only, so the next invoice cannot be matched |
| `change_orders` | An owner or commitment change order | Contract value, committed cost, exposure | Dropping pending and rejected ones, or loading pending ones as approved |
| `cost_transactions` | A posted cost line, or an opening balance | Cost to date | Duplicates from a re-run export, and credits lost to a positive-only filter |
| `billings` | An owner pay application | Billed to date, retainage receivable | Restarting application numbers at 1 on the first new application |
| `control_totals` | One figure from the old system's own report | The proof | Taking figures from a spreadsheet instead of the system's printed report |

## What each record has to carry

**Keep originals and changes apart.** `budgets` has `original_budget` and `approved_changes`, and
`commitments` has `original_value` with change orders as separate rows. A migration that loads only the
revised figure loses the answer to the question every owner eventually asks: *what did we start at, and
what changed?*

**Keep the old system's references.** Every `cost_transactions` row carries a `transaction_id` built from
the old system's batch and line, or its invoice reference. If a figure is ever questioned, you need to trace
a line in the new system back to the line it came from in one step.

**Keep status honestly.** A change order is `approved`, `pending`, `rejected` or `void`, and only
approved ones count toward contract value and committed cost. Pending change orders are the company's
open exposure. They are often worth more attention than the approved ones, and they are the ones most
often lost, because many old systems keep them in a spreadsheet rather than in the ledger.

**Keep tax IDs out.** The vendor record carries `tin_last4`, the last four digits, and nothing else. The
new system's vendor setup needs the full tax ID. Enter it there from the W-9 or equivalent, through the new
system's own secure process. Do not pass it through a migration file that gets emailed, copied and
attached to issue logs. The reconciliation refuses a file that carries more than four digits.

## What is not in the neutral model, and where it goes

| Data | Where it goes | Why it is left out |
| --- | --- | --- |
| Payroll, employee records, benefits | The payroll provider's own conversion | It is regulated personal data with its own year-to-date tax rules. Move it through the payroll provider's process, with your accountant |
| Certified payroll and prevailing wage records | Archive, kept retrievable | They are compliance records that must be produced on request, not operational data |
| Equipment rates and usage | The new system's equipment module, if it has one | The structure varies too much between systems to model neutrally |
| Lien waivers, insurance certificates, bonds | Document migration ([chapter 8](08-project-records-and-documents.md)) | They are documents with dates and signatures, not ledger records |
| RFIs, submittals, change events, daily reports, punch lists | Their own logs; open schemas and a checker are in [construction-project-records](https://github.com/constructelligence-lab/construction-project-records) | They are project records with numbers and histories, not ledger records ([chapter 8](08-project-records-and-documents.md)) |
| Estimates and bid history | The estimating system, or the archive | Estimates are not obligations. Keep them where estimators can compare them |
| General ledger | Your accountant's conversion plan | The job cost subledger must tie to the GL ([chapter 6](06-financial-cutover.md#tie-the-job-cost-ledger-to-the-general-ledger)), but the GL conversion itself is accounting work |

## Validating files against the model

```bash
python3 -m cdm validate path/to/your/records
```

This checks that every file parses, that every required field is present, that amounts are exact to the cent,
that dates are ISO dates and that enumerated fields hold allowed values. Fix these before you reconcile.
A reconciliation run on malformed files only tells you the files are malformed.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
