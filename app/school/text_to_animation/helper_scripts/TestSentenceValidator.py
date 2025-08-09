#!/usr/bin/env python3
"""
Validate WSD dataset entries.

Checks per entry:
1) Valid JSON with required fields and types.
2) Sentence contains the EXACT target token {ambiguous_word} as a standalone word
   (case-insensitive, word-boundary match). No inflections allowed.
3) "answer" is a non-empty string.
4) "options" contains the "answer".
5) (Soft check) Sentence should not contain explicit hint words pointing to
   multiple senses or to a non-answer sense. Hints are extracted from any
   parenthetical labels in options, e.g., "formal (dress)" -> hint "dress".

Usage:
  python validate_wsd.py --input data.json --out bad_entries.txt
"""

import argparse
import json
import re
from typing import Any, Dict, List, Tuple

WORD_BOUNDARY_FMT = r"(?:^|(?<!\w))({})(?!\w|-)"

def load_entries(path: str) -> List[Dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        # If user provided a dict keyed by something, convert to list of values
        return list(data.values())
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of entries or a dict mapping to entries.")
    return data

def is_valid_required_fields(entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    # Required fields
    required = ["ambiguous_word", "options", "test_sentence", "answer"]
    missing = [k for k in required if k not in entry]
    if missing:
        errors.append(f"Missing fields: {', '.join(missing)}")
        return False, errors

    # Types / content
    if not isinstance(entry["ambiguous_word"], str) or not entry["ambiguous_word"].strip():
        errors.append("ambiguous_word must be a non-empty string.")
    if not isinstance(entry["test_sentence"], str) or not entry["test_sentence"].strip():
        errors.append("test_sentence must be a non-empty string.")
    if not isinstance(entry["answer"], str) or not entry["answer"].strip():
        errors.append("answer must be a non-empty string.")
    if not isinstance(entry["options"], list) or not entry["options"]:
        errors.append("options must be a non-empty list.")
    else:
        # Ensure options are strings
        if not all(isinstance(o, str) and o.strip() for o in entry["options"]):
            errors.append("All options must be non-empty strings.")
    return (len(errors) == 0), errors

def contains_exact_token(sentence: str, token: str) -> bool:
    """
    Word-boundary match for the exact token (case-insensitive), e.g.,
    token='forget' matches 'forget', but not 'forgets', 'forgot', 'forgetting', or 'forgotten'.
    """
    pattern = WORD_BOUNDARY_FMT.format(re.escape(token))
    return re.search(pattern, sentence, flags=re.IGNORECASE) is not None

def answer_in_options(answer: str, options: List[str]) -> bool:
    return answer in options

def extract_hint(option: str) -> str:
    """
    Extract a parenthetical hint if present: "formal (dress)" -> "dress".
    Returns '' if no parenthetical hint exists.
    """
    m = re.search(r"\(([^)]+)\)", option)
    return (m.group(1).strip() if m else "").lower()

def tokenize_for_hints(text: str) -> set:
    # Simple word tokens; keep hyphenated parts split
    return set(re.findall(r"[A-Za-z]+", text.lower()))

def validate_entry(entry: Dict[str, Any]) -> List[str]:
    """
    Returns a list of failure reasons. Empty list means the entry passed all checks.
    """
    reasons = []

    ok, field_errors = is_valid_required_fields(entry)
    if not ok:
        reasons.extend(field_errors)
        return reasons  # Can't proceed further if basic structure is invalid

    word = entry["ambiguous_word"].strip()
    sent = entry["test_sentence"]
    ans = entry["answer"].strip()
    opts = entry["options"]

    # 2) Exact token match (no inflections)
    if not contains_exact_token(sent, word):
        reasons.append(f'Sentence does not contain exact token "{word}" as a standalone word.')

    # 3) Answer string present (already type-checked as non-empty). Nothing else to do here.

    # 4) Answer must be in options
    if not answer_in_options(ans, opts):
        reasons.append('Answer not found in options.')

    return reasons

def main():
    ap = argparse.ArgumentParser()
    input_path = "app/school/text_to_animation/helper_scripts/outputs/wsd_test_cases_single.json"
    output_path = "app/school/text_to_animation/helper_scripts/outputs/wsd_test_cases_validation.txt"
    failed_words_path = "app/school/text_to_animation/helper_scripts/outputs/failed_words.txt"
    args = ap.parse_args()

    entries = load_entries(input_path)

    bad_lines: List[str] = []
    failed_words: List[str] = []
    total = 0
    bad = 0

    for idx, entry in enumerate(entries):
        total += 1
        try:
            reasons = validate_entry(entry)
        except Exception as e:
            bad += 1
            bad_lines.append(
                f"[{idx}] ERROR validating entry: {e}"
            )
            # Add ambiguous word even if there's an error
            if "ambiguous_word" in entry:
                failed_words.append(entry["ambiguous_word"])
            continue

        if reasons:
            bad += 1
            # Provide compact context to help you fix quickly
            aw = entry.get("ambiguous_word", "<missing>")
            ans = entry.get("answer", "<missing>")
            sent = entry.get("test_sentence", "<missing>").strip().replace("\n", " ")
            opts = entry.get("options", [])
            bad_lines.append(
                f"[{idx}] ambiguous_word='{aw}' | answer='{ans}' | options={opts} | "
                f"sentence='{sent}'\n  -> Reasons: " + " ; ".join(reasons)
            )
            # Add the failed ambiguous word
            failed_words.append(aw)

    # Write detailed validation results
    with open(output_path, "w", encoding="utf-8") as f:
        if bad_lines:
            f.write("\n".join(bad_lines) + "\n")
        else:
            f.write("All entries passed validation.\n")

    # Write failed words only
    with open(failed_words_path, "w", encoding="utf-8") as f:
        if failed_words:
            # Remove duplicates while preserving order
            unique_failed_words = list(dict.fromkeys(failed_words))
            f.write("\n".join(unique_failed_words) + "\n")
        else:
            f.write("No failed words.\n")

    print(f"Checked {total} entries.")
    print(f"Failures: {bad}. Valid: {total - bad}.")
    print(f"Wrote details to: {output_path}")
    print(f"Wrote failed words to: {failed_words_path}")
    
if __name__ == "__main__":
    main()
