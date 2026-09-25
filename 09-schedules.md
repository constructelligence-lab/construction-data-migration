# Schedules

A schedule conversion looks like the easiest part of a migration: export a file, import a file, and the bars
look the same. Then the next update is run, and the forecast finish moves by three weeks, because one
relationship on the critical path did not survive the trip, or a ten-day lag became a one-day lag.

This chapter covers what survives a conversion, what does not, and how to check it activity by activity and
link by link.

## Check the contract before you change tools

Many contracts specify the scheduling software, the file format for submissions, or both, typically in the
scheduling section of Division 01 of the specifications. Changing tools on a job whose contract requires a
particular format can put you in breach, or make your schedule submissions non-compliant. That matters most
when the schedule becomes evidence in a delay claim. For those jobs, keep producing submissions in the
contractual format, whatever tool you use internally.

## Formats

| Format | What it is | Notes |
| --- | --- | --- |
| **XER** | Primavera P6 text export: tab-delimited tables for projects, WBS, activities, relationships, calendars, resources and codes | The usual exchange format for P6 schedules. Read by `cdm` |
| **Microsoft Project XML (MSPDI)** | Microsoft Project's XML format, [documented publicly by Microsoft](https://learn.microsoft.com/en-us/office-project/xml-data-interchange/introduction-to-project-xml-data) | Use this rather than the binary `.mpp` format for any conversion. Read by `cdm` |
| **P6 XML** | Primavera's own XML export | Carries more than XER in some areas. Not read by `cdm` yet |
| **Native files** (`.mpp`, P6 database backups) | The tools' own formats | Always keep the native file of every submitted update as the record |

## What survives, and what does not

| Element | Usually survives | Often lost or changed |
| --- | --- | --- |
| Activities, names, IDs | Yes | Activity IDs, when the target tool has no equivalent field |
| Durations | Yes, in hours | Elapsed durations; durations on non-standard calendars |
| Relationships | Types (FS, SS, FF, SF) usually | Relationships to activities in other projects (external links) |
| Lags | The value | **Lag calendars.** P6 can calculate lag on different calendars; Project cannot. Percentage lags |
| Calendars | Working days and hours | Holidays and exceptions, and calendars assigned per activity |
| Constraints | Common ones (start no earlier than, finish no later than) | Mandatory constraints and the tools' different constraint types |
| Progress | Actual dates | **Percent complete.** P6 physical % and Project's duration % are different measures |
| Data date | Usually | Status date semantics differ; confirm it after import |
| Baselines | Sometimes | Often dropped, or imported as the current plan |
| WBS | As summary tasks in Project | Code values and hierarchy detail |
| Activity codes and custom fields | Rarely | Almost always need manual mapping |
| Resources and cost loading | Sometimes | Rates, curves and resource calendars |
| Level-of-effort and hammock activities | As ordinary tasks | Their special behaviour |
| Scheduling options | Rarely | Retained logic versus progress override, which moves dates on the next update |

## The conversion, step by step

1. **Freeze an update.** Pick the latest statused update. Record its data date, its forecast finish and its
   critical path.
2. **Export** from the source tool in the most complete format available, and keep the native file.
3. **Convert** or import into the target tool.
4. **Compare the two files** with `cdm schedule-compare` (below). Fix every error before going further.
5. **Reschedule in the target tool** at the same data date, then compare the forecast finish and the critical
   path with step 1. If they differ, find out why before anyone relies on the new file. The usual causes are
   calendars, constraints, lag calendars and scheduling options.
6. **Record the conversion**: source file, target file, differences found and how they were resolved. On a
   job that may end in a delay claim, this record is part of the schedule's credibility.

## Checking a conversion

Read one file and see what is in it:

```bash
python3 -m cdm schedule samples/schedules/fitout.xer --out out/schedule
```

```text
fitout.xer: project J-1104-FITOUT, data date 2026-08-31 17:00:00
  16 activities, 19 relationships, 1 calendars
  open starts (no predecessor): 1  A1000
  open ends (no successor):     1  A1150
  WARNING not read (check these by hand after any conversion): ACTVCODE
```

Compare the source with the converted file. Match activities by name when the target tool has no activity ID
field:

```bash
python3 -m cdm schedule-compare samples/schedules/fitout.xer samples/schedules/fitout-lossy-conversion.xml --match name
```

```text
fitout.xer: 16 activities, 19 relationships, 2026-02-02 to 2026-11-06
fitout-lossy-conversion.xml: 16 activities (+3 summary rows), 18 relationships, 2026-02-02 to 2026-11-06
ERROR   relationship hang and finish board -> prime and first coat paint (FF) is missing from fitout-lossy-conversion.xml
ERROR   relationship hang and finish board -> ceiling grid: lag 120h became 16h

FAIL  (2 errors, 1 warnings)
```

The comparison checks every activity is present with the same type, dates, actual dates and duration; every
relationship is present with the same type and lag; and the data dates agree. It warns on percent complete,
calendar changes and anything the readers could not interpret. WBS summary rows are left out of the comparison,
because P6 and Project represent WBS differently.

Both readers take lag and duration in **working hours**. Project XML stores lag in tenths of a minute, so a
`LinkLag` of 4800 is 8 hours. That unit is a common source of hand-conversion errors.

## Limits of the readers

The readers cover what a conversion check needs: projects, WBS, activities, relationships, calendars (by name)
and data dates. They do not read resources, costs, activity codes, user-defined fields, baselines or calendar
exceptions, and they list what they skipped so you know what to check by hand. Treat a passing comparison as
"the logic and dates came across", not "the whole schedule came across".

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
