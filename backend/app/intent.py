import re
from app.schemas import IntentResult


def _normalize_city(name: str) -> str:
    # Title-case tokens but keep hyphens/apostrophes (e.g., "st. louis" -> "St Louis")
    tokens = re.split(r"[\s]+", name.strip())
    cleaned = []
    for t in tokens:
        # remove trailing punctuation
        t = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", t)
        if not t:
            continue
        cleaned.append(t[0].upper() + t[1:].lower())
    return " ".join(cleaned)


def extract_cities(message: str) -> list[str]:
    """
    Extract likely city names using tolerant regex heuristics.
    - Supports lowercase inputs (e.g., "pune")
    - Handles multi-word cities (e.g., "new york")
    - Looks after prepositions like in/of/at/for/near/around
    """
    text = message.strip()
    cities: list[str] = []

    # 1) Preposition-based capture (case-insensitive)
    #    e.g., "weather in pune", "forecast for new york"
    preposition_pattern = r"(?i)\b(?:in|at|for|of|near|around|from|to)\s+([a-zA-Z][\w\-'.]*(?:\s+[a-zA-Z][\w\-'.]*){0,3})"
    for m in re.findall(preposition_pattern, text):
        cities.append(_normalize_city(m))

    # 2) Capitalized words/groups (fallback for messages like "Pune weather")
    caps_pattern = r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3})\b"
    cities.extend(re.findall(caps_pattern, message))

    # 3) If still empty and message ends with a word, try last token
    if not cities:
        last_word = re.findall(r"([A-Za-z][A-Za-z\-']{1,})\s*$", text)
        if last_word:
            cities.append(_normalize_city(last_word[0]))

    # Filter obvious non-city words
    blacklist = {"What", "Weather", "Can", "Should", "Tell", "Compare", "Is", "The", "Of"}
    cities = [c for c in cities if c and c not in blacklist]

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for c in cities:
        if c not in seen:
            deduped.append(c)
            seen.add(c)

    return deduped


def detect_intent(message: str) -> IntentResult:
    text = message.lower()
    cities = extract_cities(message)

    if any(w in text for w in ["compare", "vs", "difference"]):
        intent = "comparison"
    elif any(w in text for w in ["should i", "can i", "advice", "wear", "run", "travel"]):
        intent = "advice"
    elif any(w in text for w in ["weather", "temperature", "forecast", "climate", "temp"]):
        intent = "current_weather"
    else:
        intent = "unknown"

    confidence = 0.9 if cities else 0.6

    return IntentResult(
        intent=intent,
        cities=cities,
        confidence=confidence
    )
