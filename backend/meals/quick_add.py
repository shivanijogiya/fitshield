"""
quick_add.py – AI-powered free-text meal parser using Groq.

The user sends a plain-text description like:
    "2 rotis, a bowl of dal makhani and one lassi"

One LLM call parses it into a list of structured meal dicts.
Each created meal carries source="ai".

Failure modes:
  - Groq API error     → raises QuickAddError (caller returns 503)
  - Unparseable output → raises QuickAddParseError (caller returns 422)
"""

from __future__ import annotations

import json
import os
import re

from groq import Groq

# ---------------------------------------------------------------------------
# Prompt — stored as a module-level constant per assessment requirement.
# Instructs the model to return ONLY raw JSON, no markdown, no preamble.
# Schema is defined inline. Target: under 200 output tokens.
# ---------------------------------------------------------------------------

QUICK_ADD_PROMPT = """You are a nutrition data extractor. The user will describe what they ate in plain text.

Extract each food item and return ONLY a valid JSON array. No markdown, no explanation, no backticks, no thinking.

Each object in the array must have exactly these fields:
- "name": string (food name, max 100 chars)
- "calories": integer (estimated kcal, 1-5000)
- "protein_g": number (grams, 0 or more)
- "carbs_g": number (grams, 0 or more)
- "fat_g": number (grams, 0 or more)
- "tags": array of strings, only from: ["vegetarian","non-vegetarian","vegan","high-protein","low-carb","snack"]

Example output for "2 eggs and toast":
[{"name":"Boiled Eggs","calories":140,"protein_g":12,"carbs_g":1,"fat_g":10,"tags":["non-vegetarian","high-protein"]},{"name":"Toast","calories":80,"protein_g":3,"carbs_g":15,"fat_g":1,"tags":["vegetarian"]}]

Return ONLY the JSON array, nothing else."""


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class QuickAddError(Exception):
    """Groq API or network failure."""


class QuickAddParseError(Exception):
    """LLM returned output that could not be parsed into valid meal dicts."""


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def parse_meals_from_text(text: str) -> list[dict]:
    """
    Send *text* to Groq, parse the response into a list of meal dicts.

    Returns a list of dicts ready to be passed to MealSerializer.
    Raises QuickAddError on API failure, QuickAddParseError on bad output.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise QuickAddError("GROQ_API_KEY is not set.")

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {"role": "system", "content": QUICK_ADD_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=600,
        )
    except Exception as exc:
        raise QuickAddError(f"Groq API error: {exc}") from exc

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences
    if "```" in raw:
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()

    # Extract JSON array even if model adds thinking text before/after
    # This handles models that output reasoning before the actual JSON
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        raw = match.group(0)

    try:
        meals = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise QuickAddParseError(
            f"LLM returned non-JSON output: {raw[:200]}"
        ) from exc

    if not isinstance(meals, list) or len(meals) == 0:
        raise QuickAddParseError("LLM returned empty or non-list JSON.")

    # Validate each item has required fields
    required = {"name", "calories"}
    for item in meals:
        if not isinstance(item, dict) or not required.issubset(item.keys()):
            raise QuickAddParseError(
                f"Meal item missing required fields: {item}"
            )

    return meals