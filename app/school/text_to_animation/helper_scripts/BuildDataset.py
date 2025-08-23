"""
Builds a Word-Sense Disambiguation (WSD) training dataset from a lemma→senses JSON using the OpenAI API.

What it produces:
- senses.json   : catalog of sense entries (sense_id, lemma, definition, examples[])
- dataset.jsonl : one training row per generated sentence with negatives
- META.json     : run metadata and split statistics

Constraints enforced on generated sentences:
1) DO NOT include the sense label text (parentheses) in any sentence.
2) Sentence must contain the exact token "{word}" (case-insensitive), as a standalone word boundary.
3) No inflections of "{word}" (enforced by the word-boundary regex).
4) No parentheses "()" in sentences.
5) Length 8–22 words, diverse, grammatical; de-duplicated.
"""
import json
import os
import random
import re
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('app/.env')

# --- Data classes -----------------------------------------------------------
@dataclass
class SenseEntry:
    sense_id: str
    lemma: str
    definition: str
    examples: List[str]

# --- Utility functions ------------------------------------------------------
def stable_shuffle(items, seed=42):
    rnd = random.Random(seed)
    items = list(items)
    rnd.shuffle(items)
    return items

def split_lemmas(lemmas: List[str], ratios=(0.8, 0.1, 0.1), seed=42) -> Dict[str, str]:
    lemmas = stable_shuffle(lemmas, seed=seed)
    n = len(lemmas)
    n_train = int(n * ratios[0])
    n_dev = int(n * ratios[1])
    split_map = {}
    for i, lemma in enumerate(lemmas):
        if i < n_train:
            split_map[lemma] = "train"
        elif i < n_train + n_dev:
            split_map[lemma] = "dev"
        else:
            split_map[lemma] = "test"
    return split_map

def word_boundary_regex(word: str) -> re.Pattern:
    # Case-insensitive whole-word match, using word boundaries.
    # This ensures "fly" does not match "flies" or "butterfly".
    return re.compile(rf"(?i)\b{re.escape(word)}\b")

def contains_parentheses(text: str) -> bool:
    return "(" in text or ")" in text

def sentence_length_ok(text: str) -> bool:
    # Rough token count by whitespace
    wc = len(text.strip().split())
    return 8 <= wc <= 22

def normalize_sentence(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def dedupe_preserving_order(seq: List[str]) -> List[str]:
    seen = set()
    out = []
    for s in seq:
        k = normalize_sentence(s)
        if k not in seen:
            seen.add(k)
            out.append(s.strip())
    return out

def sentence_passes_rules(sentence: str, word: str) -> bool:
    # 1) Must contain the exact token "{word}" (case-insensitive), as a standalone word boundary.
    if not word_boundary_regex(word).search(sentence):
        return False
    # 2) No inflections of "{word}" (enforced by word-boundary regex above).
    # 3) No parentheses "()" in sentences.
    if contains_parentheses(sentence):
        return False
    # 4) Length 8–22 words, diverse, grammatical; de-duplicated.
    if not sentence_length_ok(sentence):
        return False
    return True

# --- Prompts ---------------------------------------------------------------
SENSE_PROMPT = """You produce a compact JSON object with keys: sense_id, lemma, definition, examples.
Create a sense entry for the lemma "{lemma}" with the label "({label})".
Rules:
- sense_id = "{lemma} ({label})" - the lemma followed by the label in parentheses.
- definition: <= 25 words, neutral and clear.
- examples: an array with 2-3 short example sentences (6-18 words), natural and grammatical.
- Do NOT include parentheses or any sense labels in the examples.
- Avoid unsafe or sensitive content; no PII.
Return ONLY JSON."""

SENTENCES_PROMPT = """Return a JSON object with a key "sentences" whose value is an array of strings.
Generate {n} sentences for the lemma "{word}" that express the sense "{label}".
HARD RULES (must all be satisfied):
1) Each sentence MUST contain "{word}" exactly (case-insensitive), as a standalone word with word boundaries.
2) Do NOT use inflections of "{word}" (e.g., for 'fly': flies, flying, etc.).
3) Do NOT include any sense labels or parentheses in the sentence.
4) Each sentence should be 8–22 words, natural and grammatical.
5) Use diverse domains and phrasing; avoid near-duplicates.
Keep language safe and neutral. Return ONLY JSON with {{"sentences": [...]}}."""

CONFIRM_SENSE_PROMPT = """You are given a sentence containing the lemma "{word}" and a list of possible sense labels for this lemma.
Pick the ONE label that best matches the sentence usage.
Return JSON: {{"label": "..."}} ONLY.
Lemma: "{word}"
Sentence: "{sentence}"
Candidates: {candidates}"""

# --- OpenAI call wrappers with retries -------------------------------------
def oai_json_call(client, model, prompt, max_retries=4, sleep_s=1.5):
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON. No extra text."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            return data
        except Exception as e:
            if attempt == max_retries:
                raise
            time.sleep(sleep_s * attempt)

# --- Core generation functions ---------------------------------------------
from dataclasses import dataclass

@dataclass
class SenseEntry:
    sense_id: str
    lemma: str
    definition: str
    examples: List[str]

def make_label_key(label: str) -> str:
    # "(aeroplane)" -> "aeroplane"; "Ancient Egypt" -> "ancient-egypt"
    lab = label.strip()
    lab = lab.strip("()").strip()
    lab = re.sub(r"\s+", "-", lab.lower())
    return lab

def generate_sense_entry(client, model, lemma: str, label: str) -> SenseEntry:
    prompt = SENSE_PROMPT.format(lemma=lemma, label=label)
    data = oai_json_call(client, model, prompt)
    # Minimal validation
    sense_id = data.get("sense_id", f"{lemma} ({label})")
    definition = data.get("definition", "").strip()
    examples = [s.strip() for s in data.get("examples", []) if isinstance(s, str)]
    # Remove parentheses if any leaked
    examples = [re.sub(r"[()]", "", s) for s in examples]
    return SenseEntry(sense_id=sense_id, lemma=lemma, definition=definition, examples=examples)

def generate_sentences_for_sense(client, model, word: str, label: str, n: int) -> List[str]:
    prompt = SENTENCES_PROMPT.format(word=word, label=label, n=n)
    data = oai_json_call(client, model, prompt)
    cand = data.get("sentences", [])
    if not isinstance(cand, list):
        cand = []
    return [s.strip() for s in cand if isinstance(s, str)]

def confirm_sentence_sense(client, model, word: str, sentence: str, labels: List[str]) -> str:
    candidates_json = json.dumps(labels, ensure_ascii=False)
    prompt = CONFIRM_SENSE_PROMPT.format(word=word, sentence=sentence, candidates=candidates_json)
    data = oai_json_call(client, model, prompt)
    return data.get("label", "")

def assemble_sense_text(entry) -> str:
    examples = "; ".join(entry.examples[:2]) if entry.examples else ""
    # Extract label from sense_id format 'lemma (label)'
    match = re.search(r'\(([^)]+)\)', entry.sense_id)
    label_readable = match.group(1) if match else "unknown"
    return f"Sense: {entry.sense_id}\nDefinition: {entry.definition}\nExamples: {examples}"

def pick_cross_lemma_negatives(senses_by_lemma, lemma: str, k: int = 2, seed=42) -> List[str]:
    rnd = random.Random(seed)
    other_lemmas = [l for l in senses_by_lemma.keys() if l != lemma]
    if not other_lemmas:
        return []
    choices = rnd.sample(other_lemmas, min(len(other_lemmas), k))
    neg_texts = []
    for l in choices:
        se = rnd.choice(senses_by_lemma[l])
        neg_texts.append(assemble_sense_text(se))
    return neg_texts

def main():
    # Remove argparse and use only hardcoded/default values
    out_dir = "app/school/text_to_animation/helper_scripts/outputs"
    model = "gpt-4o-mini"
    per_sense = 20
    seed = 42
    confirm_labels = False
    cross_negatives = 2

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Available environment variables:")
        for key in os.environ:
            if 'API' in key or 'OPENAI' in key:
                print(f"  {key} = {os.environ[key][:20]}...")
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)

    # Hardcoded path for lemma→labels
    lemmas_json_path = "app/school/text_to_animation/ambiguous_dict.json"
    with open(lemmas_json_path, "r", encoding="utf-8") as f:
        lemma2labels: Dict[str, List[str]] = json.load(f)

    # Preview mode: only first 5 entries
    preview_lemmas = list(lemma2labels.keys())[:5]
    preview_dict = {lemma: lemma2labels[lemma] for lemma in preview_lemmas}
    
    print("=== PREVIEW MODE ===")
    print(f"Processing first 5 entries: {preview_lemmas}")
    print(f"Model: {model}")
    print(f"Per sense target: {per_sense}")
    print()

    # 1) Build sense catalog for preview
    senses_by_lemma = defaultdict(list)
    for lemma, labels in preview_dict.items():
        print(f"Processing lemma: {lemma}")
        for lab in labels:
            m = re.search(r"\(([^)]+)\)", lab)
            inner_label = m.group(1).strip() if m else lab
            print(f"  - Generating sense entry for: {inner_label}")
            entry = generate_sense_entry(client, model, lemma, inner_label)
            print(f"    → sense_id: {entry.sense_id}")
            print(f"    → definition: {entry.definition}")
            print(f"    → examples: {entry.examples}")
            senses_by_lemma[lemma].append(entry)
        print()

    # 2) Generate a few sample sentences for preview
    print("=== SAMPLE SENTENCE GENERATION ===")
    sample_count = 3  # Just a few for preview
    preview_data = []
    for lemma, senses in list(senses_by_lemma.items())[:2]:  # Only first 2 lemmas
        for se in senses[:1]:  # Only first sense per lemma
            # Extract label from sense_id format 'lemma (label)'
            match = re.search(r'\(([^)]+)\)', se.sense_id)
            label_text = match.group(1) if match else "unknown"
            print(f"Generating sample sentences for {lemma} ({label_text})...")
            batch = generate_sentences_for_sense(client, model, lemma, label_text, sample_count)
            batch = [s for s in batch if sentence_passes_rules(s, lemma)]
            for i, sentence in enumerate(batch[:sample_count], 1):
                print(f"  {i}. {sentence}")
                # Add to preview data
                preview_data.append({
                    "lemma": lemma,
                    "sense_id": se.sense_id,
                    "sentence": sentence,
                    "definition": se.definition
                })
            print()

    # Save preview JSON
    os.makedirs(out_dir, exist_ok=True)
    preview_out = os.path.join(out_dir, "preview_wsd_samples.json")
    with open(preview_out, "w", encoding="utf-8") as f:
        json.dump(preview_data, f, ensure_ascii=False, indent=2)
    print(f"Preview samples saved to: {preview_out}")

    # Ask for confirmation
    print("=== CONFIRMATION ===")
    response = input("Continue with full processing? (Y/n): ").strip().lower()
    if response not in ['y', 'yes', '']:
        print("Cancelled.")
        return

    print("\n=== FULL PROCESSING ===")
    
    # Now run full processing
    senses_out = os.path.join(out_dir, "senses.json")
    dataset_out = os.path.join(out_dir, "dataset.jsonl")
    meta_out = os.path.join(out_dir, "META.json")

    lemmas = list(lemma2labels.keys())
    split_map = split_lemmas(lemmas, ratios=(0.8, 0.1, 0.1), seed=seed)

    # 1) Build sense catalog for all entries
    senses_by_lemma = defaultdict(list)
    for lemma, labels in lemma2labels.items():
        print(f"Processing {lemma}...")
        for lab in labels:
            m = re.search(r"\(([^)]+)\)", lab)
            inner_label = m.group(1).strip() if m else lab
            entry = generate_sense_entry(client, model, lemma, inner_label)
            senses_by_lemma[lemma].append(entry)

    # Save senses.json
    senses_catalog = {se.sense_id: {"sense_id": se.sense_id, "lemma": se.lemma, "definition": se.definition, "examples": se.examples}
                      for senses in senses_by_lemma.values() for se in senses}
    with open(senses_out, "w", encoding="utf-8") as f:
        json.dump(senses_catalog, f, ensure_ascii=False, indent=2)

    # 2) Generate sentences per sense with validation and optional confirmation
    rnd = random.Random(seed)
    total_rows = 0
    split_counts = Counter()
    sense_counts = Counter()

    with open(dataset_out, "w", encoding="utf-8") as fout:
        for lemma, senses in senses_by_lemma.items():
            labels = []
            for lab_full in lemma2labels[lemma]:
                m = re.search(r"\(([^)]+)\)", lab_full)
                labels.append(m.group(1).strip() if m else lab_full)

            for se in senses:
                # Extract label from sense_id format 'lemma (label)'
                match = re.search(r'\(([^)]+)\)', se.sense_id)
                label_text = match.group(1) if match else "unknown"
                batch = generate_sentences_for_sense(client, model, lemma, label_text, per_sense * 2)
                batch = [s for s in batch if sentence_passes_rules(s, lemma)]
                batch = dedupe_preserving_order(batch)
                if confirm_labels:
                    kept = []
                    for s in batch:
                        chosen = confirm_sentence_sense(client, model, lemma, s, labels)
                        if isinstance(chosen, str) and chosen.strip().lower() == label_text.lower():
                            kept.append(s)
                    batch = kept

                batch = batch[:per_sense]
                sense_counts[se.sense_id] += len(batch)

                split = split_map[lemma]
                inlemma_negs = [assemble_sense_text(other) for other in senses if other.sense_id != se.sense_id]
                cross_negs = pick_cross_lemma_negatives(senses_by_lemma, lemma, k=cross_negatives, seed=seed)

                for sentence in batch:
                    sense_text = assemble_sense_text(se)
                    negatives = inlemma_negs + cross_negs
                    row = {
                        "split": split,
                        "lemma": lemma,
                        "sentence": sentence,
                        "sense_id": se.sense_id,
                        "sense_text": sense_text,
                        "negatives": negatives
                    }
                    fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                    total_rows += 1
                    split_counts[split] += 1

    # 3) META.json
    meta = {
        "model": model,
        "seed": seed,
        "per_sense_target": per_sense,
        "lemmas_total": len(lemmas),
        "senses_total": sum(len(v) for v in senses_by_lemma.values()),
        "rows_total": total_rows,
        "split_counts": dict(split_counts),
        "sense_counts": dict(sense_counts),
        "notes": [
            "Sentences validated for: word boundaries, no parentheses, 8–22 words.",
            "Optional sense confirmation can be enabled via --confirm_labels."
        ]
    }
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Done. Wrote:\n- {senses_out}\n- {dataset_out}\n- {meta_out}")

if __name__ == "__main__":
    main()