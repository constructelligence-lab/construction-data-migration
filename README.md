# Construction data migration: a practical guide and toolkit

Moving a construction company to a new accounting, project management or scheduling system is not an IT
project. It is an accounting close, a document handover and a schedule re-baseline, all at once, on live
jobs. This guide covers how to plan one, what has to move, how to cut over, and how to **prove** the result:
every open job tied out to the old system's own reports, to the cent.

It comes with a small, dependency-free Python toolkit that does the checking: a profiler for raw exports, a strict
CSV mapper, a to-the-cent reconciliation with 26 checks and a sign-off document, a schedule conversion check for
Primavera P6 and Microsoft Project, and file manifests for document archives. There is a
[check catalogue](CHECKS.md) of every automated and manual check, and an [`AGENTS.md`](AGENTS.md) so an AI agent
can help run the process without being trusted to sign it off.

**Updated September 2026 · the guide is about ninety minutes' read · the toolkit needs Python 3.9+ and nothing else.**

![chapters](https://img.shields.io/badge/chapters-16-1f6feb) ![checks](https://img.shields.io/badge/automated%20checks-40-2ea043) ![dependencies](https://img.shields.io/badge/dependencies-none-2ea043) ![agents](https://img.shields.io/badge/AGENTS.md-included-6e7781) ![licence](https://img.shields.io/badge/licence-CC%20BY%204.0%20%2B%20MIT-6e7781)

---

## Who this is for

| If you are… | Start with | The question you actually have |
| --- | --- | --- |
| Owner / GM | [Why migrations fail](01-why-migrations-fail.md) | "What goes wrong, and what does it cost us?" |
| Controller / finance | [Financial cutover](06-financial-cutover.md), [Reconciliation](07-reconciliation.md) | "How do I know nothing was lost?" |
| Project manager | [The records that matter](03-the-records-that-matter.md), [Project records](08-project-records-and-documents.md) | "Will my commitments, change orders and RFIs be right on day one?" |
| Scheduler | [Schedules](09-schedules.md) | "Did the logic survive the conversion?" |
| Learning by doing | [A worked example](16-worked-example.md) | "Show me the whole thing once, on real-looking data" |
| IT / systems / whoever was handed this | [Plan the migration](02-plan-the-migration.md), [Cutover runbook](11-cutover-runbook.md), [Check catalogue](CHECKS.md) | "What do I do, in what order, and how do I know it worked?" |
| Buying a new system | [Working with vendors and implementers](14-working-with-vendors-and-implementers.md) | "What must be in the contract?" |
| Anyone holding the exports | [Handling migration data safely](13-handling-migration-data-safely.md) | "What must not leak?" |
| An AI agent helping any of the above | [`AGENTS.md`](AGENTS.md) | "What may I do, and what must a person decide?" |

## Contents

1. **[Why construction data migrations fail](01-why-migrations-fail.md)**
   The fourteen failures that recur, and the one mistake behind them: moving data instead of moving obligations.
2. **[Plan the migration](02-plan-the-migration.md)**
   Inventory, scope record by record, the cutover date, the people, trial loads, the parallel run, and what
   happens to the old system.
3. **[The records that matter](03-the-records-that-matter.md)**
   A neutral model of the nine records that carry every financial obligation on an open job.
4. **[Source data quality: clean before you map](04-source-data-quality.md)**
   Where to fix a problem, profiling every export, and the clean-up list for vendors, jobs, codes, commitments,
   cash and documents.
5. **[Cost codes and crosswalks](05-cost-codes-and-crosswalks.md)**
   Keep, clean or replace; never rename a code with postings; many-to-one is fine, one-to-many is not.
6. **[Financial cutover](06-financial-cutover.md)**
   Detail or balance, owner billing, commitments, retainage in both directions, payroll and tax reporting,
   WIP, and the GL tie-out.
7. **[Reconciliation: proving the migration](07-reconciliation.md)**
   Seven control totals per job, why to the cent, twenty-six checks, and how to chase a difference.
8. **[Project records and documents](08-project-records-and-documents.md)**
   Numbers, history, attachments and obligations; archives that can be used; legal holds; file manifests.
9. **[Schedules](09-schedules.md)**
   What survives a P6 or Project conversion and what does not, and how to check it link by link.
10. **[Integrations and reports](10-integrations-and-reports.md)**
    Bank files, payroll imports, field apps and lender reports, and rebuilding the reports people actually use.
11. **[Cutover runbook](11-cutover-runbook.md)**
    Week by week from T minus 12 to the end of the parallel run.
12. **[After go-live: the first 90 days](12-after-go-live.md)**
    Hypercare, the first month-end roll-forward, warning signs, and the day 90 review.
13. **[Handling migration data safely](13-handling-migration-data-safely.md)**
    Tax IDs, bank details, payroll, pricing and client documents in plain files.
14. **[Working with vendors and implementers](14-working-with-vendors-and-implementers.md)**
    Who does what, the questions to ask before you sign, and what the statement of work must say.
15. **[Questions we get asked](15-faq.md)**
16. **[A worked example, end to end](16-worked-example.md)**
    One trial load on the samples, from profiling the exports to go/no-go, with the real commands and output. Start
    here if you learn by doing.

**[The check catalogue](CHECKS.md)** lists every check in the guide, automated and manual, with who owns it and
when it runs. **[The glossary](GLOSSARY.md)** defines the migration terms the guide uses.

## Templates you can use today

| Template | Use it for |
| --- | --- |
| [Migration inventory](templates/migration-inventory.csv) | Every system and spreadsheet that holds job data, and how the data gets out |
| [Scope decisions](templates/scope-decisions.csv) | Detail, balance, archive or leave, record by record, agreed in writing |
| [Cost code crosswalk](templates/cost-code-crosswalk.csv) | Old code to new code, with the reason for every merge |
| [Field mapping](templates/field-mapping.csv) | Every target field, its source report and column, and its transform |
| [Integration inventory](templates/integration-inventory.csv) | Every connection in and out, and whether it is rebuilt, replaced or retired |
| [Report rebuild list](templates/report-rebuild-list.csv) | The reports people use, their definitions, and who signs each one off |
| [Issue log](templates/issue-log.csv) | Every problem from trial load 1 to day 90, with its cause and where it was fixed |
| [Parallel run log](templates/parallel-run-log.csv) | Job-by-job comparison for the period after cutover |
| [Vendor and implementer questions](templates/vendor-and-implementer-questions.md) | What to ask, and get in writing, before you sign |
| [Cutover checklist](templates/cutover-checklist.md) | The printable, signable version of the runbook |
| [Go / no-go](templates/go-no-go.md) | The decision to open the new system: what must be yes, what can be accepted with an owner |
| [Reconciliation sign-off](templates/reconciliation-sign-off.md) | The three-signature sign-off, for when you reconcile by other means |

## The toolkit

Standard-library Python, no install step, no network access. Clone the repository and run it from the root.

```bash
python3 -m cdm profile EXPORT.csv                         # inspect a raw export before mapping it (14 checks)
python3 -m cdm map MAPPING.json EXPORT.csv --out FILE.csv # turn an old system's export into a record file
python3 -m cdm validate DIR                               # check record files against the neutral schema
python3 -m cdm reconcile DIR --markdown sign-off.md       # tie out to control totals (26 checks), write a sign-off
python3 -m cdm schedule FILE.xer                          # read a P6 XER or Project XML schedule
python3 -m cdm schedule-compare SOURCE TARGET             # check a schedule survived a conversion
python3 -m cdm manifest DIR --out manifest.csv            # hash every file in a document export
python3 -m cdm manifest-compare BEFORE AFTER              # prove an archive arrived complete and unaltered
```

Try it on the synthetic samples. The clean set passes; the broken set has
[twelve planted faults](samples/README.md#the-planted-faults), and every one is caught:

```text
$ python3 -m cdm reconcile samples/broken
...
ERROR   R09 vendor V-2005 carries a full tax ID; keep the last four digits only and remove this file from wherever it has been
ERROR   R14 [J-1104] B2603-004 is invoiced by V-2003 against SC-1104-02, which belongs to V-2002
ERROR   T01 [J-1104] cost_to_date: old system 1,213,290.57, migrated 1,230,026.02, difference +16,735.45
ERROR   T01 [J-1107] contract_value: old system 976,600.00, migrated 989,250.00, difference +12,650.00
WARNING R13 [J-1104] B2602-030-R matches B2602-030 (line 31) on job, code, type, date, amount and vendor: a re-run export, or two genuine charges
WARNING R20 vendors V-2001, V-2010 look like the same business; merge them before cutover or history splits between them
...
FAIL: do not cut over  (13 errors, 3 warnings, 1 notes)
```

And a vendor list that should never have left the accounting system:

```text
$ python3 -m cdm profile samples/legacy-export/vendor-list.csv
...
ERROR   P10 [Tax ID] looks like full tax IDs: drop this column at export, keep the last four digits at most
WARNING P07 [Last Payment] every value has day and month of 12 or less; confirm the format from the source system's settings
WARNING P12 [YTD Paid] 2 value(s) such as '2.51E+04': re-export from the source system, not from a spreadsheet
WARNING P14 [Name] 1 group(s), e.g. 'SAMPLE DRYWALL CO.' / 'Sample Drywall Co': merge before mapping
```

| Piece | What it does |
| --- | --- |
| [`schema/fields.csv`](schema/fields.csv) | The neutral model: nine records, every field typed and described. Readable in Excel |
| [`cdm/profile.py`](cdm/profile.py) | Finds ambiguous dates, filtered credits, spreadsheet damage, lost leading zeros, duplicate names and tax IDs in raw exports |
| [`cdm/mapping.py`](cdm/mapping.py) | Strict CSV mapping: crosswalks, lookups, templates, explicit date formats, exact money parsing. Nothing is guessed or passed through |
| [`cdm/reconcile.py`](cdm/reconcile.py) | Seven control totals per job, recomputed independently and compared to the cent, plus integrity and consistency checks |
| [`cdm/schedule/`](cdm/schedule/) | P6 XER and Microsoft Project XML readers, and an activity-by-activity, link-by-link conversion check |
| [`cdm/manifest.py`](cdm/manifest.py) | SHA-256 manifests that prove a document export or archive is complete and unaltered |
| [`mappings/`](mappings/README.md) | The mapping format, with a worked example |
| [`samples/`](samples/README.md) | Synthetic jobs, messy legacy exports and schedules, all generated by a script |

Run the checks the way CI does: `python3 scripts/check_repo.py`.

The clean tables in `schema/fields.csv` also convert straight into the
[construction schema](https://github.com/constructelligence-lab/construction-schema), which links the ledger to the
project records (RFIs, change events, submittals) behind it:
`python3 -m cschema convert construction-data-migration path/to/clean -o ledger.jsonl`.

## Using an AI agent

AI coding agents are good at the legwork of a migration: profiling exports, drafting crosswalks and mappings,
running every check and explaining the differences. They must not be the ones deciding what is acceptable.
[`AGENTS.md`](AGENTS.md) (also loaded by Claude Code through [`CLAUDE.md`](CLAUDE.md)) gives any agent working
in this repository:

- **rules that do not bend:** never invent a control total, never edit loaded data to force a tie-out, never guess a
  date format or a code mapping, never round money, never handle full tax IDs or send data to outside services;
- **the workflow**, stage by stage, with the commands to run and a working-folder layout that keeps real data out of
  git;
- **what to escalate, and to whom**: controller, data owner, accountant, counsel;
- **a report format** that separates what was explained from what still needs a decision.

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

<!-- begin:family -->
## More from Constructelligence

Open construction resources from the same team, all maintained alongside this one:

| Repository | What it is |
| --- | --- |
| [AI in construction](https://github.com/constructelligence-lab/ai-in-construction) | A practical guide to AI in construction: what works today, what the data has to look like, the risks, and a 90-day plan. |
| [Construction project records](https://github.com/constructelligence-lab/construction-project-records) | Open schemas, templates and a checker for RFIs, submittals, change events, daily reports and punch lists. |
| [Construction schema](https://github.com/constructelligence-lab/construction-schema) | One record format for construction project data, with provenance, classifications and links, built for AI. |
| [Construction reference data](https://github.com/constructelligence-lab/construction-data) | Cost codes, units, waste factors, pay units, trade sequence, glossary and metric formulas in CSV. |
| [Construction reference MCP server](https://github.com/constructelligence-lab/construction-mcp) | An offline MCP server that gives AI assistants construction reference data and calculators. |
| [Construction prompts](https://github.com/constructelligence-lab/construction-prompts) | 28 prompts for ChatGPT, Claude and Gemini, from bid go/no-go to notice letters. |
| [Construction agent skills](https://github.com/constructelligence-lab/construction-agent-skills) | 28 installable agent skills for Claude Code and any agent that reads SKILL.md. |
| [Open source construction tools](https://github.com/constructelligence-lab/open-source-construction-tools) | Open source software for BIM, CAD, scheduling and site work, verified against the GitHub API. |

<!-- end:family -->


## Licence

Guide, templates, schema and sample data: **CC BY 4.0**. Code in `cdm/`, `scripts/` and `tests/`: **MIT**. See
[`LICENSE`](LICENSE). Product names are trademarks of their owners, used only to identify formats and systems;
no affiliation or endorsement is implied.

---

*Maintained by [Constructelligence](https://constructelligence.co) — building the AI infrastructure for
construction.*
