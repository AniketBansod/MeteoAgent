import re
from app.schemas import IntentResult
from app.tools import search_city_candidates


def _normalize_city(name: str) -> str:
    # Normalize a potential city string by removing leading/trailing noise tokens
    # and title-casing words (e.g., "compare mumbai" -> "Mumbai").
    raw_tokens = re.split(r"[\s]+", name.strip())
    tokens = []
    for t in raw_tokens:
        t = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", t)  # strip punctuation at edges
        if t:
            tokens.append(t)

    if not tokens:
        return ""

    leading_noise = {
        "compare", "vs", "versus", "and", "or", "than", "to", "from",
        "is", "the", "of", "which", "city", "weather"
    }
    trailing_noise = {"weather", "today", "now", "temperature", "forecast", "climate"}

    # Drop leading noise words
    while tokens and tokens[0].lower() in leading_noise:
        tokens.pop(0)

    # Drop trailing noise words
    while tokens and tokens[-1].lower() in trailing_noise:
        tokens.pop()

    cleaned = [t[0].upper() + t[1:].lower() for t in tokens if t]
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
    #    e.g., "weather in pune", "forecast for new york", also split phrases like
    #    "of pune and nagpur" into individual cities.
    preposition_pattern = r"(?i)\b(?:in|at|for|of|near|around|from|to)\s+([a-zA-Z][\w\-'.]*(?:\s+[a-zA-Z][\w\-'.]*){0,3})"
    connector_split = re.compile(r"\s*(?:,|and|or|vs)\s*", re.IGNORECASE)
    for m in re.findall(preposition_pattern, text):
        for part in connector_split.split(m):
            norm = _normalize_city(part)
            if norm:
                cities.append(norm)

    # 2) Capture multiple cities connected by vs/and/or/commas (case-insensitive)
    connectors_pattern = r"(?i)\b([a-zA-Z][\w\-'.]*(?:\s+[a-zA-Z][\w\-'.]*){0,3})\s*(?:,|and|or|vs)\s*([a-zA-Z][\w\-'.]*(?:\s+[a-zA-Z][\w\-'.]*){0,3})"
    for a, b in re.findall(connectors_pattern, text):
        cities.append(_normalize_city(a))
        cities.append(_normalize_city(b))

    # 3) Capitalized words/groups (fallback for messages like "Pune weather")
    caps_pattern = r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3})\b"
    cities.extend(re.findall(caps_pattern, message))

    # 4) If still empty and message ends with a word, try last token
    if not cities:
        last_word = re.findall(r"([A-Za-z][A-Za-z\-']{1,})\s*$", text)
        if last_word:
            cities.append(_normalize_city(last_word[0]))

    # Filter obvious non-city words
    blacklist = {"What", "Weather", "Can", "Should", "Tell", "Compare", "Is", "The", "Of", "Vs", "And", "Or"}
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

    # First, extract likely city candidates (including multi-word names)
    extracted = extract_cities(message)

    validated: list[str] = []
    for cand in extracted:
        name = search_city_candidates(cand)
        if name:
            validated.append(name)

    # If none validated from extraction, fall back to per-word lookup
    if not validated:
        raw_words = re.findall(r"[a-zA-Z][\w\-']{2,}", text)  # words length >= 3
        seen = set()
        for w in raw_words:
            if w in seen:
                continue
            seen.add(w)
            name = search_city_candidates(w)
            if name:
                validated.append(name)

    # Prepare final city list before intent branching
    cities = list(dict.fromkeys(validated))  # dedupe, preserve order

    future_keywords = ["tomorrow", "next", "forecast", "weekend", "later", "future", "evening", "tonight"]
    has_future = any(w in text for w in future_keywords)

    if any(w in text for w in ["compare", "vs", "difference"]) or (len(cities) >= 2 and "which" in text):
        intent = "comparison"
    elif has_future:
        intent = "forecast"
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
        confidence=confidence,
        is_multi_city=len(cities) > 1,
    )
