# Handling migration data safely

A migration puts more of the company's sensitive data in one place, in plain files, than any other project it
will run: vendor tax IDs, bank details, payroll, pricing and client documents, in CSVs that are easy to copy,
email and forget about. Most migration data incidents are not attacks. They are an export left in a shared
folder, a spreadsheet attached to a support ticket, or a file pasted into a tool nobody vetted.

This chapter is practical guidance, not legal advice. Your obligations depend on your jurisdiction, your
contracts and the people whose data you hold. Take the specifics to your counsel.

## What is sensitive

| Data | Why it matters |
| --- | --- |
| Tax IDs (EIN, SSN or local equivalents) | Identity fraud; for sole-trader subcontractors the tax ID can be a personal identifier |
| Bank and payment details | Payment fraud: changed-bank-details fraud targets exactly this data |
| Payroll, employee and medical records | Regulated personal data; injury records carry extra obligations |
| Certified payroll | Personal data, plus compliance records you must be able to produce |
| Bid pricing, unit rates and margins | Commercially sensitive; a competitor would pay for it |
| Client documents and drawings | Often under contractual confidentiality, sometimes security-sensitive |
| Contracts and claims files | Privileged or confidential material may be mixed in |

## The rules

1. **Do not export what you do not need.** The neutral model carries the last four digits of a tax ID and no
   bank details at all. Enter full tax IDs and bank details in the new system through its own secure setup,
   verified against source documents, not through a migration file.
2. **One staging area.** Encrypted, access-controlled storage, limited to the people doing the migration.
   Not email, not personal drives, not a USB stick, not the team chat.
3. **Least privilege in the new system during the load.** A migration account needs write access for the
   load. Remove that access afterwards.
4. **No sensitive exports in consumer AI tools.** AI tools can help draft mappings and crosswalks from column
   headers and code lists. Do not paste real exports with personal, pricing or client data into a tool whose
   terms allow it to keep or train on what you give it. Use a business tier with contractual data protection,
   or keep the data out.
5. **Know what the new vendor does with your data.** Where it is stored, who can access it, which
   subprocessors are involved, how it is backed up, and how it is deleted if you leave. Get it in the contract.
6. **Check client contracts before moving their documents** to a new hosted system. Some restrict where
   project documents may be stored or who may host them.
7. **Delete staging copies after sign-off, and record that you did.** An export that outlives the migration
   is a liability with no remaining purpose.
8. **Watch for payment fraud around cutover.** A system change is exactly when a fraudulent "please update our
   bank details" email is most likely to be believed. Verify every bank detail change by phone, on a number
   you already hold.

## Asking for help in public

If you ask a question in a public forum, including an issue on this repository, **describe the shape of your
data, never the data itself**: column headers, record counts, the error message, a made-up row. Never post
real names, amounts, tax IDs, client names or job details. The
[issue template](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose)
reminds you of this, and anything posted in an issue is public.

---

*Part of [Construction data migration](README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
