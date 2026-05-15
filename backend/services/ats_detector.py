from urllib.parse import urlparse

ATS_URL_PATTERNS: dict[str, list[str]] = {
    "workday": ["myworkdayjobs.com", "myworkdaysite.com", "wd1.", "wd3.", "wd5."],
    "greenhouse": ["boards.greenhouse.io", "greenhouse.io"],
    "lever": ["jobs.lever.co", "lever.co"],
    "icims": ["icims.com", "careers."],
    "taleo": ["taleo.net", "tbe.taleo.net"],
    "smartrecruiters": ["smartrecruiters.com/jobs"],
    "breezyhr": ["breezy.hr"],
}


def detect_ats_from_url(url: str) -> str:
    lower = url.lower()
    for ats, patterns in ATS_URL_PATTERNS.items():
        if any(p in lower for p in patterns):
            return ats
    return "generic"


async def detect_ats_from_page(url: str, page_content: str) -> str:
    """Refine detection using page content if URL alone is ambiguous."""
    ats = detect_ats_from_url(url)
    if ats != "generic":
        return ats

    content_lower = page_content.lower()
    if "workday" in content_lower:
        return "workday"
    if "greenhouse" in content_lower:
        return "greenhouse"
    if "lever" in content_lower:
        return "lever"
    if "icims" in content_lower:
        return "icims"

    return "generic"
