"""Job-posting URL ingestion for known career sites and generic pages."""
from __future__ import annotations

import json
import re
from html import unescape
from typing import Any, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .cache import get_cached_job, set_cached_job
from packages.job_intelligence.extractor import analyze_job_description, keyword_names

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}
_TIMEOUT_SECONDS = 6
_MIN_DESCRIPTION_CHARS = 300
_MAX_DESCRIPTION_CHARS = 20000
_JOB_CACHE: Dict[str, Dict[str, Any]] = {}


def import_job_posting(
    url: str,
    cache_path: str | None = None,
    database_url: str | None = None,
    cache_ttl_hours: int = 168,
    timeout_seconds: int | None = None,
) -> Dict[str, Any]:
    normalized_url = _normalize_url(url)
    if normalized_url in _JOB_CACHE:
        return _JOB_CACHE[normalized_url]
    cached = get_cached_job(normalized_url, cache_path=cache_path, database_url=database_url)
    if cached is not None:
        _JOB_CACHE[normalized_url] = cached
        return cached

    source = detect_source(normalized_url)
    html = _fetch_html(normalized_url, timeout_seconds=timeout_seconds)
    soup = BeautifulSoup(html, "html.parser")

    structured = _extract_from_json_ld(soup)
    extracted = _extract_from_source(source, soup, normalized_url)
    merged = {
        "source": source,
        "title": extracted.get("title") or structured.get("title") or "",
        "company": structured.get("company") or extracted.get("company") or "",
        "location": extracted.get("location") or structured.get("location") or "",
        "description": extracted.get("description") or structured.get("description") or "",
    }

    description = _sanitize_description(merged.get("description", ""))
    meta_description = _meta_description(soup)
    if len(description) < _MIN_DESCRIPTION_CHARS:
        description = _sanitize_description("\n\n".join(part for part in [description, meta_description] if part))
    if len(description) < _MIN_DESCRIPTION_CHARS:
        description = _sanitize_description(_extract_generic_text(soup))

    if len(description) < _MIN_DESCRIPTION_CHARS:
        raise ValueError("Could not extract a full job description from this URL. Paste the JD manually.")

    description = description[:_MAX_DESCRIPTION_CHARS]
    intelligence = analyze_job_description(description)
    cleaned_description = intelligence.get("cleaned_text", "") or description

    title = _normalize_title(merged.get("title") or intelligence.get("title") or "Imported Job")
    company = merged.get("company") or _fallback_company(source, normalized_url)

    result = {
        "url": normalized_url,
        "source": source,
        "title": title,
        "company": company,
        "location": merged.get("location", ""),
        "description": cleaned_description,
        "skills": keyword_names(intelligence.get("skills", [])),
        "raw_json": {
            "structured": structured,
            "extracted": extracted,
            "source": source,
        },
    }
    set_cached_job(
        normalized_url,
        result,
        cache_path=cache_path,
        database_url=database_url,
        ttl_hours=cache_ttl_hours,
    )
    _JOB_CACHE[normalized_url] = result
    return result


def detect_source(url: str) -> str:
    lowered = url.lower()
    if "amazon.jobs" in lowered:
        return "amazon"
    if "linkedin.com/jobs" in lowered:
        return "linkedin"
    if "boards.greenhouse.io" in lowered or "job-boards.greenhouse.io" in lowered:
        return "greenhouse"
    if "jobs.lever.co" in lowered:
        return "lever"
    if "myworkdayjobs.com" in lowered or "workday.com" in lowered:
        return "workday"
    return "generic"


def _normalize_url(url: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise ValueError("Job URL is required.")
    if not normalized.startswith(("http://", "https://")):
        normalized = f"https://{normalized}"
    return normalized


def _fetch_html(url: str, timeout_seconds: int | None = None) -> str:
    response = requests.get(url, headers=_REQUEST_HEADERS, timeout=timeout_seconds or _TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text


def _extract_from_json_ld(soup: BeautifulSoup) -> Dict[str, str]:
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw_text = script.string or script.get_text(strip=True)
        if not raw_text:
            continue
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        for item in _iter_json_ld_entries(payload):
            item_type = str(item.get("@type", "")).lower()
            if "jobposting" not in item_type and not item.get("description"):
                continue
            company = item.get("hiringOrganization", {})
            location = item.get("jobLocation", {})
            address = location.get("address", {}) if isinstance(location, dict) else {}
            return {
                "title": _sanitize_text(item.get("title") or item.get("name") or ""),
                "company": _sanitize_text(company.get("name") if isinstance(company, dict) else ""),
                "location": _sanitize_text(" ".join(filter(None, [
                    address.get("addressLocality", ""),
                    address.get("addressRegion", ""),
                ]))),
                "description": _sanitize_description(item.get("description") or ""),
            }
    return {}


def _iter_json_ld_entries(payload: Any):
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
        return
    if isinstance(payload, dict):
        if "@graph" in payload and isinstance(payload["@graph"], list):
            for item in payload["@graph"]:
                if isinstance(item, dict):
                    yield item
            return
        yield payload


def _extract_from_source(source: str, soup: BeautifulSoup, url: str) -> Dict[str, str]:
    if source == "amazon":
        return _extract_amazon(soup)
    if source == "greenhouse":
        return _extract_greenhouse(soup)
    if source == "lever":
        return _extract_lever(soup)
    if source == "linkedin":
        return _extract_linkedin(soup)
    if source == "workday":
        return _extract_workday(soup)
    return _extract_generic(soup, url)


def _extract_amazon(soup: BeautifulSoup) -> Dict[str, str]:
    title = _first_text(soup, ["h1", ".job-detail-title"])
    company = "Amazon"
    location = _first_text(soup, [".location-and-id", ".job-detail-location"])
    description = _first_block_text(
        soup,
        ["#job-detail-body", ".job-detail-description", ".section"],
    )
    return {"title": title, "company": company, "location": location, "description": description}


def _extract_greenhouse(soup: BeautifulSoup) -> Dict[str, str]:
    return {
        "title": _first_text(soup, ["h1", ".app-title"]),
        "company": _first_text(soup, [".company-name", ".job-board-header h1"]),
        "location": _first_text(soup, [".location", ".location-name"]),
        "description": _first_block_text(soup, ["#content", ".content", ".job-post"]),
    }


def _extract_lever(soup: BeautifulSoup) -> Dict[str, str]:
    return {
        "title": _first_text(soup, ["h2", "h1"]),
        "company": _first_text(soup, [".main-header-logo a", ".posting-categories h5"]),
        "location": _first_text(soup, [".location", ".posting-categories .sort-by-location"]),
        "description": _first_block_text(soup, [".posting-page", ".posting", "#content"]),
    }


def _extract_linkedin(soup: BeautifulSoup) -> Dict[str, str]:
    return {
        "title": _first_text(soup, ["h1", ".top-card-layout__title"]),
        "company": _first_text(soup, [".topcard__org-name-link", ".topcard__flavor"]),
        "location": _first_text(soup, [".topcard__flavor--bullet", ".job-details-jobs-unified-top-card__primary-description"]),
        "description": _first_block_text(soup, [".show-more-less-html__markup", ".description__text", "main"])
        or _meta_description(soup),
    }


def _extract_workday(soup: BeautifulSoup) -> Dict[str, str]:
    return {
        "title": _first_text(soup, ["h1", "[data-automation-id='jobPostingHeader']"]),
        "company": _first_text(soup, ["[data-automation-id='company']"]),
        "location": _first_text(soup, ["[data-automation-id='locations']"]),
        "description": _first_block_text(
            soup,
            ["[data-automation-id='jobPostingDescription']", "[data-automation-id='jobDescription']", "main"],
        )
        or _meta_description(soup),
    }


def _extract_generic(soup: BeautifulSoup, url: str) -> Dict[str, str]:
    return {
        "title": _first_text(soup, ["h1", "title"]),
        "company": _first_meta(soup, "og:site_name") or _fallback_company("generic", url),
        "location": _first_text(soup, [".location", "[data-location]", ".job-location"]),
        "description": _extract_generic_text(soup),
    }


def _extract_generic_text(soup: BeautifulSoup) -> str:
    selectors = [
        "main",
        "article",
        "[role='main']",
        ".job-description",
        ".description",
        "#content",
    ]
    return _first_block_text(soup, selectors)


def _first_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = _sanitize_text(node.get_text(" ", strip=True))
            if text:
                return text
    return ""


def _first_meta(soup: BeautifulSoup, property_name: str) -> str:
    node = soup.find("meta", {"property": property_name}) or soup.find("meta", {"name": property_name})
    if node and node.get("content"):
        return _sanitize_text(node["content"])
    return ""


def _meta_description(soup: BeautifulSoup) -> str:
    for meta_name in ("description", "og:description", "twitter:description"):
        content = _first_meta(soup, meta_name)
        if content:
            return _sanitize_description(content)
    return ""


def _first_block_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = _sanitize_description(node.get_text("\n", strip=True))
            if len(text) >= _MIN_DESCRIPTION_CHARS:
                return text
    paragraphs = [node.get_text(" ", strip=True) for node in soup.find_all(["p", "li"])]
    return _sanitize_description("\n".join(paragraphs))


def _sanitize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def _sanitize_description(value: str) -> str:
    text = BeautifulSoup(unescape(value or ""), "html.parser").get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_title(title: str) -> str:
    normalized = _sanitize_text(title)
    normalized = re.sub(r"\s*\((?:US|UK|EU|EMEA|APAC|NA|Remote|Hybrid|Onsite|[A-Z]{2,5})\)\s*$", "", normalized)
    normalized = re.sub(r"\s*[-|,]\s*20\d{2}\b\s*$", "", normalized)
    normalized = re.sub(r"\s+20\d{2}\b\s*$", "", normalized)
    normalized = re.sub(r"\s{2,}", " ", normalized).strip(" -|,")
    return normalized or "Imported Job"


def _fallback_company(source: str, url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    if source == "amazon":
        return "Amazon"
    if source == "linkedin":
        return "LinkedIn"
    if source == "greenhouse":
        return "Greenhouse Job Board"
    if source == "lever":
        return "Lever Job Board"
    if source == "workday":
        return "Workday Job Board"
    return host.split(".")[0].replace("-", " ").title()
