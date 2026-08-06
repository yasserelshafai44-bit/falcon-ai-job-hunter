# Sprint 9 Repair Merge

Copy this package into the repository and overwrite the existing zero-byte files.

Run:

```powershell
pytest tests/test_background_core.py tests/test_task_queue.py tests/test_document_worker.py tests/test_email_worker.py tests/test_worker_manager.py tests/test_job_registry.py tests/test_dispatcher.py tests/test_scheduler.py
```

Then verify file sizes:

```powershell
Get-ChildItem backend\app\workers\*.py,backend\app\jobs\*.py,backend\app\services\scheduler_service.py,tests\test_*worker*.py,tests\test_scheduler.py,tests\test_dispatcher.py,tests\test_job_registry.py |
Select-Object Length,Name
```

Create a normal repair commit:

```powershell
git add backend/app/workers backend/app/jobs backend/app/services/scheduler_service.py tests/test_document_worker.py tests/test_email_worker.py tests/test_worker_manager.py tests/test_job_registry.py tests/test_dispatcher.py tests/test_scheduler.py README_SPRINT9_REPAIR.md SPRINT9_REPAIR_MERGE.md
git commit -m "Repair Sprint 9 worker and scheduler implementations"
git push
```

Do not amend or force-push again.
