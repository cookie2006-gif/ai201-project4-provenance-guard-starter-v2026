# Design notes — Milestone 1 (written before any code)

## The path a submission takes
1. **Arrives** at `POST /submit` as JSON `{text, creator_id}`.
2. **Validation** rejects missing / non-string / empty / too-short / enormous text with a 400 and logs the rejection. Adds: a guarantee later stages see clean input.
3. **Signal one** (`detector.model_signal`) runs GPT-2 locally and returns `model_score` 0-1 (higher = more AI-like).
4. **Signal two** (`stylometry.style_signal`) measures sentence-length spread, vocabulary variety and punctuation, returns `style_score` 0-1.
5. **Combining rule** (`scoring.combine_signals`) merges them into one `confidence` score, pulling toward the middle when the signals disagree.
6. **Label** (`scoring.score_to_label`) maps the score to one of three full-sentence labels.
7. **Audit log** (`audit.log_decision`) writes both signal scores, combined score, guess, label and status `decided`; the response returns content_id, guess, confidence, label, model_score, style_score.

## Signals
**Signal one - model predictability.** Measures how predictable the text is to GPT-2 (perplexity). Generated text is the likeliest continuation, so it tends to be low-perplexity; people surprise the model more. *Blind spot:* it only sees predictability, not authorship. Plain, conventional, or heavily-edited human prose is predictable too (false positives), and AI text with odd word choices or typos looks surprising (false negatives). Short text gives noisy readings; GPT-2 is old, so modern LLM output is less predictable to it.

**Signal two - style shape.** Measures text as text: spread of sentence lengths, type-token ratio, punctuation density/variety. AI prose tends to have even mid-length sentences and a narrow vocabulary; people are lumpier. *Blind spot:* it can't read. Anything that changes shape but not substance moves it: breaking up sentences, adding typos, pasting quotes. Careful human writers with even, tidy style look like AI; short texts have no meaningful spread.

## The false positive
A real writer submits a plain, tidy, conventional essay. GPT-2 finds it predictable (model_score ~0.7) and even sentences give a style_score ~0.6, so confidence is ~0.65. If that is over the AI threshold, they see "probably AI-generated". They can `POST /appeal` with reasoning; status becomes `under_review` and the appeal is logged beside the original decision. That is why the AI threshold is high (0.70), the "unsure" band is wide, the unsure label is never an accusation, and the AI label itself points to the appeal.

## Endpoint contracts
**POST /submit** in: `{"text": str (required, 20-20000 chars), "creator_id": str (required, non-empty)}`.
Out 200: `{"content_id": str uuid, "guess": "ai"|"human"|"unsure", "confidence": float 0-1 (higher = more likely AI), "label": str, "model_score": float, "style_score": float, "status": "decided"}`.
Out 400: `{"error": code, "message": str}` for bad input; nothing is scored.

**POST /appeal** in: `{"content_id": str, "reasoning": str (non-empty)}`.
Out 200: `{"content_id", "status": "under_review", "message": str}`. 404 if the content_id is unknown, 400 if reasoning is missing.
