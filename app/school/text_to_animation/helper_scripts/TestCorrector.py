import json
import time
from openai import OpenAI

client = OpenAI(api_key='')

def load_failed_words(txt_file_path):
    """Load failed words from txt file into a set for fast lookup"""
    with open(txt_file_path, "r") as f:
        failed_words = set(word.strip() for word in f.readlines())
    return failed_words

def generate_sentence(word, sense, senses):
    """Generate a new sentence using the same prompt as OpenAISentenceCreator.py"""
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
        
        # Clean raw output and extract json data
        if content.startswith('```json'):
            # Remove ```json from the start and ``` from the end
            content = content[7:]  # Remove '```json\n'
            if content.endswith('```'):
                content = content[:-3]  # Remove final '```'
            content = content.strip()
        
        # Parse and return the result
        example = json.loads(content)
        return example

    except Exception as e:
        print(f"[x] Failed to process {word} ({sense}): {e}")
        return None

def main():
    # Define file paths
    json_file_path = "app/school/text_to_animation/helper_scripts/outputs/wsd_test_cases_single.json"
    txt_file_path = "app/school/text_to_animation/helper_scripts/outputs/failed_words.txt"
    output_file_path = "app/school/text_to_animation/helper_scripts/outputs/wsd_corrected_test_cases.json"
    
    # Load data
    with open(json_file_path, "r") as f:
        wsd_data = json.load(f)
    
    failed_words = load_failed_words(txt_file_path)
    
    corrected_data = []
    
    # Process each entry in the JSON file
    for entry in wsd_data:
        word = entry.get("ambiguous_word", "")
        
        # Check if the word is in the failed words list
        if word in failed_words:
            print(f"Processing failed word: {word}")
            
            # Get the sense and options from the original entry
            sense = entry.get("answer", "")
            senses = entry.get("options", [])
            
            # Generate a new sentence
            new_example = generate_sentence(word, sense, senses)
            
            if new_example:
                corrected_data.append(new_example)
                print(f"[✓] {word} → {sense} (corrected)")
            
            time.sleep(1)  # Optional: avoid rate limits
    
    # Save the corrected dataset
    with open(output_file_path, "w") as f:
        json.dump(corrected_data, f, indent=2)
    
    print(f"\nCorrected {len(corrected_data)} entries and saved to {output_file_path}")

if __name__ == "__main__":
    main()