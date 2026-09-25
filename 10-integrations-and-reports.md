# Integrations and reports

The data is only half of what a system does. The other half is what it is connected to and what it produces:
the bank file, the payroll import, the time-capture app, the estimating hand-off, the lender's draw report,
the dashboard the owner looks at every Monday. Migrations routinely move the data correctly and then discover,
in the first week, that nothing arrives and nothing goes out.

## Inventory the connections

List every connection into and out of the old system, including the manual ones. A person who downloads a
report every Friday and emails it to a lender is an integration. Use
[`templates/integration-inventory.csv`](templates/integration-inventory.csv).

| Connection | Direction | What breaks if it is forgotten |
| --- | --- | --- |
| Bank feeds and positive pay files | Both | Payments rejected by the bank, or cheques not protected against fraud |
| Payroll import (hours by job and cost code) | In | Labour cost missing from every job until someone notices |
| Time capture and field apps | In | Crews' hours land nowhere, or on the old codes |
| Estimating to budget hand-off | In | New jobs start with no budget, or a budget in the old code structure |
| Subcontractor and supplier portals | Both | Invoices and compliance documents go to an inbox nobody watches |
| Owner and lender reporting | Out | A draw request or a monthly report is late, or in a new format nobody agreed |
| Document storage and project management | Both | Change events and commitments stop flowing between PM and accounting |
| Business intelligence and dashboards | Out | Reports show the old system's frozen numbers, or nothing |
| Single sign-on and user provisioning | In | People cannot log in on day one, or leavers keep access |
| Email-in addresses (for example, invoice capture) | In | Vendor invoices bounce, or arrive in the old system after it is read-only |

For each connection, decide: **rebuild**, **replace**, or **retire**, and name an owner. Test each rebuilt
connection in the test system during the trial loads, with real (non-production) files, not in cutover week.

## Codes flow through integrations

Every integration that carries a job number, cost code, vendor number or employee number must use the new
numbering on day one. The crosswalk from [chapter 5](05-cost-codes-and-crosswalks.md) applies to them too:

- the payroll provider's job and cost code tables;
- the field app's cost code picker;
- the estimating system's export template;
- any spreadsheet that builds an import file.

A payroll import that still posts to `0902.10` after cutover produces exactly the kind of difference the
reconciliation was supposed to have ruled out, one week too late.

## Rebuild the reports people actually use

Nobody reads every report. Everybody depends on a few. Before cutover, ask each role which reports they use,
how often, and for what decision, and list them in
[`templates/report-rebuild-list.csv`](templates/report-rebuild-list.csv).

For each report:

1. **Find the equivalent** in the new system, or build it.
2. **Run both** for the same job and period during the parallel run.
3. **Compare the figures**, not the layout. A report that looks different but agrees is fine. A report that looks
   the same but defines "cost to date" or "percent complete" differently is not.
4. **Get the user to sign it off.** The person who makes decisions from the report, not the person who built it.

The reports that most often define figures differently between systems:

| Report | The definition to check |
| --- | --- |
| WIP schedule | How percent complete, earned revenue and over/under billing are computed |
| Cost to complete / forecast | Whether committed but uninvoiced cost is included; how pending change orders are treated |
| Job profitability | Whether overhead, equipment and burden are included, and at what rates |
| Retainage | Whether released retainage awaiting payment is still counted as held |
| Aged payables | Whether retainage payable is aged with the invoice or separately |
| Commitment status | Whether pending commitment change orders are included in "revised value" |

## External reports with a fixed format

Some reports go to people outside the company in a format they expect: pay applications to owners, draw
reports to lenders, certified payroll to agencies, bonding company WIP to surety. Before cutover, produce each
one from the test system and compare it with the last one sent from the old system. If the format changes,
tell the recipient **before** the first new one arrives, not after it is rejected.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
