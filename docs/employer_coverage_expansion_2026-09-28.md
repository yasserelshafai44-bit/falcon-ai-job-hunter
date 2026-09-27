# Employer coverage expansion — 2026-09-28

## Verified production baseline

Captured 2026-09-27T22:05:01.491731+00:00: **108 active genuine vacancies, 108 distinct database IDs**, across five employer sources. No demo or search-engine vacancies are included.

Relevant means STRONG APPLY / APPLY / CONSIDER (career score at least 60), evaluated against the existing private analysed-CV snapshot. Location does not reduce career fit. The private CV is never committed.

| Provider key | Employer | Source type | Baseline status | Active genuine | Relevant | Official source | Last successful refresh (UTC) |
|---|---|---|---|---:|---:|---|---|
| deliveroo | Deliveroo | Employer WordPress REST | LIVE | 3 | 1 | https://careers.deliveroo.co.uk/ | 2026-09-27T21:59:34.636770Z |
| kfc_uk | KFC UK | Employer public JSON | LIVE | 44 | 1 | https://careers.kfc.co.uk/ | 2026-09-27T21:59:35.214826Z |
| raising_canes_uk | Raising Cane's UK | SmartRecruiters Posting API | LIVE | 11 | 2 | https://jobs.raisingcanes.co.uk/ | 2026-09-27T21:59:35.813303Z |
| wsh_group_uk | WSH Group UK | SmartRecruiters Posting API | LIVE | 14 | 2 | https://careers.wshgroup.co.uk/ | 2026-09-27T21:59:36.209155Z |
| greene_king_uk | Greene King | SmartRecruiters Posting API | LIVE | 36 | 0 | https://jobs.greeneking.co.uk/ | 2026-09-27T21:59:36.715885Z |
| — | Burger King UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://careers.burgerking.co.uk/ | None |
| — | Wingstop UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://harri.com/Wingstopuk | None |
| — | Pret A Manger | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://www.pret.co.uk/en-GB/pret-jobs | None |
| — | Costa Coffee | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://costacareers.co.uk/ | None |
| — | Starbucks UK | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://careers.starbucks.com/ | None |
| — | McDonald's UK | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://people.mcdonalds.co.uk/job-search | None |
| — | Greggs | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://careerssearch.greggs.co.uk/ | None |
| — | Domino's UK & Ireland | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://jobs.dominos.co.uk/ | None |
| — | Pizza Hut UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://www.careersatpizzahut.co.uk/ | None |
| — | Taco Bell UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://jobs.tacobell.com/jobs/country/United-Kingdom/ | None |
| — | Popeyes UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://careers.popeyesuk.com/vacancies | None |
| — | Five Guys UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://jobs.fiveguys.co.uk/jobs/home/ | None |
| — | Subway UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://www.subway.com/en-gb/careers | None |
| — | Just Eat Takeaway.com | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://careers.justeattakeaway.com/global/en/search-results | None |
| — | Uber / Uber Eats | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://www.uber.com/us/en/careers/list/ | None |
| — | Nando's UK | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://nandos.careers/ | None |
| — | Wendy's UK | Careers UI; no enabled adapter | UNAVAILABLE | Not searched | Not searched | https://wendys-careers.co.uk/job-search/ | None |
| — | Caffè Nero | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://careers.caffenero.com/ | None |
| — | GAIL's | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://jobs.gailsbread.co.uk/en-gb/ | None |
| — | Compass Group UK & Ireland | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://jobs.compass-group.co.uk/ | None |
| — | SSP UK & Ireland | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://careers.foodtravelexperts.com/ | None |
| — | Mitchells & Butlers | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://www.mbcareersandjobs.com/ | None |
| — | Whitbread | Careers UI; no enabled adapter | AUTHORIZATION_REQUIRED | Not searched | Not searched | https://www.whitbreadcareers.com/search-and-apply/ | None |
| — | Wagamama | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://jobs.wagamama.uk/search | None |
| — | Amazon Operations | Careers UI; no enabled adapter | MANUAL_ONLY | Not searched | Not searched | https://jobs.amazon.co.uk/en/ | None |

## Assessment of every requested employer and added sources

LIVE means a complete public source was retrieved successfully, not merely that a careers page exists. AUTHORIZATION_REQUIRED means no appropriate public integration was verified and permission/integration access is needed for the proposed route; it is not a claim that every possible automated interface is forbidden. MANUAL_ONLY means the public UI remains usable but Falcon has no verified automated source. UNAVAILABLE records the actual retrieval failure. Counts for inaccessible employers are unknown, never zero.

| Employer | Provider | Status | Official source | Evidence / limitation |
|---|---|---|---|---|
| Deliveroo | deliveroo | LIVE | https://careers.deliveroo.co.uk/ | Verified public employer careers endpoint |
| KFC UK | kfc_uk | LIVE | https://careers.kfc.co.uk/ | Verified public employer careers endpoint |
| Raising Cane's UK | raising_canes_uk | LIVE | https://jobs.raisingcanes.co.uk/ | Verified SmartRecruiters public Posting API |
| WSH Group UK | wsh_group_uk | LIVE | https://careers.smartrecruiters.com/WSHGroup | Westbury Street Holdings public UK postings across catering/hospitality brands including BaxterStorey and Caterlink |
| Greene King | greene_king_uk | LIVE | https://jobs.greeneking.co.uk/ | Documented SmartRecruiters public UK Posting API; all occupational families retained |
| Burger King UK | — | AUTHORIZATION_REQUIRED | https://careers.burgerking.co.uk/ | Harri source requires an authorised machine-access arrangement |
| Wingstop UK | — | AUTHORIZATION_REQUIRED | https://harri.com/Wingstopuk | Harri source requires an authorised machine-access arrangement |
| Pret A Manger | — | AUTHORIZATION_REQUIRED | https://www.pret.co.uk/en-GB/pret-jobs | No authorised public Cornerstone vacancy feed is verified |
| Costa Coffee | — | AUTHORIZATION_REQUIRED | https://costacareers.co.uk/ | Public WordPress vacancy feed exists, but published website terms prohibit reuse beyond personal print copies; permission is needed |
| Starbucks UK | — | MANUAL_ONLY | https://careers.starbucks.com/ | Session-oriented careers search has no verified public vacancy API |
| McDonald's UK | — | MANUAL_ONLY | https://people.mcdonalds.co.uk/job-search | No reliable authorised public vacancy API is verified |
| Greggs | — | MANUAL_ONLY | https://careerssearch.greggs.co.uk/ | Public Tribepad HTML board declares a ten-second crawl delay; no complete machine feed verified in this assessment |
| Domino's UK & Ireland | dominos_uk | LIVE | https://jobs.dominos.co.uk/ | Official corporate live-jobs.xml sitemap and JobPosting JSON-LD; excludes separately operated franchise boards |
| Pizza Hut UK | — | AUTHORIZATION_REQUIRED | https://www.careersatpizzahut.co.uk/ | Official WordPress REST discovery returns HTTP 401; no authorised public vacancy feed verified |
| Taco Bell UK | — | AUTHORIZATION_REQUIRED | https://jobs.tacobell.com/jobs/country/United-Kingdom/ | The public careers UI uses an undocumented vacancy endpoint |
| Popeyes UK | — | AUTHORIZATION_REQUIRED | https://careers.popeyesuk.com/vacancies | Official careers site uses Talos360; no documented public complete vacancy interface verified. An authorised integration is required. |
| Five Guys UK | — | UNAVAILABLE | https://jobs.fiveguys.co.uk/jobs/home/ | Official UK careers hostname could not be reached in this assessment; not a zero-vacancy result |
| Subway UK | — | AUTHORIZATION_REQUIRED | https://www.subway.com/en-gb/careers | Dayforce and franchise sources require separate authorised access |
| Just Eat Takeaway.com | — | AUTHORIZATION_REQUIRED | https://careers.justeattakeaway.com/global/en/search-results | Official Phenom/Workday careers UI; no authorised public tenant feed verified |
| Uber / Uber Eats | — | UNAVAILABLE | https://www.uber.com/us/en/careers/list/ | Official careers request returned HTTP 406; no challenge bypass or alternate private endpoint attempted |
| Nando's UK | — | AUTHORIZATION_REQUIRED | https://nandos.careers/ | Official vacancies use Workday; no authorised public feed is verified |
| Wendy's UK | — | MANUAL_ONLY | https://wendys-careers.co.uk/job-search/ | Official page is accessible; REST discovery exposes ordinary pages, not a verified vacancy collection |
| Caffè Nero | — | MANUAL_ONLY | https://careers.caffenero.com/ | Legacy careers host points to caffenero.com/uk/careers; no verified public vacancy feed |
| GAIL's | — | MANUAL_ONLY | https://jobs.gailsbread.co.uk/en-gb/ | Official inploi careers UI is accessible; no documented public vacancy feed verified |
| Compass Group UK & Ireland | — | MANUAL_ONLY | https://jobs.compass-group.co.uk/ | Official inploi careers UI is accessible; no documented public vacancy feed verified |
| SSP UK & Ireland | — | MANUAL_ONLY | https://careers.foodtravelexperts.com/ | SuccessFactors careers UI is public; no authorised public tenant feed verified; robots excludes services paths |
| Mitchells & Butlers | — | AUTHORIZATION_REQUIRED | https://www.mbcareersandjobs.com/ | Official Attrax site links Harri recruitment; no verified public tenant postings feed or authorised integration |
| Whitbread | — | AUTHORIZATION_REQUIRED | https://www.whitbreadcareers.com/search-and-apply/ | Official search identifies Dayforce; no authorised public feed is verified |
| Wagamama | — | MANUAL_ONLY | https://jobs.wagamama.uk/search | Official inploi search is accessible; no documented public vacancy feed verified |
| Amazon Operations | — | MANUAL_ONLY | https://jobs.amazon.co.uk/en/ | Official jobs are public, but no documented vacancy API is verified |
| Gopuff | gopuff_uk | LIVE | https://www.gopuff.com/go/careers | Documented public Lever published-postings API; current UK openings only; talent pools excluded |
| Deliverect | deliverect_uk | LIVE | https://www.deliverect.com/en/careers-home | Documented public Lever published-postings API; current UK openings only; talent pools excluded |

## What changed

The previous adapters applied candidate-role filtering during ingestion, and Greene King searched only selected management titles. That explained the small production catalogue. Those ingestion restrictions are removed: all supported UK occupational families are retained and then ranked. Complete snapshots reconcile removed IDs by marking sources inactive; rows, matches and applications are not deleted. Failed/partial snapshots cannot close jobs. Verified authoritative empty snapshots are distinguished from an unexplained zero.

New sources: Domino’s corporate/supply-chain board (not independent franchise boards), Gopuff UK and Deliverect UK. Lever talent-pool/general-interest notices are excluded because they are not current vacancies. Original employer posting URLs and provider identity are retained. UK location is verified independently of candidate preferences.

Discovery pagination now has a stable ID tie-breaker. Ranking is performed in bounded request batches after ingestion, avoiding the previous 500-job scoring ceiling and an unbounded browser request burst. SmartRecruiters always rereads the complete active list; only unchanged released posting details can be reused. No database migration or Render configuration change is required.

Two demonstrated false positives in the expanded real descriptions are addressed: KFC Head of Innovation is a specialist marketing/menu-innovation occupation, and platter/warehouse/shift team-leader positions are frontline roles. These narrow guards do not lower senior regional operations scores or mix location into career fit. Full public-description regression fixtures cover these and chef, assistant, engineering, sales, finance and HR roles.

## WSH Group UK

`wsh_group_uk` reads the public `WSHGroup` SmartRecruiters tenant. WSH means Westbury Street Holdings, the catering and hospitality group behind brands including BaxterStorey and Caterlink. It is a group recruitment board, not one restaurant chain. Brand/job identity remains in the original vacancy description/title and official posting URL. See [WSH](https://www.wshlimited.com/) and [BaxterStorey’s group statement](https://baxterstorey.com/ie/anti-slavery-and-human-trafficking-statement/).

## Other pre-existing adapters

`remoteok` is the pre-existing Remote OK aggregator adapter; it is outside the verified-employer group and is not refreshed or counted in this milestone. `local` supplies demo fixtures, excluded from genuine totals. `manual_official` accepts user-supplied official vacancy text, not an automatic feed. `linkedin`, `indeed` and `bayt` remain credential/integration placeholders, not LIVE employer coverage. No applications are submitted.

## Primary interface evidence

- [Lever public published-postings API](https://github.com/lever/postings-api): public published postings and pagination; employers verified through their official careers links. [Deliverect careers](https://www.deliverect.com/en/careers-home), [Gopuff careers](https://www.gopuff.com/go/careers).
- [SmartRecruiters Posting API](https://developers.smartrecruiters.com/docs/posting-api) and [posting update semantics](https://developers.smartrecruiters.com/docs/endpoints).
- [Domino’s official live-vacancy sitemap](https://jobs.dominos.co.uk/live-jobs.xml), advertised by its sitemap index; each posting contains employer-published JobPosting data. Robots permission and listing-count consistency checked.
- [Costa terms](https://costacareers.co.uk/terms/): public endpoint availability did not establish permission for reuse; source not enabled.

## Verification scope and preservation

Local automated suite: **266 passed, 0 failed**. Ruff, JavaScript syntax and git whitespace checks passed. One sandbox test run encountered six temporary-directory permission errors; rerun with the required filesystem access passed completely. Test-key/deprecation warnings remain pre-existing.

The authenticated production diagnostic account is available for smoke tests; the personal account is not impersonated. Global users/CVs/profiles/applications/reviews/live-v1 database counts cannot be read through that account. These counts must be reported as unavailable, not fabricated. No reset, DELETE, schema change or personal-profile update is performed. Existing local user changes are left outside this commit.

## Post-deployment results

Pending production refresh and authenticated verification; this section will be replaced with measured results.
