# Mappings

A mapping file turns one old-system export into one neutral-model record file. Keep one mapping per export,
under version control, next to its crosswalks. The same file runs in every trial load and in the final load,
which is the point: a fix made in a mapping is never forgotten.

[`legacy-job-cost-detail.json`](legacy-job-cost-detail.json) is a complete worked example against the
synthetic [legacy export](../samples/legacy-export/).

## Format

```json
{
  "record": "cost_transactions",
  "skip_if": [{"column": "Job", "matches": "|Total.*"}],
  "fields": {
    "transaction_id": {"template": "{Batch}-{Line}"},
    "cost_code":      {"from": "Phase", "crosswalk": "path/to/cost-code-crosswalk.csv"},
    "cost_type":      {"from": "Cat", "upper": true, "map": {"L": "labor", "M": "material"}},
    "posted_date":    {"from": "Date", "date_format": "%m/%d/%Y"},
    "amount":         {"from": "Amount"},
    "source":         {"value": "ap"}
  }
}
```

| Key | Meaning |
| --- | --- |
| `record` | The neutral record this export becomes. See [`schema/fields.csv`](../schema/fields.csv) |
| `skip_if` | Rows to skip, such as subtotals, totals and blank lines. `matches` is a regular expression matched against the whole cell |
| `from` | The source column |
| `template` | Build a value from several columns, for example `{Batch}-{Line}` |
| `value` | A fixed value for every row |
| `upper` | Upper-case before mapping |
| `crosswalk` | A CSV with `old_code,new_code` columns, relative to the mapping file. An old code not in it stops the row |
| `map` | An inline lookup. A value not in it stops the row |
| `date_format` | The source date format. Required for anything that is not `YYYY-MM-DD`. There is no guessing between day-first and month-first |
| `encoding`, `delimiter` | Top-level options for the input file. The defaults are UTF-8 with or without a byte order mark, and comma |

Amounts are parsed strictly: `$1,234.50`, `(1,234.50)`, `1,234.50-` and `-1234.5` are all understood, and a value
with more than two decimal places is refused rather than rounded.

## Contributing a mapping

Mappings for common report exports are welcome. Build them from your own exports and public documentation, use
synthetic example values, and never include customer-only vendor documentation. See
[export routes](../sources/export-routes.md#material-this-repository-will-not-publish).
