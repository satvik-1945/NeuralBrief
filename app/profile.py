from dataclasses import dataclass
from typing import List


@dataclass
class UserProfile:
    name: str
    interests: List[str]
    sources: List[str]


DEFAULT_PROFILE = UserProfile(
    name="Default User",
    interests=["skin", "makeup", "hair", "wellness", "celebrities"],
    sources=["allure", "youtube"],
)

