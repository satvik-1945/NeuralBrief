from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
from pydantic import BaseModel

logger = logging.getLogger(__name__)

PROMPT = """You are an expert AI news analyst specializing in summarizing beauty, wellness, and lifestyle content.

Your role is to create concise, informative digests for both articles and video transcripts. Help readers quickly understand the key points of each piece.

Guidelines:
- Create a compelling title (5-10 words) that captures the essence of the content
- Write a 2-3 sentence summary that highlights the main points and why they matter
- For videos: focus on the speaker's key takeaways, tips, or recommendations
- For articles: focus on actionable insights and what readers can take away
- Use clear, accessible language
- Avoid marketing fluff - focus on substance
- Keep each summary under 150 words"""


class DigestEntry(BaseModel):
    title: str
    summary: str


class DigestOutput(BaseModel):
    digests: List[DigestEntry]


class DigestAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.system_prompt = PROMPT

    def generate_digests_batch(
        self,
        articles: List[dict],
        max_content_chars: int = 4000,
    ) -> Optional[DigestOutput]:
        """
        Generate digests for all articles in a single API call.
        articles: List of {"id", "title", "content", "url", "section"}
        """
        if not articles:
            return DigestOutput(digests=[])

        items_text = ""
        for i, a in enumerate(articles, 1):
            content = (a.get("content") or "")[:max_content_chars]
            item_type = a.get("article_type", "article")
            items_text += f"\n--- Item {i} ({item_type}, id={a.get('id', i)}) ---\n"
            items_text += f"Title: {a.get('title', '')}\n"
            items_text += f"Content: {content}\n"

        user_prompt = f"""Create a digest for each of these items (articles and/or video transcripts). Return a JSON object with a key "digests" containing a list of objects, each with "title" and "summary".
The order of digests must match the order of items (Item 1 -> digests[0], Item 2 -> digests[1], etc.).

Items:{items_text}

Return only valid JSON. Example format: {{"digests": [{{"title": "...", "summary": "..."}}, ...]}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
            )
            content = response.choices[0].message.content.strip()

            # Parse JSON (handle markdown code blocks)
            if "```" in content:
                for part in content.split("```"):
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        content = part
                        break

            data = json.loads(content)
            digests = [
                DigestEntry(title=d["title"], summary=d["summary"])
                for d in data.get("digests", [])
            ]
            return DigestOutput(digests=digests)
        except Exception as e:
            logger.error("DigestAgent batch failed: %s", e)
            return None
