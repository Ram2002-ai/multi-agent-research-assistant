"""Deterministic source extraction and explainable credibility scoring."""

from __future__ import annotations

import re
from collections import Counter
from urllib.parse import urlparse


URL_PATTERN = re.compile(r"https?://[^\s\])}>\"']+", re.IGNORECASE)
HIGH_AUTHORITY = {
    "who.int",
    "un.org",
    "worldbank.org",
    "nature.com",
    "science.org",
    "ieee.org",
    "acm.org",
    "nih.gov",
    "cdc.gov",
    "nasa.gov",
    "arxiv.org",
    "oecd.org",
}
TRUSTED_NEWS = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "economist.com",
    "ft.com",
}


def _domain_score(domain: str) -> tuple[int, int]:
    if domain in HIGH_AUTHORITY or domain.endswith(".gov") or domain.endswith(".edu"):
        return 95, 94
    if domain in TRUSTED_NEWS:
        return 87, 86
    if domain.endswith(".org"):
        return 75, 74
    return 62, 60


def score_sources(text: str) -> list[dict]:
    clean_urls = [match.rstrip(".,;:") for match in URL_PATTERN.findall(text)]
    counts = Counter(clean_urls)
    sources: list[dict] = []
    for url, citation_count in counts.items():
        parsed = urlparse(url)
        domain = parsed.netloc.lower().removeprefix("www.")
        authority, domain_rating = _domain_score(domain)
        secure = 5 if parsed.scheme == "https" else 0
        recency = 70
        trust = min(100, round(authority * 0.75 + secure + min(citation_count * 3, 10)))
        credibility = round(authority * 0.4 + trust * 0.35 + recency * 0.25)
        label = (
            "Highly Trusted"
            if credibility >= 85
            else "Trusted"
            if credibility >= 72
            else "Moderate"
            if credibility >= 55
            else "Low Confidence"
        )
        title = parsed.path.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ")
        sources.append(
            {
                "url": url,
                "title": title.title() or domain,
                "domain": domain,
                "credibility_score": credibility,
                "trust_score": trust,
                "authority_score": authority,
                "recency_score": recency,
                "citation_count": citation_count,
                "domain_rating": domain_rating,
                "label": label,
            }
        )
    return sorted(sources, key=lambda item: item["credibility_score"], reverse=True)
