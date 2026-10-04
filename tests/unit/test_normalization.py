"""
Unit tests for text normalization rules.
"""

from dsg_ctta.data.normalization import TextNormalizer


def test_punctuation_stripping():
    raw = "Hello, world! How is everything? (It's great...)"
    norm = TextNormalizer.normalize(raw)
    assert norm == "HELLO WORLD HOW IS EVERYTHING IT S GREAT"


def test_unicode_accents():
    raw = "Résumé café naïve São Paulo"
    norm = TextNormalizer.normalize(raw)
    assert norm == "RESUME CAFE NAIVE SAO PAULO"


def test_whitespace_collapsing():
    raw = "   word1   \t\n  word2    word3  "
    norm = TextNormalizer.normalize(raw)
    assert norm == "WORD1 WORD2 WORD3"


def test_hyphen_and_slash():
    raw = "state-of-the-art model/system"
    norm = TextNormalizer.normalize(raw)
    assert norm == "STATE OF THE ART MODEL SYSTEM"
