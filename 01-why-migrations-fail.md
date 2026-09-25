# Why construction data migrations fail

A data migration in a construction company is not an IT project. It is an accounting close, a document
handover and a schedule re-baseline, all at once, on live jobs, while subcontractors wait to be paid and
owners wait for the next pay application. That is why the failures are expensive. A dropped retainage
balance does not throw an error. It shows up eleven months later, when a subcontractor asks for their
money and nobody can say how much they are owed.

The failures are also predictable. The same dozen come up again and again, and every one of them can be
prevented before cutover.

## The twelve failures

| # | What goes wrong | How it shows up | Prevented in |
| --- | --- | --- | --- |
| 1 | **Moving everything.** Ten years of closed jobs are loaded "to be safe" | The load takes months, every mapping has a hundred exceptions, and nobody can reconcile history nobody remembers | [Plan the migration](02-plan-the-migration.md#step-2-decide-the-scope-record-by-record) |
| 2 | **Cutting over mid-period** | Half of August is in one system and half in the other, and neither produces a correct August report | [Plan the migration](02-plan-the-migration.md#step-3-choose-the-cutover-date) |
| 3 | **Balances without detail** | Cost to date migrated as one number per job, so the next subcontractor invoice cannot be matched to its commitment | [Financial cutover](05-financial-cutover.md) |
| 4 | **Cost codes renamed after posting** | Budget-to-actual reports split one scope across two codes, and the variance looks like an overrun | [Cost codes and crosswalks](04-cost-codes-and-crosswalks.md) |
| 5 | **Pending change orders vanish, or turn approved** | Contract value is wrong on day one; exposure reports stop showing the money still being argued about | [Reconciliation](06-reconciliation.md) |
| 6 | **Retainage is lost** | Warranty jobs that "looked closed" were left behind with retainage still owed in both directions | [Financial cutover](05-financial-cutover.md#retainage-in-both-directions) |
| 7 | **"Close enough" totals** | A $0.43 difference on one job turns out to be a $41,000 duplicate netted against a $40,999.57 missing credit | [Reconciliation](06-reconciliation.md#why-to-the-cent) |
| 8 | **Documents lose their numbers** | RFI 047 becomes "Question about stair" with a new ID; the log no longer matches the correspondence that cites it | [Project records](07-project-records-and-documents.md) |
| 9 | **Schedule logic lost in conversion** | One relationship on the critical path disappears and the forecast finish moves, silently | [Schedules](08-schedules.md) |
| 10 | **The old system is switched off too early** | An auditor, a lender or a claims consultant asks for a report that no longer exists | [Plan the migration](02-plan-the-migration.md#step-7-decide-what-happens-to-the-old-system) |
| 11 | **Nobody inside owns it** | The vendor's consultant leaves after go-live and takes the only understanding of the mappings with them | [Plan the migration](02-plan-the-migration.md#step-4-name-the-people) |
| 12 | **Training happens after go-live** | The first month of data in the new system is coded by people guessing, so the first month of reports is wrong | [Cutover runbook](09-cutover-runbook.md) |

## The pattern behind them

Almost every item above comes from one mistake: **treating the migration as moving data rather than as
moving obligations.** The new system does not need your old data. It needs to know, on the morning after
cutover, everything the company still has to do:

- pay each subcontractor and supplier the right amount, retainage included
- bill each owner correctly on the next pay application, under the right application number
- answer each open RFI and submittal by its due date
- keep every change order that is still being argued about in the argument
- run the schedule forward from the same logic and the same data date

A migration is finished when every one of those obligations can be acted on in the new system, and the
figures behind them tie out to the old system's own reports to the cent. Everything else is archive.

## What a good migration looks like

- **It has one named owner inside the company**, not at the software vendor.
- **The scope is small and explicit.** Open jobs in detail, closed jobs archived, and the rule for each
  record type written down before anything is exported.
- **It cuts over at a period end**, after the old system's period is closed and its reports are printed.
- **It is rehearsed.** At least two full trial loads, each one reconciled, before the real one.
- **It is proven, not asserted.** Control totals from the old system, recomputed from the new data, signed
  off by the controller, the PM lead and the data owner. [Chapter 6](06-reconciliation.md) shows how, and
  [the toolkit](README.md#the-toolkit) does the arithmetic.
- **The old system stays readable** for as long as the records might be needed.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
