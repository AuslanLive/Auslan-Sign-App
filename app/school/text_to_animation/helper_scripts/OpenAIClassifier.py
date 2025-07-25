from openai import OpenAI
import json
import time

client = OpenAI(api_key='')

# Load your file
with open("/Users/albert/Downloads/clarified_definitions.json", "r") as f:
    data = json.load(f)

clarified = {}

for word, definitions in data.items():
    prompt = f"""
    Given the following definitions for the word "{word}", write one short descriptor that best summarizes the general meaning. Focus on core meanings. Avoid duplicates or over-specific examples. Be as concise as possible, while still clearly defining the word, please keep these definitions to just 1 or 2 words maximum.

    Definitions:
    {chr(10).join(f"- {d}" for d in definitions)}
    """

    try:
        response = client.chat.completions.create(
            model="o3",
            messages=[
                {"role": "system", "content": "You are an Auslan linguist helping clarify ambiguous sign meanings."},
                {"role": "user", "content": prompt}
            ],
        )

        summary = response.choices[0].message.content.strip()
        clarified[word] = summary
        print(f"[{word}] → {summary}")
        time.sleep(1)  # avoid rate limiting

    except Exception as e:
        print(f"Error for {word}: {e}")
        clarified[word] = "N/A"

# Save results
with open("/Users/albert/Downloads/clarified_definitions_openai.json", "w") as f:
    json.dump(clarified, f, indent=4)
