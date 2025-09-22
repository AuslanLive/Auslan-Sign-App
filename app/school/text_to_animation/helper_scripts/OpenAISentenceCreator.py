import json
import time
from openai import OpenAI

client = OpenAI(api_key='')

# Load your ambiguous word definitions
with open("app/school/text_to_animation/ambiguous_dict.json", "r") as f:
    ambiguous_dict = json.load(f)

output_data = []

for word, senses in ambiguous_dict.items():
    for sense in senses:
        prompt = f"""
You are an expert linguistic AI helping create test data for a word sense disambiguation (WSD) task.

## Objective:
Write **one short, natural English sentence** using the ambiguous word **"{word}"**, such that **only one of its meanings is clearly correct**. Avoid creating sentences that could fit multiple interpretations.

## Rules:
- The sentence **must only support the intended sense**: "{sense}"
- **Do not include the sense label** in the sentence.
- **Avoid ambiguity** — make it impossible to choose any of the other senses.
- Keep the sentence clear, simple, and real-world.
- Output in **valid JSON format** as shown below (use double quotes, no extra commentary).
- The sentence must include the exact token "{word}" as written (case-insensitive). Do not use inflections (e.g., for forget: forgot, forgetting, forgets are forbidden).
- The sentence must contain "{word}" as a standalone word boundary (not part of another word).

## Options:
{json.dumps(senses)}

## Desired Format:
{{
  "ambiguous_word": "{word}",
  "options": {json.dumps(senses)},
  "test_sentence": "...",
  "answer": "{sense}"
}}

## Examples:

Example 1:
{{
  "ambiguous_word": "flat",
  "options": ["flat (apartment)", "flat (level)", "flat (battery)"],
  "test_sentence": "She moved into a small flat near the university.",
  "answer": "flat (apartment)"
}}

Example 2:
{{
  "ambiguous_word": "fly",
  "options": ["fly (trousers)", "fly (aeroplane)", "fly (insect)", "fly (flap wings)"],
  "test_sentence": "A fly kept buzzing around the fruit bowl.",
  "answer": "fly (insect)"
}}

## Now write a new example using the following sense:
"{sense}"
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a linguist helping design training examples for word sense disambiguation."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            
            # clean raw output and extract json data
            if content.startswith('```json'):
                # Remove ```json from the start and ``` from the end
                content = content[7:]  # Remove '```json\n'
                if content.endswith('```'):
                    content = content[:-3]  # Remove final '```'
                content = content.strip()
            
            # Parse and store the result
            example = json.loads(content)
            output_data.append(example)
            print(f"[✓] {word} → {sense}")

            time.sleep(1)  # Optional: avoid rate limits

        except Exception as e:
            print(f"[x] Failed to process {word} ({sense}): {e}")

# Save the full dataset
with open("app/school/text_to_animation/helper_scripts/outputs/wsd_test_cases.json", "w") as f:
    json.dump(output_data, f, indent=2)
