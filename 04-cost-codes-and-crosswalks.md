# Cost codes and crosswalks

The cost code list is the spine of every cost report the company produces. Get it wrong in a migration and
every budget-to-actual, every cost-to-complete and every job comparison after cutover is wrong with it. Most
of the time nobody notices, because the totals still add up.

## Decide first: keep, clean or replace

| Choice | When it is right | Cost |
| --- | --- | --- |
| **Keep** the old list unchanged | It works, estimators and PMs know it, and the new system can hold it | Lowest. Historical comparisons still work |
| **Clean** it | The list has grown duplicates, dead codes and inconsistent cost types | Moderate. Every merge needs a crosswalk row |
| **Replace** it | The old list does not reflect how you estimate or build any more | Highest. Old and new jobs will not compare like-for-like without the crosswalk |

A migration is a tempting moment to replace the list, because everything is being touched anyway. It is also
the worst moment, because the same people are busy with everything else. If you do replace it, do it
because the estimating and cost reporting need it, not because the new system's default list looks tidier.

If you are starting a list from scratch, the
[starter cost code taxonomy in construction-data](https://github.com/constructelligence-lab/construction-data)
is a free, independently numbered starting point mapped to CSI division titles.

## The rules

1. **Freeze the list** four to six weeks before cutover. No new codes after that date without the data owner's
   sign-off, and each one goes straight into the crosswalk.
2. **Never rename a code that carries postings.** Create the new code, map the old one to it in the crosswalk,
   and make the old code inactive. Renaming in place rewrites history without a record of it.
3. **Many-to-one is fine.** Merging `0902.00` and `0902.10` into one board code is a normal clean-up, as long as
   the crosswalk says so and gives a reason.
4. **One-to-many is not fine for history.** If one old code has to split into two new ones, posted cost cannot
   be split without a rule. Either carry the history under the old code (kept inactive), or post a documented
   allocation journal at cutover with the split percentages and the controller's approval. Never split by hand
   in the loaded data.
5. **Cost type is part of the key.** A budget line is a job, a code *and* a cost type. Map the cost types
   explicitly, and check that every cost posted has a budget line to land on. The reconciliation's `R04`
   check lists the ones that do not.
6. **Every old code must appear in the crosswalk**, even the ones that map to themselves. The mapping tool
   stops on any old code it cannot find rather than passing it through. That is deliberate: a silently
   passed-through code is how `03-310` ends up living alongside `03-100` for the next five years.

## The crosswalk file

A crosswalk is a two-column table with a reason column. Keep it with the mappings, under version control, and
treat changes to it like changes to the mappings.

```text
old_code,new_code,note
0106.00,01-060,
0902.00,09-020,merged: old codes 0902.00 and 0902.10 were the same scope
0902.10,09-020,merged: old codes 0902.00 and 0902.10 were the same scope
```

Start from [`templates/cost-code-crosswalk.csv`](templates/cost-code-crosswalk.csv). The worked example used
by the samples is [`samples/legacy-export/cost-code-crosswalk.csv`](samples/legacy-export/cost-code-crosswalk.csv).

## Standards and licensing

CSI MasterFormat section numbers and titles are licensed by CSI. It is common, and fine, to roll your codes up
to the **division** level (two-digit division numbers and titles) for reporting. Do not copy the full
MasterFormat numbering into a public file, a shared template or a product without a licence. The neutral
schema's `csi_division` field is there for exactly this: a two-digit roll-up, nothing more.

## Checking the crosswalk before the load

Run the mapping against the full export, not a sample. Every old code that has ever carried a posting will
turn up in the unmapped list if it is missing:

```bash
python3 -m cdm map mappings/legacy-job-cost-detail.json samples/legacy-export/job-cost-detail.csv --out out/cost_transactions.csv
```

```text
cost_transactions: 58 rows read, 58 written, 0 rejected, 11 skipped by skip_if
  amount: 1,213,290.57 parsed, 1,213,290.57 written
  retainage_withheld: 88,151.31 parsed, 88,151.31 written
```

The `parsed` and `written` totals are your first tie-out. The `amount` total must equal the old system's job
cost report for the same job and date before anything is loaded.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
