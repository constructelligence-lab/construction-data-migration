# Export routes

How data gets out of a system decides how much of a migration is mapping and how much is clean-up. In order of
preference:

1. **A documented public API.** Structured, complete and repeatable. Usually the best route for project
   management platforms.
2. **A documented export format** (CSV, XER, Project XML, IFC). Repeatable, and the format is public.
3. **Standard reports exported to CSV.** Workable and very common for accounting systems. Expect subtotal
   lines, formatted amounts and month-first dates. The [mapping tool](../mappings/README.md) handles all three.
4. **A direct database extract.** Complete but fragile. Table structures are often undocumented, change between
   versions, and may be covered by licence terms. Only with the vendor's agreement.
5. **Copy and paste.** For small spreadsheets only, and never as the final load.

## Public documentation

Only public, official documentation is linked here. Product names are trademarks of their owners and are used
only to identify the formats and interfaces. Nothing here implies any partnership with, or endorsement by, any
of them.

| Area | Format or interface | Official documentation |
| --- | --- | --- |
| Schedules | Microsoft Project XML (MSPDI) | [Microsoft Learn: Project XML Data Interchange](https://learn.microsoft.com/en-us/office-project/xml-data-interchange/introduction-to-project-xml-data) |
| Schedules | Primavera P6 XER and P6 XML | [Oracle Primavera P6 documentation](https://docs.oracle.com/en/industries/construction-engineering/primavera-p6-project/) |
| Project management | Procore REST API | [Procore developer documentation](https://developers.procore.com) |
| Project management and documents | Autodesk Platform Services, including Autodesk Construction Cloud APIs | [Autodesk Platform Services](https://aps.autodesk.com/) |
| Small business accounting | QuickBooks Online Accounting API | [Intuit developer documentation](https://developer.intuit.com) |
| Building models | IFC (ISO 16739) | [buildingSMART: IFC](https://technical.buildingsmart.org/standards/ifc/) |
| Facility handover | COBie | [WBDG: COBie](https://www.wbdg.org/bim/cobie) |

## Material this repository will not publish

Many construction accounting and ERP systems document their database tables, import formats and report layouts
**only for licensed customers**, often under terms that restrict redistribution. If you have that material, use
it inside your own migration. Do not post it in an issue or a pull request here. We will remove it, and we do not
build mappings from it.

Contributions of mappings are welcome when they are built from **your own exports**, the column headers of a
standard report as it appears on screen, and public documentation, using **synthetic example values**.

---

*Part of [Construction data migration](../README.md) · Maintained by [Constructelligence](https://constructelligence.co) ·
Planning a migration? [Ask us on GitHub](https://github.com/constructelligence-lab/construction-data-migration/issues/new/choose).*
