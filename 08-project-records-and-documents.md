# Project records and documents

Project records are where the company's memory of a job lives: RFIs, submittals, drawings, change events,
daily logs, photos, meeting minutes, inspections, correspondence. Moving them is less about arithmetic than the
financial cutover, and more about **keeping identity and history intact**. A document that arrives without its
number, its revision history or the record of who had the ball loses most of its value as evidence.

## The four things every record must keep

1. **Its number.** RFI 047 must still be RFI 047. Correspondence, meeting minutes, change order backup and
   claims all cite records by number. If the new system cannot use your numbers as its IDs, store the old
   number in a searchable field and put it in the title.
2. **Its history.** Revisions, responses, resubmittals, status changes and dates. A submittal's value is the
   record that it was submitted on the 3rd, returned "revise and resubmit" on the 17th, and approved on the
   29th, not just the final approved PDF.
3. **Its attachments, attached.** Files must travel with the record they belong to. An export that separates
   the files from the records, with a promise to reconnect them later, usually means they are never reconnected.
4. **Its obligations.** For open items: who has the ball, and when the answer is due. That is what someone
   will act on the morning after cutover.

## Record by record

| Record | Open items | Closed items | Watch for |
| --- | --- | --- | --- |
| RFIs | Detail, with ball-in-court and due date | Archive with index | Responses stored as email replies outside the system |
| Submittals | Detail, with every revision and review stamp | Archive with index | Review comments embedded in PDF markups that do not survive re-export |
| Drawings and specifications | Current set in detail, with the revision history | Superseded sets archived, never deleted | Losing which revision was current on which date. That matters in every dispute |
| Change events and potential change orders | Detail, linked to the change orders in the financial migration | Archive | Change events that exist only in a PM's spreadsheet |
| Daily logs and field reports | Current job in detail if the new system holds them | Archive | Weather, manpower and delay notes. These are claims evidence |
| Photos | Current job in detail | Archive | Losing the capture date and location in the file metadata by re-saving or compressing |
| Meeting minutes | Archive; carry open action items forward by hand | Archive | Action items nobody re-creates |
| Inspections, punch lists, safety records | Open items in detail | Archive | Records a regulator or insurer may ask for years later |
| Lien waivers, insurance certificates, bonds | Current ones in detail, linked to vendors and commitments | Archive | Expiry dates. The new system must know when a certificate lapses |
| Warranties and O&M manuals | Archive, indexed by job, system and expiry | Archive | Warranty start dates. They are claimed years later |

## A neutral format for the logs

The five logs that carry most of a job's obligations (RFIs, submittals, change events, daily reports and punch lists)
have open schemas and CSV templates in
[construction-project-records](https://github.com/constructelligence-lab/construction-project-records). Mapping each
log into that format on the way out gives you one shape to check, whichever systems you are moving between. Its checker
finds the faults that damage a log in transit: duplicate and missing numbers, answers with no date, open items with
nobody holding the ball. Run it on the export from the old system and on the export from the new one, and the metrics
(open, overdue, by status) should agree.

## Archives that can be used

An archive is only useful if someone can find a document in it in five years' time without the old system.
For each closed job, or each record type you archive:

- export the records to a folder per job and record type, with files named by their number and revision
  (for example `RFI-047-r1.pdf`);
- write an index CSV per folder listing number, title, status, dates, who raised it and who answered it, and
  the file name of each attachment;
- export the old system's standard log reports (RFI log, submittal register, drawing register) as PDFs
  alongside, because they show the data the way the team saw it at the time;
- keep file metadata intact. Copy files, do not re-save them.

## Email and links

Two things are routinely forgotten:

- **Email.** Much of a job's real correspondence is in email, attached to nothing. Decide what is filed to the
  job before cutover. Moving systems does not move inboxes.
- **Links.** Documents, spreadsheets and emails that link into the old system will break when it is switched
  off. There is no general fix. Record in the archive index which system a record came from and its old
  identifier, so a broken link can at least be traced.

## Disputes and legal holds

If a job is in a dispute, or one is reasonably expected, **speak to counsel before moving, converting or
deleting anything connected to it.** Documents under a legal hold may need to be preserved in their original
form, with their metadata, and a migration can alter both. Construction contracts may also carry
confidentiality clauses or client requirements about where project documents are stored. Check them before
moving a client's documents into a new hosted system.

## Reconciling documents

Documents are reconciled by count rather than by value. For each project and record type:

| Check | Old system | New system or archive |
| --- | --- | --- |
| Records, by status (open, closed, void) | From the log report | From the new system or the archive index |
| Attachments | Count and total size | Count and total size |
| Highest number in the sequence | For example, RFI 112 | The same, so the next new RFI is 113 |
| Open items with a due date | Count and earliest due date | The same |

Any difference is a record left behind or duplicated. Chase it the same way as a financial difference: fix the
export, not the loaded result.

For the files themselves, take a manifest when they leave the old system and compare it with the archive or
upload folder after every copy:

```bash
python3 -m cdm manifest exports/documents --out out/documents-at-export.csv
python3 -m cdm manifest-compare out/documents-at-export.csv archive/documents
```

The comparison lists every file that is missing, added or changed in content (by SHA-256 hash), and every file that
moved folder. A file that is "the same PDF" but has a different hash has been re-saved. Find out by what, because
re-saving can strip signatures, markups and metadata.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
