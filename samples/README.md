# Samples

Everything in this folder is **synthetic**. The jobs, companies, people, amounts and dates were invented by
[`scripts/make_samples.py`](../scripts/make_samples.py), which is deterministic, so the files only change when
the script does. Names such as "Sample Drywall Co" are placeholders and do not refer to any real business.

| Folder | What it is |
| --- | --- |
| [`clean/`](clean/) | A complete migration of three jobs in the neutral model, with control totals. It ties out to the cent |
| [`broken/`](broken/) | The same migration with nine realistic faults planted in it |
| [`legacy-export/`](legacy-export/) | One job's cost detail as a typical old-system report export, plus the cost code crosswalk |
| [`schedules/`](schedules/) | One fit-out schedule as P6 XER, as Microsoft Project XML, and as a conversion that lost logic |

## The jobs

| Job | Status | Why it is here |
| --- | --- | --- |
| J-1104 Riverside Clinic Fit-out | open | A lump sum job mid-way through, with pending and rejected change orders |
| J-1107 Harbor Street Retail Shell | open | A GMP job with a deductive change order |
| J-1098 Oak Avenue Office Refresh | warranty | Finished, but retainage is still held by the owner. This is the job migrations leave behind |

## The planted faults

Run `python3 -m cdm reconcile samples/broken` to see each one caught.

| # | Fault | Caught by |
| --- | --- | --- |
| 1 | A payroll line exported twice under a new reference | `T01` cost to date on J-1104. There is no duplicate key, so only the tie-out finds it |
| 2 | A cost code renamed in the new system without updating the crosswalk | `R03` |
| 3 | A pending owner change order mapped to approved | `T01` contract value on J-1107 |
| 4 | A full tax ID pasted into the vendor file | `R09` |
| 5 | A retainage release keyed at three times the amount released | `R06` and `T01` retainage receivable on J-1098 |
| 6 | A September invoice included in the August cutover load | `R05` and `T01` cost to date on J-1107 |
| 7 | A commitment change order attached to the right number on the wrong job | `R10` |
| 8 | A credit note dropped by a filter that kept positive amounts only | `T01` cost to date and retainage payable on J-1107 |
| 9 | The same purchase order loaded twice | `R01` and `T01` committed cost on J-1107 |

## Try the mapping

```bash
python3 -m cdm map mappings/legacy-job-cost-detail.json samples/legacy-export/job-cost-detail.csv --out out/cost_transactions.csv
```

The export has subtotal lines, dollar signs, thousands separators, negative amounts in parentheses,
month-first dates, one-letter cost categories and the old phase codes. The mapping turns it back into exactly
the J-1104 rows in `clean/cost_transactions.csv`, and the parsed total equals the job's control total.

## Try the schedules

```bash
python3 -m cdm schedule-compare samples/schedules/fitout.xer samples/schedules/fitout.xml --match name
python3 -m cdm schedule-compare samples/schedules/fitout.xer samples/schedules/fitout-lossy-conversion.xml --match name
```

The first passes. The second finds the relationship that went missing and the lag that shrank from 120 hours
to 16.
