"""Local, visible Playwright adapter for the normal SmartRecruiters applicant UI.

No ATS credentials or private endpoint calls. The request policy allows the
observed temporary resume upload and normal security scripts, but denies all
application writes. The runner never clicks a final employer Submit control.
"""

import re
from urllib.parse import urlsplit


def allowed_browser_request(method, url):
    if method in {"GET", "HEAD", "OPTIONS"}:
        return True
    target = urlsplit(url)
    host, path = target.hostname, target.path
    if target.scheme != "https":
        return False
    if host == "jobs.smartrecruiters.com":
        return path.startswith("/cdn-cgi/") or (
            method == "POST"
            and bool(
                re.fullmatch(
                    r"/oneclick-ui/api/company/[a-f0-9]{24}/attachment/resume", path
                )
            )
        )
    return (host, path) in {
        ("api-js.datadome.co", "/js/"),
        ("rum.smartrecruiters.com", "/sink/"),
        ("privacyportal-uk.onetrust.com", "/request/v1/consentreceipts"),
    }


SUBMISSION_GUARD = """(() => {
  // A guard for this dry-run browser only. Never solves or hides security UI.
  document.addEventListener('click', event => {
    const button=event.composedPath().find(e=>e instanceof Element &&
      (e.matches('button,spl-button,[role=button],input[type=submit]')));
    const label=button &&
      (button.innerText||button.textContent||button.value||'').trim();
    const finalAction=/^(submit(?: application)?|send application|apply(?: now)?)$/i;
    if(label && finalAction.test(label)){
      event.preventDefault();event.stopImmediatePropagation();
    }
  },true);
  document.addEventListener('keydown',event=>{
    if(event.key==='Enter' && event.composedPath().some(e=>e instanceof Element &&
      e.matches('input:not([type=file])'))){event.preventDefault();}
  },true);
})()"""


class LocalSmartRecruiters:
    name = "smartrecruiters_local_browser"

    def __init__(self, playwright, directory, channel="chrome"):
        self.playwright = playwright
        self.directory = directory
        self.channel = channel
        self.browser = self.context = self.page = None
        self.blocked_requests = []
        self.upload_status = None
        self.work_saved = []
        self.education_saved = []
        self.notes = []
        self.questions_reached = False
        self.personal_fields = {}

    async def guard(self, route):
        request = route.request
        if allowed_browser_request(request.method, request.url):
            await route.continue_()
        else:
            self.blocked_requests.append(
                {
                    "method": request.method,
                    "host": urlsplit(request.url).hostname,
                    "path": urlsplit(request.url).path,
                }
            )
            await route.abort()

    async def capture_upload(self, response):
        if (
            re.fullmatch(
                r"/oneclick-ui/api/company/[a-f0-9]{24}/attachment/resume",
                urlsplit(response.url).path,
            )
            and response.request.method == "POST"
        ):
            self.upload_status = response.status

    async def open(self, url):
        raise ValueError(
            "SmartRecruiters browser automation is disabled. Use Assisted Apply."
        )

    async def security_blocker(self):
        """Detect a visible challenge; never interact with its controls."""
        if self.page.is_closed():
            return None
        for frame in self.page.frames:
            host = urlsplit(frame.url).hostname or ""
            if host.endswith("captcha-delivery.com"):
                return (
                    "SmartRecruiters requires human security verification in "
                    "the local browser. Complete it yourself, then resume."
                )
            notice = frame.get_by_text(
                re.compile(
                    r"^(Verification Required|Slide right to secure your access)$"
                )
            )
            if await notice.count() and await notice.first.is_visible():
                return (
                    "SmartRecruiters requires human security verification in "
                    "the local browser. Complete it yourself, then resume."
                )
        return None

    async def populate(self, profile, resume_path, cover_text):
        raise ValueError(
            "SmartRecruiters browser automation is disabled. Use Assisted Apply."
        )
