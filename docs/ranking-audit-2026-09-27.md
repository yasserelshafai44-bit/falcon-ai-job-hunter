# Production ranking audit

The read-only audit used the complete descriptions already stored in production
for Deliveroo Partner Operations Manager, KFC Area Coach, both Caterlink Operations
Manager vacancies, and Raising Cane's Area Leader. It used the existing local CV
analysis privately; no private CV text or contact details are included here or in
the regression fixtures. The production user's authenticated CV was not accessed.

The existing local analysis reproduced all reported 89-point ties. These were not
an explicit 89-point cap: the same coarse component totals repeatedly produced
85/95, rounded to 89. Generic operations titles received full role-family credit;
cross-market merchant support was treated as physical multi-site ownership; one
or two recognised responsibility phrases could earn full responsibility credit.
Caterlink's 20-year company history also incorrectly earned experience points.

The scorer now separates described responsibilities from company history and
benefits, distinguishes partner contact-centre work from restaurant ownership,
and requires stated remit for site scope, people leadership and P&L. Commercial
responsibility alone is not full P&L ownership. Quantified team/site scale is
compared only when stated by both vacancy and candidate. Missing facts remain
NOT STATED or UNKNOWN. Seniority comes from the role and evidenced remit, not the
seniority of the person it reports to. Generic operations/manager terms do not
earn responsibility coverage. Candidate career-track labels are not CV evidence.

Mandatory CRM and catering experience, licences and right-to-work requirements
are checked against CV or confirmed profile evidence. Unsupported requirements
remain unconfirmed, not assertions that the candidate lacks them. Desirable SQL
does not become mandatory. Location remains a separate zero-weight assessment;
it never enters career score, career caps, or recommendations.

Private local-CV audit against the production snapshots:

| Vacancy | Before | After |
| --- | ---: | ---: |
| Deliveroo Partner Operations Manager | 89 | 64 |
| KFC Area Coach | 89 | 84 |
| Caterlink Operations Manager (both locations) | 89 | 69 |
| Raising Cane's Area Leader of Restaurants | 95 | 95 |

These are evidence-based ranking points, not probabilities. Other candidates or
newly confirmed profile facts can produce different results. Similar Caterlink
descriptions appropriately remain tied; no arbitrary tie-break bonus is added.

Tests use full, source-labelled vacancy snapshots and a synthetic candidate.
They cover relative ordering, site/team scale, company-age contamination, mandatory
versus optional requirements, generic keyword repetition, and location invariance.
Existing recommendation thresholds and location weights are unchanged. Two older
tests now assert the applicable recommendation band rather than assuming maximum
credit for unstated scale or an arbitrary 80-point boundary within Apply.

No employer adapters, ingestion, deployment settings, schema, or historical data
were changed. Existing matches are recalculated through the existing authenticated
ranking action; this change does not bulk-rewrite users' matches or review snapshots.
