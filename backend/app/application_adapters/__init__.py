from urllib.parse import urlsplit

from app.application_adapters.smartrecruiters import SmartRecruitersAdapter


def adapter_for(url):
    if urlsplit(url).hostname == "jobs.smartrecruiters.com":
        return SmartRecruitersAdapter()
    raise ValueError("No supported application adapter for this employer URL")


def local_adapter_for(url, playwright, directory, channel="chrome"):
    # Import lazily: Playwright runs on the Windows host, not in the Docker API.
    if urlsplit(url).hostname != "jobs.smartrecruiters.com":
        raise ValueError("No local browser adapter for this employer")
    from app.application_adapters.local_smartrecruiters import LocalSmartRecruiters

    return LocalSmartRecruiters(playwright, directory, channel)
