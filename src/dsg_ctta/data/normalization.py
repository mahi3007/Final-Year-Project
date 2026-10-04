"""
Text normalization module for ASR evaluation.
Enforces invariant standardizations: uppercase, punctuation stripping, whitespace collapsing.
"""

from __future__ import annotations
import re
import string
import unicodedata


class TextNormalizer:
    """Canonical text normalizer for exact, fair ASR scoring."""

    # Punctuation to remove: all ASCII punctuation + common unicode typographic quotes/dashes
    PUNCTUATION_PATTERN = re.compile(r"[" + re.escape(string.punctuation) + r"‘’“”«»—–…¿¡]")
    WHITESPACE_PATTERN = re.compile(r"\s+")

    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normalize text to canonical ASR evaluation format.
        
        Rules:
        1. Unicode NFKD normalization (decomposing accents/diacritics).
        2. Uppercase conversion.
        3. Punctuation removal (replaced with space to avoid word joining).
        4. Whitespace trimming and multiple space collapse.
        """
        if not text:
            return ""

        # Step 1: Unicode decomposition
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))

        # Step 2: Uppercase conversion
        text = text.upper()

        # Step 3: Replace hyphens and slashes with space before removing punctuation
        text = text.replace("-", " ").replace("/", " ")

        # Step 4: Punctuation removal
        text = cls.PUNCTUATION_PATTERN.sub(" ", text)

        # Step 5: Collapse multiple whitespaces and strip ends
        text = cls.WHITESPACE_PATTERN.sub(" ", text).strip()

        return text

    @classmethod
    def count_words(cls, text: str) -> int:
        norm = cls.normalize(text)
        if not norm:
            return 0
        return len(norm.split())

    @classmethod
    def count_chars(cls, text: str) -> int:
        norm = cls.normalize(text)
        return len(norm)
