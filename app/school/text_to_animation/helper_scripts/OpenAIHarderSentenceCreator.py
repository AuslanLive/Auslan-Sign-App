# OpenAISentenceCreator.py  — Hard-mode WSD generator with validators & retries
# Requirements: pip install openai
import os
import re
import json
import time
import random
from typing import List, Tuple, Optional
from openai import OpenAI

# ----------------------------
# Config
# ----------------------------
MODEL = "gpt-4o"
REQ_SLEEP_S = 1.0           # rate-limit cushion per request
MAX_TRIES = 3               # retries per (word, sense)
MIN_WORDS = 8               # target sentence length window
MAX_WORDS = 14
TEMPS = [0.7, 0.85, 0.95]   # temperature schedule across retries
SEED = 42                   # set None to disable deterministic sampling

# Output location
OUT_PATH = "app/school/text_to_animation/helper_scripts/outputs/wsd_test_cases_harder.json"
AMBIG_PATH = "app/school/text_to_animation/ambiguous_dict.json"

# Challenge modes (one is chosen per request to force harder cues)
CHALLENGES = [
    "Minimal-cues",   # avoid typical collocations
    "Negation",       # use negation; disambiguation relies on syntax/semantics
    "Attachment",     # PP/clausal attachment resolves the sense
    "Coreference",    # pronoun/demonstrative forces correct reference
    "Passive/Voice",  # unusual/marked voice
    "Rare framing"    # a less common but valid frame
]

# Optional: add extra sense-specific giveaway tokens here to ban (hand-curation)
# e.g., {"bank (financial)": ["account","ATM","interest"], "bank (river)": ["shore","meander"]}
EXTRA_GIVEAWAYS = {}


# ----------------------------
# Utilities
# ----------------------------
def toks(s: str) -> List[str]:
    """Tokenize to alnum-lower tokens."""
    return [t for t in re.split(r"[^A-Za-z0-9]+", s.lower()) if t]

def extract_banned_words(senses: List[str], target_sense: str, word: str) -> List[str]:
    """
    Collect tokens from sense labels (inside/outside parentheses) as giveaways.
    Remove tokens from the target sense (to avoid overconstraining).
    Never ban the ambiguous word itself (we require it).
    """
    all_tokens = set()
    for s in senses:
        all_tokens.update(toks(s))

    target_tokens = set(toks(target_sense))
    all_tokens -= target_tokens
    all_tokens.discard(word.lower())

    # Add any optional hand-curated giveaways
    extra = EXTRA_GIVEAWAYS.get(target_sense, [])
    for e in extra:
        all_tokens.add(e.lower())

    # Remove super short tokens that are too generic (e.g., "a", "an", "to")
    all_tokens = {w for w in all_tokens if len(w) > 2}
    return sorted(list(all_tokens))

def pick_near_miss_token(senses: List[str], target_sense: str, word: str) -> Optional[str]:
    """Pick a token from a non-target sense to act as a soft confounder."""
    others = [s for s in senses if s != target_sense]
    pool = [t for s in others for t in toks(s) if t and t != word.lower() and len(t) > 2]
    return random.choice(pool) if pool else None

def contains_exact_token(sentence: str, word: str) -> bool:
    """Check that {word} appears as a standalone word (case-insensitive)."""
    return re.search(rf"\b{re.escape(word)}\b", sentence, flags=re.IGNORECASE) is not None

def has_forbidden_inflection(sentence: str, word: str) -> bool:
    """
    Enforce 'exact token only' (case-insensitive).
    If sentence contains other morphological forms of {word}, reject.
    We implement a simple heuristic: if any token that starts with word
    but is longer, flag it (e.g., forgets/forgetting/forgot).
    """
    wlow = word.lower()
    for t in toks(sentence):
        if t == wlow:
            continue
        if t.startswith(wlow) and len(t) > len(wlow):
            return True
    return False

def length_ok(sentence: str) -> bool:
    n = len(re.findall(r"[A-Za-z0-9']+", sentence))
    return MIN_WORDS <= n <= MAX_WORDS

def has_banned_giveaway(sentence: str, banned_words: List[str], word: str) -> Optional[str]:
    low = sentence.lower()
    for w in banned_words:
        if w == word.lower():
            continue
        if re.search(rf"\b{re.escape(w)}\b", low):
            return w
    return None

def parse_json_strict(s: str) -> dict:
    """
    Strictly parse JSON from model output. Allows for accidental ```json fences.
    """
    s = s.strip()
    if s.startswith("```json"):
        s = s[7:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    # If it's still not valid, try naive brace extraction
    try:
        return json.loads(s)
    except Exception:
        first = s.find("{")
        last = s.rfind("}")
        if first != -1 and last != -1 and last > first:
            return json.loads(s[first:last+1])
        raise

def passes_validators(example: dict, word: str, banned_words: List[str]) -> Tuple[bool, str]:
    s = example.get("test_sentence", "")
    if not isinstance(s, str) or not s.strip():
        return False, "Empty or missing test_sentence"

    if not contains_exact_token(s, word):
        return False, f'The sentence must include "{word}" as a standalone token (word boundary).'

    if has_forbidden_inflection(s, word):
        return False, f'Inflected form of "{word}" detected; exact base token only.'

    culprit = has_banned_giveaway(s, banned_words, word)
    if culprit:
        return False, f'Giveaway token "{culprit}" present.'

    if not length_ok(s):
        return False, f"Sentence length must be {MIN_WORDS}–{MAX_WORDS} words."

    return True, "ok"


# ----------------------------
# Prompt builder
# ----------------------------
def build_prompt(word: str,
                 senses: List[str],
                 target_sense: str,
                 challenge: str,
                 banned_words: List[str],
                 near_miss: Optional[str]) -> str:
    """
    Build the hard-mode prompt with your two new rules and difficulty knobs.
    """
    banned_list = ", ".join(banned_words[:40])  # cap display length

    extra_confounder = ""
    if near_miss:
        extra_confounder = f"""
## Extra (near-miss confounder)
- Try to include the word "{near_miss}" **only if** you can keep the sentence unambiguous for "{target_sense}".
- If it risks ambiguity, omit it.
"""

    return f"""
You are an expert linguistic AI generating **difficult** test data for a word sense disambiguation (WSD) evaluation.

## Objective
Write **one short, natural English sentence** using the ambiguous word **"{word}"** such that **only one** of its meanings is clearly correct: "{target_sense}".

## Strict Rules
- The sentence **must include** the exact token **"{word}"** as written (case-insensitive). **Do not use inflections** (e.g., if the word is "forget", then "forgot", "forgetting", "forgets" are forbidden).
- The sentence must contain **"{word}" as a standalone word boundary** (not part of another word).
- The sentence **must only support** the intended sense: "{target_sense}".
- **Avoid ambiguity** — do not allow any other sense to plausibly fit.
- **Do not include** words taken from sense labels or obvious giveaways.
- Keep it **concise and natural**: target {MIN_WORDS}–{MAX_WORDS} words.
- Output **valid JSON only** (no backticks, no commentary).

## Options
{json.dumps(senses)}

## Difficulty: apply exactly ONE challenge
- Minimal-cues | Negation | Attachment | Coreference | Passive/Voice | Rare framing
Chosen challenge: **{challenge}**

## Forbidden words (giveaways from option labels and curated lists)
{banned_list or "(none)"}

{extra_confounder}
## Desired JSON format
{{
  "ambiguous_word": "{word}",
  "options": {json.dumps(senses)},
  "test_sentence": "...",
  "answer": "{target_sense}",
  "challenge": "{challenge}"
}}

Now produce exactly ONE example for the sense: "{target_sense}".
""".strip()


# ----------------------------
# Main
# ----------------------------
def main():
    if SEED is not None:
        random.seed(SEED)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Available environment variables:")
        for key in os.environ:
            if 'API' in key or 'OPENAI' in key:
                print(f"  {key} = {os.environ[key][:20]}...")
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialized")


    with open(AMBIG_PATH, "r", encoding="utf-8") as f:
        ambiguous_dict = json.load(f)

    output_data = []

    for word, senses in ambiguous_dict.items():
        # ensure list
        if not isinstance(senses, list) or not senses:
            print(f"[skip] {word}: senses missing or invalid")
            continue

        for target_sense in senses:
            banned_words = extract_banned_words(senses, target_sense, word)
            near_miss = pick_near_miss_token(senses, target_sense, word)
            challenge = random.choice(CHALLENGES)

            for attempt in range(min(MAX_TRIES, len(TEMPS))):
                prompt = build_prompt(
                    word=word,
                    senses=senses,
                    target_sense=target_sense,
                    challenge=challenge,
                    banned_words=banned_words,
                    near_miss=near_miss
                )

                try:
                    resp = client.chat.completions.create(
                        model=MODEL,
                        temperature=TEMPS[attempt],
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a linguist generating difficult, unambiguous WSD test sentences that obey strict constraints."
                            },
                            {"role": "user", "content": prompt}
                        ]
                    )
                    content = resp.choices[0].message.content or ""
                    example = parse_json_strict(content)

                    ok, why = passes_validators(example, word, banned_words)
                    if ok:
                        output_data.append(example)
                        print(f"[✓] {word} → {target_sense} ({example.get('challenge','')})")
                        break
                    else:
                        print(f"[retry] {word} ({target_sense}): {why}")
                        if attempt == MAX_TRIES - 1:
                            print(f"[x] Failed after {MAX_TRIES} tries — skipping.")
                except Exception as e:
                    # On JSON/format/API failure, nudge the model next try
                    print(f"[retry] {word} ({target_sense}): {e}")
                    if attempt == MAX_TRIES - 1:
                        print(f"[x] Failed after {MAX_TRIES} tries — skipping.")

                time.sleep(REQ_SLEEP_S)

    # Save results
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n[done] Wrote {len(output_data)} examples → {OUT_PATH}")


if __name__ == "__main__":
    main()
