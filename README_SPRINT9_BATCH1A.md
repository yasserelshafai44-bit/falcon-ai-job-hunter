# Sprint 9 Batch 1A — Background Task Core

Adds:

- task lifecycle model
- deterministic retry policy
- progress tracking
- cancellation state
- concurrency-safe in-memory FIFO queue
- task lookup and requeue support
- focused unit tests

The queue is process-local. It is suitable for development and a single-process
deployment only. A shared broker such as Redis is required before horizontal scaling.
