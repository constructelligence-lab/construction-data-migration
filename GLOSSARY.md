# Glossary of migration terms

The words this guide uses, as it uses them. For construction terms in general, see the glossary in
[construction-data](https://github.com/constructelligence-lab/construction-data).

| Term | Meaning here |
| --- | --- |
| **Archive** | Records exported from the old system to a read-only store with an index, and not loaded into the new one ([chapter 8](08-project-records-and-documents.md#archives-that-can-be-used)) |
| **Balance** | One summarised figure per job, cost code and cost type, dated at cutover, in place of line-by-line history. In the neutral model its source is `opening_balance` |
| **Ball in court** | The party who owes the next action on an open item |
| **Control total** | A figure printed by the old system's own report at cutover, used as the answer the migrated data must reproduce ([chapter 7](07-reconciliation.md#the-control-totals)) |
| **Crosswalk** | A table mapping each old code to its new code, with the reason for every merge ([chapter 5](05-cost-codes-and-crosswalks.md#the-crosswalk-file)) |
| **Cutover** | The point at which the old system stops being the book of record and the new one starts. Always a closed period end |
| **Data owner** | The person inside the company who owns the migration: inventory, mappings, trial loads, issue log ([chapter 2](02-plan-the-migration.md#step-4-name-the-people)) |
| **Detail** | Every open record migrated line by line with its own identifier, so it can be acted on after cutover |
| **Export route** | How data gets out of a system: API, documented format, report export, database extract, or copy and paste ([export routes](sources/export-routes.md)) |
| **Go / no-go** | The decision, on the last day before the new system opens, whether to open it ([template](templates/go-no-go.md)) |
| **Hypercare** | The first two weeks after go-live, with daily check-ins and a review of every new commitment and change ([chapter 12](12-after-go-live.md#weeks-1-to-2-hypercare)) |
| **Manifest** | A list of every file in an export or archive with its size and SHA-256 hash, used to prove a copy is complete and unaltered |
| **Mapping** | A file that says how each field of an old system's export becomes a field of the neutral model ([mappings](mappings/README.md)) |
| **Neutral model** | The nine record types this guide maps everything into and out of ([chapter 3](03-the-records-that-matter.md)) |
| **Open obligation** | Anything the company still has to do after cutover: pay, bill, release retainage, answer, argue a change. The thing a migration exists to move |
| **Parallel run** | One period after cutover in which the essentials are entered in both systems and compared job by job ([chapter 2](02-plan-the-migration.md#step-6-run-in-parallel-for-one-period)) |
| **Profile** | An automated inspection of a raw export before mapping, for problems such as ambiguous dates and spreadsheet damage ([chapter 4](04-source-data-quality.md#profile-every-export-first)) |
| **Reconciliation** | Recomputing each control total from the migrated data and comparing it to the old system's figure, to the cent ([chapter 7](07-reconciliation.md)) |
| **Roll-forward** | Checking at a later period end that opening balance plus the period's activity equals the closing balance ([chapter 12](12-after-go-live.md#the-first-month-end)) |
| **Scope decision** | For each record type, the choice of detail, balance, archive or leave, agreed in writing ([chapter 2](02-plan-the-migration.md#step-2-decide-the-scope-record-by-record)) |
| **Sign-off** | The reconciliation document signed by the controller, the PM lead and the data owner, with the control reports attached |
| **Staging area** | The single, access-controlled place where exports are kept during the migration, and deleted from afterwards ([chapter 13](13-handling-migration-data-safely.md)) |
| **Trial load** | A full rehearsal of the load into a test copy of the new system, reconciled like the real one. Plan for at least two |

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
