# Occupational identity audit

The live catalogue's 108 unique vacancies were reviewed using their full saved
descriptions and the candidate's existing CV evidence. No vacancy ingestion,
deployment configuration, account, CV or schema changes were made.

Chef Manager (WSH, job 61) scored 85 / Apply because culinary titles were absent
from specialist classification. Generic leadership and P&L boilerplate then
classified this vacancy as operations leadership. Its description explicitly
calls for a Chef Manager delivering dishes in a kitchen with two colleagues;
restaurant portfolio leadership does not establish that occupation.

The corrected score is 24 / Reject, with culinary experience marked UNKNOWN
in candidate evidence. This does not invent an unstated culinary qualification.
The occupational mismatch takes precedence over transferable management points.
Explicit first-hand specialist CV evidence can satisfy the occupational check;
inferred labels and supervision of specialists cannot.

All 107 other career scores were unchanged. No additional Apply/Strong Apply
occupational false positives were found in this catalogue. Raising Cane's Area
Leader remains 95 / Strong Apply, KFC Area Coach 84 / Apply, Deliveroo Partner
Operations 64 / Consider, and both Caterlink Operations roles 69 / Consider.
Deliveroo's two fraud/risk specialist vacancies were already capped at 24.

Coverage: Deliveroo 3, KFC 44, Raising Cane's 11, WSH 14, Greene King 36.
Pagination produced overlapping records, so missing IDs were fetched individually
and the comparison required 108 unique IDs. Private CV evidence and credentials
remain outside version control. The regression fixture contains the public Chef
Manager vacancy; regression candidates are synthetic.

Location remains independently scored. No location contributes to the
occupational check or career score. Existing stored matches are recalculated by
the normal ranking action after deployment.
