from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

from app.profile import DEFAULT_PROFILE

MAX_CURATED = 20  # Slightly higher to allow mix of articles + videos


@dataclass
class CuratorItem:
    """Unified content item for curator (article or video)."""

    content_type: str  # "article" | "video"
    id: int
    title: str
    description: str | None
    section: str | None
    categories: str | None
    published_at: datetime
    source: str
    content_text: str | None  # article body or video transcript

    def searchable_text(self) -> str:
        return (
            f"{self.title} {self.description or ''} {self.section or ''} "
            f"{self.categories or ''} {self.content_text or ''}"
        ).lower()


@dataclass
class CuratorRules:
    """Rule-based scoring and filtering for curation."""

    interest_keywords: List[str]
    boost_keywords: List[str]
    exclude_keywords: List[str]
    min_matches: int = 1
    max_items: int = MAX_CURATED

    def score_item(self, item: CuratorItem) -> float:
        """Score 0-100 based on rules. 0 = exclude."""
        text = item.searchable_text()
        score = 0.0

        for kw in self.exclude_keywords:
            if kw.lower() in text:
                return 0.0

        for kw in self.interest_keywords:
            if kw.lower() in text:
                score += 10.0

        for kw in self.boost_keywords:
            if kw.lower() in text:
                score += 5.0

        if item.section:
            score += 2.0
        if item.categories:
            score += 1.0

        return score

    def is_relevant(self, item: CuratorItem) -> bool:
        text = item.searchable_text()
        matches = sum(1 for kw in self.interest_keywords if kw.lower() in text)
        if matches < self.min_matches:
            return False
        for kw in self.exclude_keywords:
            if kw.lower() in text:
                return False
        return True


DEFAULT_RULES = CuratorRules(
    interest_keywords=[
        "skin", "makeup", "hair", "wellness", "celebrities",
        "beauty", "skincare", "cosmetic", "nail", "fragrance",
        "lifestyle", "health", "body", "face", "eye",
        "acne", "moisturizer", "serum", "cleanser", "sunscreen",
        "lip", "blush", "foundation", "eyeliner", "mascara",
        "curly", "natural", "organic", "vegan", "sensitive",
        "anti-aging", "hydrat", "glow", "routine", "review",
    ],
    boost_keywords=[
        "best", "recommended", "editor", "expert", "how to",
        "guide", "tips", "trend", "2025", "2026",
    ],
    exclude_keywords=[
        "sponsored", "advertisement", "buy now", "click here",
        "male", "men's", "men grooming",
    ],
    min_matches=1,
    max_items=MAX_CURATED,
)


class CuratorAgent:
    """Rule-based curator agent. Supports both articles and videos."""

    def __init__(self, rules: CuratorRules | None = None):
        self.rules = rules or DEFAULT_RULES

    def curate(self, items: List[CuratorItem]) -> List[Tuple[str, int]]:
        """
        Select relevant content from the given list.
        Returns [(content_type, id), ...] in order of relevance.
        """
        if not items:
            return []

        profile_interests = [i.lower() for i in DEFAULT_PROFILE.interests]
        rules = CuratorRules(
            interest_keywords=profile_interests or self.rules.interest_keywords,
            boost_keywords=self.rules.boost_keywords,
            exclude_keywords=self.rules.exclude_keywords,
            min_matches=self.rules.min_matches,
            max_items=self.rules.max_items,
        )

        scored: List[Tuple[float, CuratorItem]] = []
        for item in items:
            if not rules.is_relevant(item):
                continue
            score = rules.score_item(item)
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: (-x[0], -x[1].published_at.timestamp()))
        return [(item.content_type, item.id) for _, item in scored[: rules.max_items]]


__all__ = ["CuratorAgent", "CuratorItem", "CuratorRules", "DEFAULT_RULES"]
