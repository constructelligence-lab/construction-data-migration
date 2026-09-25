# Working with vendors and implementers

Most migrations involve at least one outside party: the new system's vendor, an implementation partner, or a
consultant. They bring experience of the software. You bring the knowledge of your jobs. A migration goes
wrong when either side assumes the other has the part it does not.

## Who does what

| Work | Usually best done by | Why |
| --- | --- | --- |
| Configuring the new system | Vendor or implementer | They know its settings and their consequences |
| Loading data into it | Vendor or implementer | They know its import tools and their limits |
| Deciding scope and cutover date | You | Only you know which jobs, obligations and deadlines matter |
| Cost code crosswalk and field mappings | You, with their review | The mappings encode your business, and you will maintain them |
| Control totals and reconciliation | You | The proof has to come from someone independent of the load |
| Cleaning source data | You | It is your data, in your old system |
| Training | Both | They know the software; your people know how the company works |
| Sign-off | You | Controller, PM lead, data owner |

The one rule without exceptions: **the people who load the data must not be the only people who check it.**

## Questions to ask before you sign

Take these to the sales and implementation conversations. The full checklist is in
[`templates/vendor-and-implementer-questions.md`](templates/vendor-and-implementer-questions.md).

**About the migration**

- Which records will you load, and which are we expected to load or re-key? Is that written in the statement of work?
- How many trial loads are included? What does an additional one cost?
- What format do you need the data in? Can you load commitments with invoiced-to-date and retainage per commitment,
  or only balances?
- Can pay application numbering continue from our last application?
- Can we load pending and rejected change orders with their status?
- How do you prove the load is complete? Will you give us the loaded data back as an export for our own reconciliation?
- Who owns the mapping files at the end, and in what format do we receive them?

**About the data after cutover**

- Where is our data stored, and who can access it? Which subprocessors are involved?
- How do we get **all** of our data out, in a documented format, if we leave? Is there a cost?
- How long is data retained after the contract ends, and how is it deleted?
- Is there a documented API, and is access included in our plan?

**About the old system**

- Can the old system stay read-only for our retention period? What does that licence cost?
- If not, what archive export does the old vendor provide, and in what format?

## Statements of work

A statement of work for a migration should name, at least:

- the records in scope, with the treatment for each (detail, balance, archive), matching your scope decisions;
- the number of trial loads and what "complete" means for each one;
- that the vendor provides the loaded data back as an export after each load;
- that the mappings and any transformation scripts are delivered to you;
- who fixes a load error, how quickly, and at whose cost;
- the cutover window, and who is on call during it.

If "the migration" is a single line item with a fixed price and no definitions, ask what it includes before you sign.
That line is where most disputes about migrations start.

## When the implementer leaves

Before the implementation team rolls off, make sure you hold:

- every mapping, crosswalk and transformation script, in files you control;
- the issue log, with every resolution;
- the reconciliation sign-offs and control reports for every trial and the final load;
- the system configuration decisions and why they were made;
- named contacts for support after go-live.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
