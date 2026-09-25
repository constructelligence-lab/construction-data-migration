# Questions we get asked

### Where do I start?

With [the worked example](16-worked-example.md). It runs a whole trial load on the sample data in ten minutes, and shows
what every check is for. Then read [why migrations fail](01-why-migrations-fail.md) and
[plan the migration](02-plan-the-migration.md).

### How long does a migration take?

For a contractor with a few dozen open jobs, twelve to sixteen weeks from inventory to the end of the parallel
run is realistic ([the shape of a plan](02-plan-the-migration.md#a-typical-shape)). The biggest variable is not
the software. It is how much of the source data has to be fixed before it can be mapped.

### Should we migrate our history?

Usually not in detail. Migrate open and warranty jobs in detail, cost history as balances, and archive closed
jobs in a form you can search. If you need historical cost for estimating, that is a reporting question. A
cost history extract kept alongside the new system is often better than forcing ten years of old postings into
new structures.

### Can the software vendor do the migration for us?

They can do the loading, and they should know their own import tools well. They cannot decide your scope,
own your mappings or sign your control totals, because they do not know your jobs. The migration data owner
has to be someone inside the company.

### Can AI do the mapping?

AI tools are useful for drafting: suggesting a crosswalk from two code lists, drafting a field mapping from
column headers, or explaining an unfamiliar export. They should not compute your control totals or decide
whether a difference matters. The reconciliation is the control, and it has to be arithmetic, not judgement.
Keep sensitive exports out of any tool whose terms let it keep what you give it
([chapter 13](13-handling-migration-data-safely.md)).

If you use an AI coding agent in this repository, it reads [`AGENTS.md`](AGENTS.md): the rules it follows (never
invent a control total, never edit loaded data to force a tie-out, never guess a date format, never handle full tax
IDs) and the workflow it runs. The agent does the legwork; the controller, the PM lead and the data owner still
make the calls and sign.

### Our totals are off by a few cents. Can we just book an adjustment?

Not until you know why. Small differences are often two large errors cancelling each other out
([why to the cent](07-reconciliation.md#why-to-the-cent)). If the cause turns out to be a genuine rounding policy
difference between the systems, that is the controller's decision to make and document, not a mapping fix.

### We are mid-year. Can we still cut over?

Yes, with a plan for year-to-date payroll and vendor tax reporting, agreed with your payroll provider and
accountant ([chapter 6](06-financial-cutover.md#payroll-and-tax-reporting)). A quarter start is often easier
than a random month end.

### We run everything in spreadsheets. Is this for us?

Yes, and arguably more so. Spreadsheets are an old system too. The same rules apply: inventory them, freeze
them, take control totals from them before you move, and reconcile to the cent. Spreadsheets are more likely
than accounting systems to hold duplicates, inconsistent codes and formulas that were overwritten, so trial
loads matter more.

### A job is in a dispute. Should we migrate it?

Speak to counsel first. You may need to preserve its records in their original form and system, with
metadata intact, and a migration can alter both. Many companies keep disputed jobs in the old system,
read-only, until the dispute is resolved.

### Which systems does this work with?

Any system that can export CSV. The neutral model, the mapping format and the reconciliation do not depend on
a particular product. The schedule readers handle Primavera P6 XER and Microsoft Project XML. Where a system
offers a documented public API, that is usually a better route than report exports; see
[export routes](sources/export-routes.md).

### Is this legal, tax or accounting advice?

No. It is general guidance on process and data. The questions in chapters 6, 8 and 13 are the ones to take to
your accountant, payroll provider and counsel, who know your jurisdiction, your contracts and your books.

### Can you help with our migration?

Yes. [Open an issue on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose)
using the *Migration help* template. Describe your systems and the problem, not your data. Or see what we do at
[constructelligence.co](https://constructelligence.co).

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
