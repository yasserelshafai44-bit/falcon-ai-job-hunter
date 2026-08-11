# Sprint 12 Merge

## Test

```powershell
$env:PYTHONPATH="$PWD\backend"
python -m pytest --noconftest tests/test_job_hunt_orchestrator.py
```

## Integration note

Sprint 12 adds the orchestration service only. It deliberately avoids inventing a
new API-provider factory contract. A later route can call `prepare_application`
once the preferred text-generation provider is selected by the existing app
configuration.
