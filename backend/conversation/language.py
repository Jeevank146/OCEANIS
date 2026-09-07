import re
from typing import Dict, List, Optional, Tuple


class LanguageDetector:
    """
    Multilingual & script detection engine for Indian coastal languages.
    Supports English, Telugu Unicode, Telugu Transliteration, Hindi Unicode, Hindi Transliteration,
    and other regional variations.
    """

    # Unicode script ranges
    TELUGU_UNICODE_PATTERN = re.compile(r"[\u0c00-\u0c7f]")
    DEVANAGARI_UNICODE_PATTERN = re.compile(r"[\u0900-\u097f]")
    TAMIL_UNICODE_PATTERN = re.compile(r"[\u0b80-\u0bff]")

    # Transliterated Telugu phonetic markers (exclusive grammatical and functional words)
    TELUGU_TRANSLIT_KEYWORDS = {
        "repu", "ivvala", "eroju", "ippudu", "nedu", "sayamthram", "udayam",
        "vellacha", "vellavacha", "vellalani", "povacha", "pothe", "daggara",
        "daggarlo", "unnaya", "undi", "unnara", "nunchi", "nundi", "samudram",
        "chepalu", "tufan", "toofan", "gaali", "ala", "padava", "ela", "enti",
        "cheppu", "chudu", "pettavacha", "unnam", "vetaki", "cheskovacha",
        "veltoondi", "untundhi", "untundi",
    }

    # Transliterated Hindi phonetic markers (exclusive grammatical and functional words)
    HINDI_TRANSLIT_KEYWORDS = {
        "aaj", "kal", "subah", "shaam", "kya", "machli", "pakadne", "sakte",
        "chetavani", "samundar", "laharein", "kaisa", "batao", "chalein",
    }

    # Common Telugu maritime lexicon
    TELUGU_LEXICON = {
        "repu": "tomorrow",
        "ivvala": "today",
        "eroju": "today",
        "udayam": "morning",
        "sayamthram": "evening",
        "udayam 6": "morning 6 AM",
        "6 ki": "at 6:00",
        "vellacha": "can I go",
        "vellavacha": "can I go",
        "samudram": "sea state / marine conditions",
        "chepalu": "fishing / fish",
        "chepala veta": "fishing expedition",
        "tufan": "cyclone / storm",
        "toofan": "cyclone / storm",
        "gaali": "wind",
        "ala": "waves / wave height",
        "padava": "boat / vessel",
        "daggara": "near",
        "nunchi": "from",
        "nundi": "from",
        "unnaya": "are there any",
        "undi": "is it",
        "ela undi": "how is the condition",
    }

    @classmethod
    def detect_language(cls, text: str) -> Tuple[str, str]:
        """
        Detects primary language code and input script mode.
        Returns:
            Tuple of (language_code, input_mode)
            e.g. ("te", "standard"), ("te", "transliterated"), ("hi", "standard"), ("en", "standard")
        """
        if not text or not text.strip():
            return "en", "standard"

        cleaned = text.strip()

        # 1. Check for native Unicode scripts
        if cls.TELUGU_UNICODE_PATTERN.search(cleaned):
            return "te", "standard"
        if cls.DEVANAGARI_UNICODE_PATTERN.search(cleaned):
            return "hi", "standard"
        if cls.TAMIL_UNICODE_PATTERN.search(cleaned):
            return "ta", "standard"

        # 2. Check for Transliterated Telugu
        words = re.findall(r"\b[a-zA-Z]+\b", cleaned.lower())
        if words:
            te_matches = sum(1 for w in words if w in cls.TELUGU_TRANSLIT_KEYWORDS)
            hi_matches = sum(1 for w in words if w in cls.HINDI_TRANSLIT_KEYWORDS)

            if te_matches > 0 and te_matches >= hi_matches:
                return "te", "transliterated"
            if hi_matches > 0:
                return "hi", "transliterated"

        return "en", "standard"

    @classmethod
    def normalize_to_english_intent(cls, text: str, lang: str, mode: str) -> str:
        """
        Produces a normalized English representation of the query for the Agent Orchestrator
        while preserving all locations, entities, coordinates, and temporal anchors.
        """
        if lang == "en" and mode == "standard":
            return text

        normalized = text

        # Telugu Unicode handling
        if lang == "te" and mode == "standard":
            # Direct replacements for common Telugu phrase structures
            replacements = [
                (r"రేపు", "tomorrow"),
                (r"ఈరోజు", "today"),
                (r"ఉదయం", "morning"),
                (r"సాయంత్రం", "evening"),
                (r"నుంచి", "from"),
                (r"నుండి", "from"),
                (r"దగ్గర", "near"),
                (r"వెళ్లవచ్చా\??", "can I go?"),
                (r"వెళ్లొచ్చా\??", "can I go?"),
                (r"చేపల వేట", "fishing"),
                (r"చేపలు", "fishing"),
                (r"తుఫాను", "cyclone"),
                (r"తుఫాన్", "cyclone"),
                (r"హెచ్చరికలు ఉన్నాయా\??", "active warnings present?"),
                (r"సముద్రం ఎలా ఉంది\??", "how are marine conditions?"),
                (r"కాకినాడ", "Kakinada"),
                (r"విశాఖపట్నం", "Visakhapatnam"),
                (r"వైజాగ్", "Vizag"),
                (r"మచిలీపట్నం", "Machilipatnam"),
                (r"కృష్ణపట్నం", "Krishnapatnam"),
                (r"గంగవరం", "Gangavaram"),
            ]
            for pattern, repl in replacements:
                normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)

        # Telugu Transliterated handling
        elif lang == "te" and mode == "transliterated":
            words = normalized.split()
            translated_words = []
            for w in words:
                clean_w = re.sub(r"[^\w]", "", w.lower())
                if clean_w in cls.TELUGU_LEXICON:
                    translated_words.append(cls.TELUGU_LEXICON[clean_w])
                else:
                    translated_words.append(w)
            normalized = " ".join(translated_words)

        # Hindi handling
        elif lang == "hi":
            hindi_replacements = [
                (r"कल", "tomorrow"),
                (r"आज", "today"),
                (r"सुबह", "morning"),
                (r"शाम", "evening"),
                (r"मछली पकड़ने", "fishing"),
                (r"जा सकते हैं\??", "can I go?"),
                (r"तूफान", "cyclone"),
                (r"चेतावनी", "warning"),
                (r"समुद्र", "marine conditions"),
                (r"काकीनाडा", "Kakinada"),
                (r"विशाखापट्टनम", "Visakhapatnam"),
                (r"वाइजाग", "Vizag"),
            ]
            for pattern, repl in hindi_replacements:
                normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)

        return normalized
