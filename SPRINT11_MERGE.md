# Sprint 11 Merge

## Test

```powershell
$env:PYTHONPATH="$PWD\backend"
python -m pytest --noconftest tests/test_integration_registry.py tests/test_remotive_connector.py tests/test_email_notifier.py tests/test_integration_routes.py
```

The Remotive connector is tested with `httpx.MockTransport`, so tests do not require live internet access.
