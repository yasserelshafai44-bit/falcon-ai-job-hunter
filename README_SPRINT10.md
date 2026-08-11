# Sprint 10 — Application Workflow & Approval Engine

Sprint 10 turns Falcon's matching and document-generation features into a controlled
application workflow.

## Added

- application workflow persistence
- human approval gate
- resume / cover-letter attachment validation
- workflow state transitions
- submitted timestamp and application URL tracking
- interview / rejection / offer outcomes
- authenticated REST endpoints
- migration and tests

## Deliberate non-goal

Sprint 10 does not automatically submit forms on third-party websites. It creates a
safe approval and tracking layer that browser automation can use later.
