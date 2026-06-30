"""Citation formatting and bibliography generation."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable


class CitationManager:
    def format_all(self, sources: Iterable[dict]) -> dict:
        unique = list({item["url"]: item for item in sources}.values())
        year = datetime.now().year
        ieee, apa, mla, bibtex = [], [], [], []
        for index, source in enumerate(unique, start=1):
            title = source.get("title") or source.get("domain") or "Online source"
            domain = source.get("domain") or "Web"
            url = source["url"]
            ieee.append(f'[{index}] {domain}, "{title}." [Online]. Available: {url}.')
            apa.append(f"{domain}. ({year}). {title}. {url}")
            mla.append(f'“{title}.” {domain}, {year}, {url}.')
            key = "".join(char for char in domain if char.isalnum()) + str(index)
            bibtex.append(
                "@misc{"
                f"{key},\n"
                f"  title = {{{title}}},\n"
                f"  author = {{{domain}}},\n"
                f"  year = {{{year}}},\n"
                f"  url = {{{url}}}\n"
                "}"
            )
        return {"ieee": ieee, "apa": apa, "mla": mla, "bibtex": bibtex}

    def bibliography_markdown(self, sources: Iterable[dict], style: str = "ieee") -> str:
        citations = self.format_all(sources)
        selected = citations.get(style.lower(), citations["ieee"])
        return "\n".join(f"{item}" for item in selected)
