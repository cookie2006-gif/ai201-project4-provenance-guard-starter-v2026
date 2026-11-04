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

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

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

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



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
