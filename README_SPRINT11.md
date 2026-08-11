# Sprint 11 — External Integration Layer

Sprint 11 introduces a clean connector layer for external job sources and outbound notifications.

## Added

- connector interface and registry
- Remotive job-source connector
- normalized external-job contract
- integration API endpoints
- SMTP email notifier
- tests for registry, connector normalization, routes and notifier settings

## Deliberate non-goals

- No LinkedIn scraping or login automation.
- No CAPTCHA bypassing.
- No automatic form submission to third-party sites.

Falcon now has a provider abstraction that can support approved APIs and user-authorized integrations safely.
