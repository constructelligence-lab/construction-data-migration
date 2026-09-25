# Construction data migration: a practical guide and toolkit

Moving a construction company to a new accounting, project management or scheduling system is not an IT
project. It is an accounting close, a document handover and a schedule re-baseline, all at once, on live
jobs. This guide covers how to plan one, what has to move, how to cut over, and how to **prove** the result:
every open job tied out to the old system's own reports, to the cent.

It comes with a small, dependency-free Python toolkit that does the proving: a neutral data model, a strict
CSV mapper, a reconciliation that produces a sign-off document, and a schedule conversion check for Primavera
P6 and Microsoft Project.

**Updated September 2026 · the guide is about an hour's read · the toolkit needs Python 3.9+ and nothing else.**

![chapters](https://img.shields.io/badge/chapters-11-1f6feb) ![checks](https://img.shields.io/badge/reconciliation%20checks-15-2ea043) ![dependencies](https://img.shields.io/badge/dependencies-none-2ea043) ![licence](https://img.shields.io/badge/licence-CC%20BY%204.0%20%2B%20MIT-6e7781)

---

## Who this is for

| If you are… | Start with | The question you actually have |
| --- | --- | --- |
| Owner / GM | [Why migrations fail](01-why-migrations-fail.md) | "What goes wrong, and what does it cost us?" |
| Controller / finance | [Financial cutover](05-financial-cutover.md), [Reconciliation](06-reconciliation.md) | "How do I know nothing was lost?" |
| Project manager | [The records that matter](03-the-records-that-matter.md), [Project records](07-project-records-and-documents.md) | "Will my commitments, change orders and RFIs be right on day one?" |
| Scheduler | [Schedules](08-schedules.md) | "Did the logic survive the conversion?" |
| IT / systems / whoever was handed this | [Plan the migration](02-plan-the-migration.md), [Cutover runbook](09-cutover-runbook.md) | "What do I do, in what order?" |
| Anyone holding the exports | [Handling migration data safely](10-handling-migration-data-safely.md) | "What must not leak?" |

## Contents

1. **[Why construction data migrations fail](01-why-migrations-fail.md)**
   The twelve failures that recur, and the one mistake behind them: moving data instead of moving obligations.
2. **[Plan the migration](02-plan-the-migration.md)**
   Inventory, scope record by record, the cutover date, the people, trial loads, the parallel run, and what
   happens to the old system.
3. **[The records that matter](03-the-records-that-matter.md)**
   A neutral model of the nine records that carry every financial obligation on an open job.
4. **[Cost codes and crosswalks](04-cost-codes-and-crosswalks.md)**
   Keep, clean or replace; never rename a code with postings; many-to-one is fine, one-to-many is not.
5. **[Financial cutover](05-financial-cutover.md)**
   Detail or balance, owner billing, commitments, retainage in both directions, payroll and tax reporting,
   WIP, and the GL tie-out.
6. **[Reconciliation: proving the migration](06-reconciliation.md)**
   Seven control totals per job, why to the cent, fifteen checks, and how to chase a difference.
7. **[Project records and documents](07-project-records-and-documents.md)**
   Numbers, history, attachments and obligations; archives that can be used; legal holds.
8. **[Schedules](08-schedules.md)**
   What survives a P6 or Project conversion and what does not, and how to check it link by link.
9. **[Cutover runbook](09-cutover-runbook.md)**
   Week by week from T minus 12 to the end of the parallel run.
10. **[Handling migration data safely](10-handling-migration-data-safely.md)**
    Tax IDs, bank details, payroll, pricing and client documents in plain files.
11. **[Questions we get asked](11-faq.md)**

## Templates you can use today

| Template | Use it for |
| --- | --- |
| [Migration inventory](templates/migration-inventory.csv) | Every system and spreadsheet that holds job data, and how the data gets out |
| [Scope decisions](templates/scope-decisions.csv) | Detail, balance, archive or leave, record by record, agreed in writing |
| [Cost code crosswalk](templates/cost-code-crosswalk.csv) | Old code to new code, with the reason for every merge |
| [Field mapping](templates/field-mapping.csv) | Every target field, its source report and column, and its transform |
| [Parallel run log](templates/parallel-run-log.csv) | Job-by-job comparison for the period after cutover |
| [Cutover checklist](templates/cutover-checklist.md) | The printable, signable version of the runbook |
| [Reconciliation sign-off](templates/reconciliation-sign-off.md) | The three-signature sign-off, for when you reconcile by other means |

## The toolkit

Standard-library Python, no install step, no network access. Clone the repository and run it from the root.

```bash
python3 -m cdm validate  DIR                     # check record files against the neutral schema
python3 -m cdm reconcile DIR --markdown out.md   # tie out to the old system's control totals, write a sign-off
python3 -m cdm map MAPPING.json EXPORT.csv --out FILE.csv   # turn an old system's export into a record file
python3 -m cdm schedule FILE.xer --out DIR       # read a P6 XER or Project XML schedule
python3 -m cdm schedule-compare SOURCE TARGET    # check a schedule survived a conversion
```

Try it on the synthetic samples. The clean set passes; the broken set has
[nine planted faults](samples/README.md#the-planted-faults), and every one is caught:

```text
$ python3 -m cdm reconcile samples/broken
...
ERROR   R09 vendor V-2005 carries a full tax ID; keep the last four digits only and remove this file from wherever it has been
ERROR   R06 [J-1098] owner has released 25,422.51 more retainage than was held
ERROR   T01 [J-1104] cost_to_date: old system 1,213,290.57, migrated 1,230,026.02, difference +16,735.45
ERROR   T01 [J-1107] contract_value: old system 976,600.00, migrated 989,250.00, difference +12,650.00
...
FAIL: do not cut over  (12 errors, 0 warnings, 1 notes)
```

| Piece | What it does |
| --- | --- |
| [`schema/fields.csv`](schema/fields.csv) | The neutral model: nine records, every field typed and described. Readable in Excel |
| [`cdm/mapping.py`](cdm/mapping.py) | Strict CSV mapping: crosswalks, lookups, templates, explicit date formats, exact money parsing. Nothing is guessed or passed through |
| [`cdm/reconcile.py`](cdm/reconcile.py) | Seven control totals per job, recomputed independently and compared to the cent, plus integrity checks |
| [`cdm/schedule/`](cdm/schedule/) | P6 XER and Microsoft Project XML readers, and an activity-by-activity, link-by-link conversion check |
| [`mappings/`](mappings/README.md) | The mapping format, with a worked example |
| [`samples/`](samples/README.md) | Synthetic jobs, a messy legacy export, and schedules, all generated by a script |

Run the checks the way CI does: `python3 scripts/check_repo.py`.

## Need help with a migration?

We help construction companies plan, map and reconcile data migrations. If you are planning one, stuck in
one, or cleaning up after one:

- **[Open an issue on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose)**
  using the *Migration help* template. Tell us which systems you are moving between and what is going wrong.
  Issues are public, so **describe your data, never paste it**: column headers and a made-up row are enough.
- Or find us at **[constructelligence.co](https://constructelligence.co)**.

## What this guide deliberately does not do

- **It does not recommend a system.** The same questions apply whichever product you are moving to.
- **It does not publish any vendor's confidential material.** Readers and mappings are built from public
  documentation and from what an export file visibly contains. See [export routes](sources/export-routes.md).
- **It does not use real data.** Every job, company, figure and date in the samples is synthetic.
- **It is not legal, tax, payroll or accounting advice.** It tells you which questions to take to your counsel,
  accountant and payroll provider. It does not answer them for your jurisdiction.

## Contributing

Corrections from people who have run a migration are the most valuable thing this repository can get. Useful
contributions:

- a failure mode we have missed, with how it showed up;
- a mapping for a common report export, built from your own export and public documentation with **synthetic
  values**;
- a check the reconciliation should make.

Run `python3 scripts/check_repo.py` before opening a pull request. Do not include real project data, customer-only
vendor documentation or anyone's personal data. We will remove it.

## Related

- [`construction-data`](https://github.com/constructelligence-lab/construction-data): reference data, including a
  starter cost code taxonomy mapped to CSI divisions.
- [`ai-in-construction`](https://github.com/constructelligence-lab/ai-in-construction): a practical guide to AI in
  construction. Chapter 3 explains why clean, coded, current data comes first.
- [`open-source-construction-tools`](https://github.com/constructelligence-lab/open-source-construction-tools):
  verified open source software for construction, including schedule and document tools.

## Licence

Guide, templates, schema and sample data: **CC BY 4.0**. Code in `cdm/`, `scripts/` and `tests/`: **MIT**. See
[`LICENSE`](LICENSE). Product names are trademarks of their owners, used only to identify formats and systems;
no affiliation or endorsement is implied.

---

*Maintained by [Constructelligence](https://constructelligence.co) — building the AI infrastructure for
construction.*
