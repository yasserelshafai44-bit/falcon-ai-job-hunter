# Sprint 8 Batch 2 — Audit Persistence and System Readiness

Adds:

- immutable audit-event model
- audit-event migration
- sanitized audit persistence service
- `/health`
- `/ready`
- database readiness check
- text-generation-provider readiness check
- tests

This batch deliberately does not recreate authentication because Falcon already
has authentication from Sprint 3.
