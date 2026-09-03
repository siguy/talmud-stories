"""Speech-act lexicon — the verbs that look like actions but are not.

PROVENANCE
  Jeff Rubenstein, email 2026-09-02 (after reviewing the 25 Gittin passages):
    "a lot of the AI's confusion had to do with speech-acts or quasi speech-acts
     that could seem like actions but are really more connected to a legal
     discussion, not a story... words like 'retracted,' 'considered,'
     'responded' and even 'sent' (when what he sends is a message or question)
     should not be evaluated as actions for our purposes, or that those sources
     require extra scrutiny."
  Jeff, 2026-03-17 review corpus:
    "'stating, objecting, asking questions' are all part of a dialogue,
     and not really events."
  Jeff, 2026-07-06 criteria:
    emotional reactions ("Rabbi X was embarrassed") DO count as events.

DESIGN — three tiers, not one blacklist.
  A flat stopword list is wrong because the same verb flips on its object:
  "sent a messenger" is an action, "sent a question" is a speech-act;
  "retracted a get" is an action, "retracted his opinion" is a speech-act.
  So T1 disqualifies, T2 only triggers scrutiny, T3 is the positive target
  that keeps the rule from eating real stories.

  The lists are used as PROMPT MATERIAL and as a post-hoc surface-form flag.
  They are never a hard regex veto on their own.
"""

# T1 — pure speech-acts. On their own these are never a story event.
TIER1_SPEECH_ACTS = {
    "english": [
        "said", "stated", "replied", "responded", "answered", "asked",
        "questioned", "objected", "raised an objection", "ruled", "taught",
        "recited", "declared", "argued", "explained", "maintained", "held",
        "reasoned", "inferred", "cited", "quoted", "interpreted", "expounded",
        "instructed", "permitted", "prohibited", "deemed",
    ],
    "aramaic": [
        "אָמַר", "אֲמַר לֵיהּ", "תָּנֵי", "תְּנַן", "תָּנוּ רַבָּנַן", "מֵתִיב",
        "אֵיתִיבֵיהּ", "בָּעֵי", "אִיבַּעְיָא לְהוּ", "אַהְדַּר", "מַתְקִיף לַהּ",
        "קָא סָבַר", "פְּשִׁיטָא", "מְנָא הָנֵי מִילֵּי", "אֶלָּא",
    ],
}

# T2 — quasi speech-acts. Look like actions; disqualify unless the OBJECT is
# physical. These are the ones Jeff says "require extra scrutiny".
TIER2_SCRUTINY = {
    "english": [
        "sent",         # a message/question = speech; a messenger/object = action
        "retracted",    # an opinion = speech; a document/get = action
        "considered",   # deliberation = speech-act-like; NOT the same as feeling
        "thought",      # ditto
        "intended",
        "brought",      # a case before a sage = framing; an object = action
        "came before",  # legal framing, not narrative
        "appeared before",
        "sat", "was sitting",   # setting, not event
        "stood",                # often rhetorical ("stood and said")
        "went out",             # sometimes idiom for a ruling being issued
        "wrote",        # a get/document = action; a responsum = speech
    ],
    "aramaic": [
        "שָׁלַח לֵיהּ", "הָדַר בֵּיהּ", "סְבַר", "אֲתָא לְקַמֵּיהּ", "יָתֵיב",
        "הֲוָה יָתֵיב", "קָם", "נְפַק", "כָּתַב",
    ],
}

# T3 — the positive target. Presence of ANY of these is what makes a passage
# survive the speech-act rule. Split so Jeff's emotional-reaction carve-out
# stays visible and separately countable.
TIER3_REAL_EVENTS = {
    "physical_english": [
        "went", "traveled", "ascended", "descended", "arrived", "fled", "hid",
        "found", "met", "struck", "hit", "tore", "seized", "took", "gave",
        "bought", "sold", "stole", "died", "fell ill", "married", "divorced",
        "ate", "drank", "wept aloud", "threw", "burned", "built", "freed",
    ],
    "physical_aramaic": [
        "אֲזַל", "סְלֵיק", "נְחֵית", "אַשְׁכְּחֵיהּ", "עֲרַק", "שְׁקַל", "יְהַב",
        "זַבֵּין", "מִית", "חֲלַשׁ", "נְסֵיב", "אֲכַל", "מְחָא",
    ],
    # Jeff 2026-07-06: these COUNT as events.
    "emotional_english": [
        "was embarrassed", "was ashamed", "was distressed", "was offended",
        "wept", "rejoiced", "was angry", "was afraid", "was astonished",
        "took offence", "was humiliated",
    ],
    "emotional_aramaic": [
        "אִיכְּסִיף", "חֲלַשׁ דַּעְתֵּיהּ", "בְּכָה", "חֲדִי", "אִיקְּפַד",
        "אִיסְתַּיַּים", "כְּסִיפָא לֵיהּ",
    ],
}


def _all(d):
    out = []
    for v in d.values():
        out.extend(v)
    return out


def surface_flags(text: str) -> dict:
    """Cheap, deterministic surface-form flags. NOT a verdict — a router.

    Returns which lexicon entries literally appear in the passage text.
    Used to (a) report co-occurrence with the model's verdict, and
    (b) show Jeff how often his words fire.
    """
    low = text.lower()
    hit = lambda terms: sorted({t for t in terms if (t.lower() in low if t.isascii() else t in text)})
    return {
        "tier1": hit(_all(TIER1_SPEECH_ACTS)),
        "tier2": hit(_all(TIER2_SCRUTINY)),
        "tier3_physical": hit(TIER3_REAL_EVENTS["physical_english"] + TIER3_REAL_EVENTS["physical_aramaic"]),
        "tier3_emotional": hit(TIER3_REAL_EVENTS["emotional_english"] + TIER3_REAL_EVENTS["emotional_aramaic"]),
    }
