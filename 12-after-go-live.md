# After go-live: the first 90 days

Signing off the reconciliation proves the data arrived. It does not prove the company is using the new system
correctly. Most of the damage from a migration is done in the first two months after cutover, by people
entering new data the old way. This chapter covers how to catch that early.

## Weeks 1 to 2: hypercare

- **A daily fifteen-minute check-in** with the data owner, an accounting lead and a PM lead. Log every problem in
  [`templates/issue-log.csv`](templates/issue-log.csv), with an owner and a date.
- **Someone reviews every new commitment, change order and budget change** before it is approved. Coding habits
  form in the first fortnight.
- **Watch the first transactions through end to end**: the first AP invoice against a migrated commitment, the
  first payroll import, the first retainage release, the first RFI answered.
- **Keep the old system read-only and easy to reach.** People will need to look things up. Do not let them key
  anything into it.

## The first month-end

The first period close in the new system is the real test. Before closing:

- [ ] Every open job's cost to date in the new system equals the cutover balance plus the period's postings
- [ ] Job cost ties to the general ledger
- [ ] The first pay application from the new system continues the numbering and agrees with the owner's copy of the last one
- [ ] Retainage receivable and payable roll forward: opening balance, plus held, less released, equals closing balance
- [ ] Committed cost rolls forward: opening, plus new commitments and approved changes, equals closing
- [ ] No cost posted to inactive codes, and no cost posted without a budget line (run the reconciliation again: `R04`, `R23`)
- [ ] Every integration delivered what it was supposed to, for the whole period
- [ ] The WIP schedule from the new system agrees with the parallel run

The reconciliation toolkit works for roll-forwards too. Export the new system's records at month-end, enter the
new control totals, and run `cdm reconcile` again. The checks are the same; only the date changes.

## Signs that something is wrong

| You see | It usually means |
| --- | --- |
| Cost appearing on codes that nobody budgets | People are picking codes from a long list rather than the job's budget |
| New vendors that look like existing ones | The vendor search is not being used before setup. Run the reconciliation's `R20` check monthly |
| Change orders approved without a commitment change order to match | PM and accounting workflows are not connected yet |
| Pay applications rejected by owners | The format or the numbering changed without warning |
| Reports people have stopped opening | The report they used was not rebuilt, and they have gone back to a spreadsheet |
| A spreadsheet appearing next to the new system | Something the old system did is missing. Find out what, fast |

## Day 90: review

Hold a review with the controller, the PM lead, the field lead and the data owner:

1. **What does the new system report that the old one did not?** That is the return on the project.
2. **What did the old system report that the new one does not?** Either rebuild it or decide it is not needed.
3. **What is still being done in spreadsheets?** Each one is a decision: bring it in, or accept it.
4. **Which issues in the log are still open?** Close them or put them on a roadmap with an owner.
5. **Can the old system be switched off?** Only if the archive is complete and verified
   (`cdm manifest-compare`, [chapter 8](08-project-records-and-documents.md#reconciling-documents)) and the
   retention decisions from [chapter 2](02-plan-the-migration.md#step-7-decide-what-happens-to-the-old-system)
   are met.

Delete the staging copies of the exports once the review is done, and record that you did
([chapter 13](13-handling-migration-data-safely.md)).

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
