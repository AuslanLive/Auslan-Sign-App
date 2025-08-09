import json
from pathlib import Path

# Fixed file paths
path1 = Path("/Users/albert/Documents/GitHub/Auslan-Sign-App/app/school/text_to_animation/helper_scripts/outputs/wsd_test_cases_single.json")
path2 = Path("/Users/albert/Documents/GitHub/Auslan-Sign-App/app/school/text_to_animation/helper_scripts/outputs/wsd_corrected_test_cases.json")
failed_words_path = Path("app/school/text_to_animation/helper_scripts/outputs/failed_words.txt")

# Output path
output_path = '/Users/albert/Documents/GitHub/Auslan-Sign-App/app/school/text_to_animation/helper_scripts/outputs/wsd_test_cases.json'

# --- Load failed words ---
with open(failed_words_path, "r", encoding="utf-8") as f:
    failed_words = set(line.strip().lower() for line in f if line.strip())

print(f"Loaded {len(failed_words)} failed words to remove")

# --- Load JSON files ---
with open(path1, "r", encoding="utf-8") as f:
    data1 = json.load(f)

with open(path2, "r", encoding="utf-8") as f:
    data2 = json.load(f)

print(f"Loaded {len(data1)} entries from path1")
print(f"Loaded {len(data2)} entries from path2")

# --- Remove failed words from data1 ---
deleted_count = 0
print("\n=== DELETION OPERATIONS ===")

filtered_data1 = []
for entry in data1:
    if entry["ambiguous_word"].lower() in failed_words:
        print(f"DELETED: '{entry['ambiguous_word']}' - removing failed word")
        deleted_count += 1
    else:
        filtered_data1.append(entry)

print(f"Kept {len(filtered_data1)} entries from path1 after deletions")

# --- Add all entries from data2 ---
added_count = len(data2)
print(f"\n=== ADDITION OPERATIONS ===")
print(f"ADDING: All {added_count} entries from path2")

# Show breakdown by ambiguous word for data2
word_counts = {}
for entry in data2:
    word = entry["ambiguous_word"]
    word_counts[word] = word_counts.get(word, 0) + 1

print("Breakdown of entries being added:")
for word, count in sorted(word_counts.items()):
    print(f"  - {word}: {count} entries")

# --- Combine the lists ---
merged_list = filtered_data1 + data2

# --- Save merged output ---
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(merged_list, f, ensure_ascii=False, indent=2)

print(f"\n=== SUMMARY ===")
print(f"Total entries deleted from path1: {deleted_count}")
print(f"Total entries kept from path1: {len(filtered_data1)}")
print(f"Total entries added from path2: {added_count}")
print(f"Final total entries: {len(merged_list)}")
print(f"Merged JSON saved to: {output_path}")

# Show final breakdown by ambiguous word
final_word_counts = {}
for entry in merged_list:
    word = entry["ambiguous_word"]
    final_word_counts[word] = final_word_counts.get(word, 0) + 1

print(f"\nFinal breakdown (words with multiple entries):")
for word, count in sorted(final_word_counts.items()):
    if count > 1:
        print(f"  - {word}: {count} entries")