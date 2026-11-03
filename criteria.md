# Acceptance criteria — Provenance Guard

Written in unit 7 **before** the service was built or any result seen.

## 1. False positives: at most 1 of 10 of my own pieces is labelled high-confidence AI

I will run 10 pieces I wrote myself (plain and ordinary prose, 80-200 words, not just formal essays) through `/submit`. At most 1 may get the guess `ai`, and this has to hold in every one of three trials.

**Why this target:** On a writing site, wrongly accusing a real writer costs that person far more than a missed AI text costs the site. 1 in 10 is the most I'd tolerate and I'd rather hit 0; 0 would be dishonest to promise for a GPT-2 based detector.

## 2. Score spread: clearly-AI text averages at least 0.25 higher than clearly-human text

Using 5 clearly-AI samples (chatbot-style output) and 5 clearly-human samples (casual, personal, uneven), the mean `confidence` of the AI group must exceed the mean of the human group by at least 0.25, and every clearly-AI sample must score above 0.5.

**Why this target:** A confidence score that only flips near 0.5 isn't confidence. A 0.25 gap is large enough that the three labels mean different things, small enough to be achievable with two cheap signals.

## 3. Label coverage: all three labels reachable, and text I judge borderline lands in "unsure" in at least 3 of 5 cases

I must be able to produce `ai`, `human` and `unsure` from real submissions (not by calling `score_to_label` directly). Of 5 pieces I judge borderline (e.g. lightly-edited AI, formal human), at least 3 must score into the unsure band.

**Why this target:** An unreachable label means a gap in my ranges. "Unsure" is the safe answer for a writer who might be innocent, so it must actually catch the hard cases.

## 4. The appeal path: 10 of 10 appeals on valid ids change status to under_review and are logged

For 10 valid content_ids, `/appeal` must return 200 with `status: under_review` and `GET /log` must show an appeal entry for each id. An unknown content_id must return 404 and write no appeal; empty reasoning must return 400.

**Why this target:** The appeal is the only recourse for a wrongly accused writer, so it is the one feature that gets a 100% target with no tolerance.

## 5. Bad input: 0 crashes (no 500s) across 8 malformed submissions

Missing text, missing creator_id, empty text, whitespace-only text, non-string text, a JSON body that is a list, a non-JSON body, and a 100,000-character text must each return a 4xx JSON error with an `error` field (never a 500), and each rejection is written to the audit log.

**Why this target:** A crash on malformed input is one of the most common real failures, and next unit's attack set will throw exactly these at it. Rejections must also leave a trace so they aren't invisible.
