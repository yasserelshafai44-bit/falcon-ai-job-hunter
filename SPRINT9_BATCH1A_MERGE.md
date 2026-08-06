# Sprint 9 Batch 1A merge steps

This package is intentionally self-contained and requires no router or model edits.

## Run tests

```powershell
pytest tests/test_background_core.py tests/test_task_queue.py
```

## Check formatting

```powershell
ruff format backend/app/core/background.py backend/app/core/task_queue.py tests/test_background_core.py tests/test_task_queue.py
ruff check backend/app/core/background.py backend/app/core/task_queue.py tests/test_background_core.py tests/test_task_queue.py
```

## Important limitation

The queue stores tasks only in application memory.

- Tasks disappear when the process restarts.
- Multiple workers in separate processes do not share the same queue.
- Do not use it for horizontally scaled production deployment.

Later Sprint 9 batches will add workers, services, and scheduling.
