"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

# ⚠️ HONESTY NOTE: the ten "own writing" pieces below were DRAFTED BY CLAUDE at
# the student's request, in an ordinary human voice (some casual, some plain
# and conventional on purpose, since plain prose is what gets falsely
# accused). They are NOT pieces the student wrote. Criterion 1 as written
# says "pieces I wrote myself", so its verdict is weaker evidence than it
# should be; the README says this too.

OWN_WRITING = [
    # 1 casual
    "I switched my major twice before I figured out what I actually liked. First it was biology because my parents liked the sound of it, then business because my roommate did it. Neither stuck. It was a random elective on film editing that got me, and I stayed up till 3am cutting a two minute clip about my cat. Dumb, but I've never been that into anything.",
    # 2 plain, conventional
    "Last weekend I cleaned out the garage. It took most of Saturday. I found some old textbooks, a broken lamp and a box of cables that I probably will never use. I donated what I could and threw the rest away. The garage looks much bigger now, and my dad says we can finally fit the car in it.",
    # 3 plain report-style
    "Our team met on Monday to plan the science fair project. We decided to test how different kinds of soil affect plant growth. Maya will buy the seeds, Jordan will build the stands, and I will keep the data sheet. We agreed to measure the plants every two days for three weeks and compare the results in a chart.",
    # 4 opinion
    "I think school should start later. Everyone I know is tired by second period, and honestly half the class is just trying to stay awake. Studies say teenagers need more sleep, which makes sense to me because I'm basically a different person after nine hours. Some people say it would mess up sports practice, but that seems fixable.",
    # 5 narrative
    "The first time I rode the train alone I was twelve and convinced I would get off at the wrong stop. I held my ticket so tight it went soft. A man across from me was eating an orange, the smell filled the whole car, and for some reason that calmed me down. I got off at the right stop. I still think about that orange.",
    # 6 explanatory, plain
    "To make the sauce, start by chopping an onion and cooking it in oil until it is soft. Add garlic for a minute, then pour in a can of tomatoes. Let it simmer for about twenty minutes. Add salt and a little sugar if it tastes sharp. My grandmother never measured anything, so these amounts are just my best guess.",
    # 7 reflective
    "Volunteering at the food bank taught me more than I expected. I thought it would be boring, just lifting boxes, but the regulars know each other and the whole place runs on jokes. One man brings donuts every week even though he comes to pick up food himself. I went in to fill service hours and ended up staying a second year.",
    # 8 academic-ish plain
    "The novel follows a family that moves to a small town after a financial loss. The author uses the setting to show how the characters feel trapped, and the weather changes along with the mood of the story. In the final chapters the father finally admits what happened. I found the ending a little rushed but the character work was strong.",
    # 9 casual email
    "Hey, just wanted to say thanks for covering my shift on Friday. I owe you one, seriously. My cousin's flight got moved up and I had no time to find anybody. If you ever need me to take a weekend, just tell me. Also the new schedule looks weird, did they really put me on Tuesday mornings again?",
    # 10 plain description
    "My town has one main street with a bakery, a hardware store and a diner that has been open since the seventies. Most people know each other. In the summer there is a farmers market in the parking lot behind the library. It is not a big place, but I like that you can walk anywhere in ten minutes.",
]

AI_TEXTS = [
    "Artificial intelligence is transforming the way we live and work. It offers numerous benefits, including increased efficiency, improved decision-making, and enhanced productivity. Furthermore, it is important to consider the ethical implications of these technologies. By understanding both the opportunities and challenges, society can ensure that artificial intelligence is developed responsibly. In conclusion, the future of artificial intelligence is bright, and it will continue to shape our world in meaningful ways.",
    "Climate change is one of the most pressing challenges facing humanity today. It is caused primarily by the release of greenhouse gases into the atmosphere. Governments, businesses, and individuals all have a role to play in addressing this issue. By adopting renewable energy sources and reducing consumption, we can create a more sustainable future for generations to come.",
    "Effective communication is essential for success in both personal and professional settings. It involves not only expressing ideas clearly but also listening actively to others. Moreover, strong communication skills can improve relationships, increase productivity, and foster collaboration. By practicing empathy and clarity, individuals can build trust and achieve their goals more effectively.",
    "Education plays a vital role in shaping the future of society. It provides individuals with the knowledge and skills necessary to succeed in an ever-changing world. Additionally, education promotes critical thinking, creativity, and social awareness. In conclusion, investing in education is one of the most important steps a community can take to ensure long-term prosperity.",
    "Regular exercise is one of the most important factors in maintaining good health. It strengthens the heart, improves mood, and helps control weight. Furthermore, physical activity can reduce the risk of chronic diseases such as diabetes and hypertension. By incorporating exercise into their daily routines, people can enjoy a longer and healthier life.",
]

HUMAN_TEXTS = [
    "So I missed the bus again this morning - third time this week, which is honestly embarrassing. Ran after it like an idiot, coffee sloshing everywhere, and the driver just looked at me and pulled away. Grandpa used to say the universe has a sense of humor. Mine apparently likes slapstick. Anyway, I walked. Forty minutes! Got to class soaked, late, and weirdly happy?? Don't ask me why.",
    "My sister's wedding was a disaster, and I loved every minute. The cake collapsed (twice!), her new husband's uncle gave a toast that went on for fifteen minutes, and somebody's dog ate a whole plate of brisket. Still - nobody cared. We danced till the DJ gave up and went home; I've never seen mom laugh so hard.",
    "ok so the thing nobody tells you about moving out: you will cry in an IKEA. Not because of the furniture. Because the little pencil is so cute and you suddenly miss home?? Anyway. Bought the bed, forgot the screws, lived on the floor for a week. 10/10 would do again (but with a checklist).",
    "Dad's truck has a smell. Not bad exactly - coffee, dust, old fries, something like pine. When he sold it last spring I sat in the driver's seat for ten minutes just breathing. The guy who bought it said, 'You okay, kid?' No. Yes. Whatever. It's just a truck.",
    "Honestly? I hated chemistry until Ms. Ortega set a pile of steel wool on fire in front of us. Fire! In school! After that I paid attention to everything - even the boring unit on moles (not the animal, ugh). She retired in June and half the class showed up to say goodbye.",
]

BORDERLINE_TEXTS = [
    "The committee's findings, though preliminary, suggest that the observed decline in enrollment cannot be attributed solely to tuition increases; rather, a confluence of demographic shifts, regional competition, and changes in federal aid policy appears to have contributed. Dr. Okafor, who chaired the review, noted that two of the three affected programs had already lost faculty. Whether the trend will reverse is unclear.",
    "Honestly, remote work has changed a lot about how teams operate. It gives people more flexibility and cuts out the commute, which many folks love. But it also brings real challenges - communication can suffer, and some employees feel isolated. Managers need clear expectations and regular check-ins. Overall, a hybrid model seems to balance these trade-offs pretty well, and lots of companies are heading that way.",
    "Social media has changed how people stay in touch, and I think that's mostly a good thing. You can see what old friends are up to, share photos, and keep up with family overseas. The downside is that it's easy to waste hours scrolling. Experts say moderation is key, and I tend to agree, though I'm not great at following my own advice.",
    "In the past decade, the role of the library has quietly shifted. Books remain central, yes, but patrons now come for internet access, job-search help, and quiet places to study. Librarians, once gatekeepers of information, increasingly act as guides. This evolution is neither a loss nor a triumph; it is simply a response to what communities need.",
    "Learning a second language takes patience. Most people start with excitement and lose steam around month three, when the grammar gets hard. What helped me was talking to real people, even badly. Apps are fine for vocabulary, but nothing beats a conversation where you have to find the word on the spot and hope they understand.",
]

SCENARIOS = [
    {"name": "own writing flagged as AI", "criterion": 1, "texts": OWN_WRITING},
    {"name": "clearly AI", "criterion": 2, "texts": AI_TEXTS},
    {"name": "clearly human", "criterion": 2, "texts": HUMAN_TEXTS},
    {"name": "borderline text", "criterion": 3, "texts": BORDERLINE_TEXTS},
    # Criterion 4 (appeal path) and the non-dict bad bodies of criterion 5 can't
    # be sent through run_eval.py, so run_criteria_extra.py tests them.
    {
        "name": "bad input",
        "criterion": 5,
        "bodies": [
            {"creator_id": "eval_bad_notext"},
            {"text": "This text is long enough but it has no creator at all", "creator_id": ""},
            {"text": "", "creator_id": "eval_bad_empty"},
            {"text": "      ", "creator_id": "eval_bad_blank"},
            {"text": 12345, "creator_id": "eval_bad_number"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": "word " * 30000, "creator_id": "eval_bad_huge"},
        ],
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
