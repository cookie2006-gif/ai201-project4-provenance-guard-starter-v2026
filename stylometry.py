"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def _clamp(x: float) -> float:
    return min(max(x, 0.0), 1.0)


def sentence_length_spread(text: str) -> float:
    """
    Coefficient of variation of sentence length (stdev / mean, in words).

    Scale: 0 means every sentence is the same length; ~0.3 is typical of
    even, generated prose; 0.7+ is lumpy. **Higher = more human.**
    A text with fewer than two sentences has no spread, so it returns 0.5
    (a neutral, mid-range value) instead of raising.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.5
    mean = statistics.mean(lengths)
    return statistics.stdev(lengths) / mean if mean else 0.5


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words, measured on the first 100 words so texts of
    different lengths are comparable (TTR falls as text gets longer).
    Scale 0-1. **Higher = more varied vocabulary = more human.**
    """
    w = words(text)[:100]
    return len(set(w)) / len(w) if w else 0.0


def punctuation_density(text: str) -> float:
    """
    How rich the punctuation is: marks per word from the 'expressive' set
    (semicolon, colon, dash, parentheses, quotes, ! ?, ellipsis), plus a bonus
    for how many different kinds appear. Commas and full stops are ignored
    because every writer uses them. Roughly 0-1; **higher = more human.**
    """
    w = len(words(text))
    if not w:
        return 0.0
    marks = re.findall(r"[;:!?()\"\u201c\u201d]|--|\u2014|\u2013|\.\.\.|\u2026| - ", text)
    density = len(marks) / w                     # ~0.0 (AI-plain) to ~0.15+
    kinds = len(set(marks))                      # 0-8
    return _clamp(density / 0.10 * 0.6 + kinds / 4 * 0.4)


# ── Combining them ───────────────────────────────────────────────────────────

# Weights inside the style signal (sum to 1). Spread is the strongest cue;
# type-token ratio is weakest (it moves with topic), so it counts least.
W_SPREAD, W_TTR, W_PUNCT = 0.45, 0.20, 0.35


def style_signal(text: str) -> float:
    """
    The style signal as a 0-1 score. **Higher means more likely AI.**

    Each measure is "higher = more human", so each is scaled to 0-1 and
    flipped (1 - x):
      spread: CV 0.0 -> 1.0 (AI-ish), CV >= 0.8 -> 0.0 (human-ish)
      ttr:    0.95+ -> 0.0, 0.55 or less -> 1.0 (linear in between)
      punct:  already 0-1, flipped
    Then a weighted average.
    """
    spread = _clamp(sentence_length_spread(text) / 0.8)
    ttr = _clamp((type_token_ratio(text) - 0.55) / 0.40)
    punct = _clamp(punctuation_density(text))
    human_ness = W_SPREAD * spread + W_TTR * ttr + W_PUNCT * punct
    return round(1.0 - human_ness, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print("\nAll zeros? These are stubs — Milestone 4 is where you build them.")
