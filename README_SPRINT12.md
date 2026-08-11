# Sprint 12 — End-to-End Job Hunt Orchestration

Sprint 12 connects Falcon's existing matching, document-generation, and
application-workflow layers into one controlled operation.

## Flow

1. calculate and persist the candidate/job match
2. create an application workflow
3. generate the tailored resume
4. optionally generate a cover letter
5. attach the documents to the workflow
6. move the workflow to `awaiting_approval`

## Safety boundary

The orchestrator intentionally stops at the human approval gate. It does not
automatically submit a third-party application.

## Why this sprint matters

Falcon already had the individual services. The missing piece was a cohesive,
testable orchestration layer that turns those isolated capabilities into one
usable application-preparation flow.
