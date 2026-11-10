# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

A submission goes through seven steps (the full Milestone 1 trace is in [design.md](design.md)):

1. **Arrives** at `POST /submit` as JSON `{text, creator_id}`.
2. **Validation** (`app.py::submit`) rejects missing, non-string, empty, under-20-character or over-20,000-character text, and a missing `creator_id`, with a 4xx JSON error. Each rejection is written to the audit log.
3. **Signal one** (`detector.py::model_signal`) runs GPT-2 locally and returns `model_score`.
4. **Signal two** (`stylometry.py::style_signal`) returns `style_score` from the shape of the text.
5. **Combine** (`scoring.py::combine_signals`) turns both into one `confidence`.
6. **Label** (`scoring.py::score_to_label`) maps `confidence` to one of three labels.
7. **Log and answer** (`audit.py::log_decision`) writes both signal scores, the combined score, guess, label and status `decided` to `logs/audit.jsonl`, and the response returns them with a new `content_id`.

`POST /appeal` checks the `content_id` exists (404 if not), requires reasoning (400 if empty), appends an `appeal` entry with status `under_review` next to the original decision and confirms. `GET /log` shows the log.



---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to GPT-2 (perplexity), squashed to 0-1 where higher means more AI-like. Lives in `detector.py::model_signal` (given; I did not change its midpoint).

**Why that might differ between human and AI writing:** Generated text is made of likely next words, so a language model finds it easy to predict. People surprise the model more.

**What it can't see:** Authorship. It sees only predictability, so plain, conventional human writing is also predictable. That is a real false positive: a short, factual council-meeting summary I wrote scored 0.89. It is also fooled by AI text with unusual word choices, and GPT-2 is old, so modern AI output is less predictable to it than older output.

### Signal two — the style signal

**What it measures:** The shape of the text, without understanding it (`stylometry.py::style_signal`): (a) sentence-length spread (stdev / mean of sentence lengths, weight 0.45), (b) type-token ratio on the first 100 words (weight 0.20), (c) expressive punctuation (semicolons, colons, dashes, parentheses, quotes, `!`, `?`, ellipses; weight 0.35). Each is scaled to 0-1, flipped so higher means more AI-like, and averaged.

**Why that might differ between human and AI writing:** Generated prose tends toward even, mid-length sentences, a narrower vocabulary and only commas and full stops. Human writing is lumpier, with a three-word sentence next to a forty-word one and more varied punctuation.

**What it can't see:** Meaning. It can't read, so anything that changes shape without changing substance moves it: breaking up sentences, adding typos or dashes, pasting a quotation. Careful, even, plain human writers (news summaries, reports) look like AI to it. A one-sentence text has no spread (it returns a neutral 0.5 for that part). Both signals share one blind spot, plain prose, which is why they agreed on the false positive above.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** A weighted average of the two scores. If the signals disagree by more than 0.30, the distance of the average from 0.5 is halved, because two methods disagreeing is itself uncertainty, so a split vote can never produce a confident label.

**The numbers:** `confidence = 0.55 * model_score + 0.45 * style_score`; if `|model_score - style_score| > 0.30` then `confidence = 0.5 + (confidence - 0.5) * 0.5`. Thresholds: human below 0.35, AI at 0.70 or above (all in `config.py`). The model gets slightly more weight because it reads the text's content statistically, while the style signal is a cheap heuristic. The AI threshold (0.70) is deliberately higher than 0.5 and the unsure band is wide (0.35 wide on the human side, 0.35 overall to 0.70) because a false accusation costs a writer more than a missed AI text costs the site.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:** The formal human paragraph about a committee's enrollment findings (long, semicolon-heavy sentence; one short one). Signal one said 0.70 (formal prose is predictable) but signal two said 0.32 (varied sentence lengths, a semicolon). The plain average would be 0.53; the gap is 0.38 > 0.30 so it is pulled to 0.515, firmly "unsure" and not an accusation.

Calibration table (the four required cases plus extras; all from `samples/`):

| Input | model | style | confidence | guess |
|---|---|---|---|---|
| clearly AI (ai) | 0.883 | 0.747 | 0.822 | ai |
| clearly AI (ai2) | 0.951 | 0.723 | 0.849 | ai |
| clearly human (human) | 0.345 | 0.175 | 0.268 | human |
| clearly human (human2) | 0.453 | 0.103 | 0.398 | unsure |
| formal human | 0.703 | 0.321 | 0.515 | unsure |
| lightly-edited AI | 0.504 | 0.559 | 0.529 | unsure |
| plain human news summary (mid) | 0.894 | 0.795 | 0.849 | **ai (false positive)** |

The last row is the honest finding: plain, factual human prose gets called AI by both signals, and my combining rule can't help because they agree. The appeal path exists for this writer.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 | We think this was probably written by a person. |
| unsure | 0.35 – 0.70 | We can't tell for sure whether a person or an AI tool wrote this. Nothing is wrong with your work and no action has been taken. |
| high-confidence AI | 0.70 – 1.00 | This looks like it may have been written with an AI tool. We can get this wrong. If you wrote it yourself, you can appeal and a person will take a look. |

**Why I worded the "unsure" one this way:** It says plainly that the system doesn't know, and then says nothing is wrong and nothing has happened, since most people receiving it wrote their own work and shouldn't feel accused. Even the AI label says "may" and "we can get this wrong", and points to the appeal.

All three are reachable through real submissions (see the table above: ai, human, unsure).



---

## Sample Run

**A submission** (the plain human news summary, which is the false-positive case)

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The city council met on Tuesday to discuss the proposed changes to the downtown parking rules. Several residents spoke during the public comment period, and most of them opposed the plan. The council said it would review the feedback and vote on the proposal at its next meeting in two weeks.", "creator_id": "mid"}'
```

```json
{
  "confidence": 0.8493,
  "content_id": "74f10521-9149-4b20-a333-77874b111105",
  "guess": "ai",
  "label": "This looks like it may have been written with an AI tool. We can get this wrong. If you wrote it yourself, you can appeal and a person will take a look.",
  "model_score": 0.8935,
  "status": "decided",
  "style_score": 0.7953
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "74f10521-9149-4b20-a333-77874b111105", "reasoning": "I wrote this news summary myself from my own notes of the meeting."}'
```

```json
{
  "content_id": "74f10521-9149-4b20-a333-77874b111105",
  "message": "Thanks - your appeal is recorded and this piece is now under review by a person.",
  "status": "under_review"
}
```

An unknown id returns 404 `{"error": "unknown_content_id", ...}`; empty reasoning returns 400 `missing_reasoning`.

**What the log shows afterwards**

```bash
$ grep 74f10521 logs/audit.jsonl     # the same entries GET /log returns
```

```json
{"timestamp": "2026-11-04T03:42:54+00:00", "content_id": "74f10521-9149-4b20-a333-77874b111105", "creator_id": "mid", "guess": "ai", "model_score": 0.8935, "style_score": 0.7953, "combined_score": 0.8493, "label": "This looks like it may have been written with an AI tool. We can get this wrong. If you wrote it yourself, you can appeal and a person will take a look.", "status": "decided", "text_length": 292}
{"timestamp": "2026-11-04T03:43:05+00:00", "content_id": "74f10521-9149-4b20-a333-77874b111105", "creator_id": "mid", "event": "appeal", "status": "under_review", "reasoning": "I wrote this news summary myself from my own notes of the meeting."}
```

Bad-input check (criterion 5): missing text, empty `creator_id`, empty text, whitespace text, non-string text, a JSON list and non-JSON bodies all returned 400; a 150,000-character text returned 413. No 500s, and each rejection appears in the log as an `event: rejected` entry.

---

## How I Used AI

**Moment 1**

- *What I asked for:* Fill in `stylometry.py` with the three measures (sentence spread, type-token ratio, punctuation) combined into a 0-1 "higher = more AI" score.
- *What came back:* Working functions, with raw type-token ratio over the whole text.
- *What I changed:* I measured type-token ratio on the first 100 words only (the starter warns it falls with length), gave it the lowest weight, and ignored commas and full stops in the punctuation measure. I checked the result on my own samples before trusting it.

**Moment 2**

- *What I asked for:* A combining rule that treats disagreement between the signals as uncertainty, and the three label texts.
- *What came back:* A weighted average with a shrink toward 0.5 on disagreement, and labels.
- *What I changed:* I raised the AI threshold to 0.70 after my plain human news summary scored 0.85, and reworded the labels so even the AI one says "may" and points to the appeal. I kept the false positive in the README instead of tuning it away.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 10 per minute, 200 per day, on `POST /submit` (`config.py`, enforced by the `@limiter.limit` line in `app.py`; `GET /health` reports `rate_limiting: true`).

**Why those numbers and not others:** A real writer submits their own work a few times an hour; even a heavy revising session is a handful per minute, so 10 per minute never gets in their way and 200 per day is far above honest use. A script mapping my thresholds needs hundreds of variations: 10 per minute turns that into hours, and 200 per day caps it at a few hundred probes a day per caller. I did not go lower because the limiter also counts requests that my route rejects with a 400, and I don't want a writer who mistypes a few times to be locked out.

**What a caller counts as:** The `creator_id` in the request body, falling back to the caller's IP address when the body has no usable `creator_id` (the starter's `rate_limit_key`). That means one script can dodge the limit by rotating `creator_id` values, and the limit is not per address. Per-address would fail the other way, since one household or school would share a single quota.

**The run of status codes when I pushed past it:**

```
$ python run_attacks.py --flood 15
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

The 429s are logged by the starter's handler, for example:

```json
{"timestamp": "2026-11-10T23:19:37+00:00", "creator_id": "flood_tester", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "10 per 1 minute"}
```

Full output: `results/flood_2026-11-10_1719.md`.

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

All numbers below are from `python run_eval.py --label before` and `python run_criteria_extra.py --label before` (`results/run_2026-11-10_1723_before.md`, `results/extra_2026-11-10_1723_before.json`). Three trials, nothing changed in between; every trial was identical, as expected, since neither signal is random.

> **Important caveat on criterion 1.** `criteria.md` says "10 pieces I wrote myself". The ten pieces in `scenarios.py` were **drafted by Claude at my request** (I did not have time to supply my own), in an ordinary human voice and with some plain, conventional ones on purpose. So criterion 1's verdict is weaker evidence than it should be, and should be re-run on my own writing. I did not edit the criterion.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Own writing labelled AI | at most 1 of 10 | 2/10 | 2/10 | 2/10 | **MISSED** |
| 2. Score spread, AI vs human | mean gap >= 0.25 and every clearly-AI > 0.5 | gap 0.547, min AI 0.775 | same | same | **MET** |
| 3. Labels reachable; borderline lands in "unsure" | 3 of 3 labels; >= 3 of 5 borderline unsure | 3/3 labels; 4/5 | 3/3; 4/5 | 3/3; 4/5 | **MET** |
| 4. Appeals change status and are logged | 10 of 10 (404 unknown id, 400 empty reasoning) | 10/10, 404, 400 | 10/10, 404, 400 | 10/10, 404, 400 | **MET** |
| 5. Bad input: 0 crashes across 8 bodies | 8 of 8 are 4xx JSON, no 500 | 8/8 | 8/8 | 8/8 | **MET** |

How I decided: criterion 1's target is at most 1 and every trial came out 2, so it is a miss with no generous reading. Criterion 3's second half needs 3 of 5; I got 4 of 5 each time. Criterion 2 is met by a wide margin, but note the weakest AI text (0.775) is only 0.075 above the AI threshold, so my target was fairly easy on that side and I'd tighten it to "every clearly-AI sample above 0.75 and mean gap above 0.4".

**Real output, one trial each (from `run_eval.py::main` calling `app.py::submit`; appeals from `run_criteria_extra.py::trial` calling `app.py::appeal`)**

Criterion 1, the two pieces called AI (`scenarios.py::OWN_WRITING` #6 and #10):

```json
{"status": 200, "guess": "ai", "confidence": 0.7054, "model_score": 0.7361, "style_score": 0.6679, "sent": "To make the sauce, start by chopping an onion and cooking it in oil until it is soft..."}
{"status": 200, "guess": "ai", "confidence": 0.7138, "model_score": 0.8032, "style_score": 0.6046, "sent": "My town has one main street with a bakery, a hardware store and a diner that has been open since the seventies..."}
```

Criterion 2: clearly-AI scored 0.822, 0.849, 0.775, 0.810, 0.841 (mean 0.819); clearly-human scored 0.268, 0.398, 0.214, 0.336, 0.146 (mean 0.272).

Criterion 3: the borderline set gave `unsure` ×4 and one `ai` (0.7124, the social media paragraph); the human label was reached by "clearly human" (0.2684) and the AI label by "clearly AI" (0.822).

Criterion 4:

```json
{"content_id": "...", "http": 200, "body": {"message": "Thanks - your appeal is recorded and this piece is now under review by a person.", "status": "under_review"}, "logged": true}
```
Unknown id -> 404, empty reasoning -> 400, in all three trials.

Criterion 5: `{"creator_id": ...}` (no text), empty `creator_id`, empty text, whitespace text, number text, null text, a JSON list and a non-JSON body each returned 400 with `{"error": ..., "message": ...}`; a 150,000-character text returned 413. No 500s.

**Diagnoses**

- **Criterion 1 (MISSED): stage = signals one and two together, then the combining rule.** The two flagged pieces are the recipe (#6) and the plain town description (#10). Both are short, plain declarative sentences of similar length with only commas and full stops. Signal one found them predictable (0.74 and 0.80: instructions and "a bakery, a hardware store" are very common word sequences for GPT-2). Signal two scored them 0.67 and 0.60 because sentence-length spread is low and they have none of the expressive punctuation it treats as human. Because both signals have the same blind spot (plain, conventional prose), they agree, the disagreement shrink in `scoring.py::combine_signals` never fires, and the average (0.705 and 0.714) lands just over the 0.70 threshold. The mechanism is that "plain" and "AI" look the same to both of my signals. Several other plain pieces (#2 garage 0.60, #8 novel 0.68) also sit just under the line.
- **Criterion 3's one borderline miss:** the social media paragraph (0.7124) is flagged AI for the same reason: even sentences, no expressive punctuation, generic topic.
- **Pattern:** one problem, not three: plain prose scores in the high 0.6s to low 0.7s from both signals, and my AI threshold (0.70) sits inside that band, while my weakest clearly-AI text is 0.775. There is a thin margin to work with, not a gap.
- **No miss on criteria 2, 4, 5.** Stability: all three trials were identical, so nothing in the pipeline is unstable.

---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
