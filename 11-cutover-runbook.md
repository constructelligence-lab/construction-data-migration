# Cutover runbook

A week-by-week plan from the decision to migrate to the end of the parallel run, for a contractor with a few
dozen open jobs. Adjust the timing to your size. Keep the order. A printable version is in
[`templates/cutover-checklist.md`](templates/cutover-checklist.md).

"T" is the cutover date: the period end on which the old system stops being the book of record.

## T minus 12 to 10 weeks: decide

- [ ] Name the migration data owner and give them the time to do it ([roles](02-plan-the-migration.md#step-4-name-the-people))
- [ ] Complete the [system inventory](templates/migration-inventory.csv), including the spreadsheets
- [ ] Agree the [scope decisions](templates/scope-decisions.csv) in writing with the controller and the PM lead
- [ ] Fix the cutover date with the controller, the payroll provider and the accountant
- [ ] Check every open job's contract for scheduling software and document storage requirements
- [ ] Agree with counsel which jobs are in, or near, a dispute, and what that means for their records
- [ ] Agree how long the old system stays readable, and check that its licence allows it

## T minus 10 to 7 weeks: map

- [ ] Freeze the cost code list; build the [crosswalk](templates/cost-code-crosswalk.csv)
- [ ] Write a [field mapping](templates/field-mapping.csv) for every record, naming the source report and column
- [ ] Clean the source data where the mapping exposes problems: duplicate vendors, dead codes, jobs never closed
- [ ] Tie job cost to the GL in the old system and clear any existing differences
- [ ] Profile every export (`cdm profile`) and clear the errors at source ([chapter 4](04-source-data-quality.md))
- [ ] Work through the [source data clean-up list](04-source-data-quality.md#the-clean-up-list)
- [ ] Inventory every [integration and report](10-integrations-and-reports.md); decide rebuild, replace or retire
- [ ] Set up a secure staging area for exports ([chapter 13](13-handling-migration-data-safely.md))

## T minus 7 to 5 weeks: trial load 1

- [ ] Export as of the last closed period, using the final reports and mappings
- [ ] Map, validate (`cdm validate`), load into a test copy of the new system
- [ ] Reconcile to the cent against that period's control reports (`cdm reconcile`)
- [ ] Check document counts, file manifests (`cdm manifest-compare`) and the schedule conversion
- [ ] Test every rebuilt integration with trial files
- [ ] Log every issue; fix each one in the mapping or the source data

## T minus 5 to 3 weeks: trial load 2 and training

- [ ] Repeat the trial with the fixes, as of the next closed period
- [ ] Time every step. That timing is the plan for cutover week
- [ ] Train PMs, the field and accounting in the test copy, on their own jobs
- [ ] Rehearse the first week's tasks: an AP invoice against a migrated commitment, a pay application, an RFI

## T minus 2 weeks: prepare

- [ ] Brief subcontractors and owners if anything they see will change (portal, invoice address, pay application format)
- [ ] Confirm the new system's vendor tax IDs, bank details and insurance certificates are entered through its own secure process
- [ ] Agree the entry freeze time in the old system
- [ ] Book the controller, PM lead and data owner for cutover week

## T: cutover week

- [ ] Freeze new commitments and change orders in the old system
- [ ] Post everything for the period, pay the AP run, submit the period's pay applications
- [ ] Close the period
- [ ] Print the control reports as PDFs; enter `control_totals.csv`
- [ ] Tie job cost to the GL
- [ ] Final export, map, validate, load
- [ ] Reconcile to the cent; resolve every error; review every warning
- [ ] Reconcile document counts and the schedule conversion
- [ ] Sign off: controller, PM lead, data owner
- [ ] Set the old system to read-only
- [ ] Open the new system for entries

## T plus 1 to 5 weeks: parallel run

- [ ] Key cost, commitments and billing in both systems for one period
- [ ] At period end, compare job by job in the [parallel run log](templates/parallel-run-log.csv): cost to date,
      committed cost, billed to date, retainage, and over/under billing on the WIP schedule
- [ ] Explain every difference; sign off again
- [ ] Produce the first pay application from the new system, continuing the numbering
- [ ] Run the rebuilt reports in both systems and get each one signed off by its user

## T plus 6 weeks and on: close it out

- [ ] Stop double entry
- [ ] Delete staging copies of the exports, and record that you did
- [ ] Archive the old system's reports and raw data if it will be switched off, with an index
- [ ] Hand the mappings, crosswalk, sign-offs and issue log to whoever will own the new system
- [ ] Hold the [day 90 review](12-after-go-live.md#day-90-review)

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
