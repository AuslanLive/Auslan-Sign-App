import json
import os

def compare_and_update_word_lists():
    """
    Compare ambiguous_dict.json values with fullWordList.json and add missing entries.
    Sort the final list alphabetically.
    """
    # Define file paths (adjust paths as needed)
    ambiguous_dict_path = 'app/school/text_to_animation/ambiguous_dict.json'
    full_word_list_path = 'src/fullWordList.json'
    
    try:
        # Load ambiguous_dict.json
        with open(ambiguous_dict_path, 'r', encoding='utf-8') as f:
            ambiguous_dict = json.load(f)
        
        # Load fullWordList.json
        with open(full_word_list_path, 'r', encoding='utf-8') as f:
            full_word_list = json.load(f)
        
        # Extract all values from ambiguous_dict
        ambiguous_values = set()
        for key, value in ambiguous_dict.items():
            if isinstance(value, list):
                ambiguous_values.update(value)
            else:
                ambiguous_values.add(value)
        
        # Convert full_word_list to set for faster lookup
        current_words = set(full_word_list)
        
        # Find missing words
        missing_words = ambiguous_values - current_words
        
        if missing_words:
            # Preview changes
            sorted_missing = sorted(missing_words)
            print(f"\n=== PREVIEW ===")
            print(f"Found {len(missing_words)} missing words that will be added:")
            print(f"Current fullWordList.json size: {len(full_word_list)} words")
            print(f"After addition: {len(full_word_list) + len(missing_words)} words")
            print(f"\nWords to be added:")
            for word in sorted_missing:
                print(f"  + {word}")
            
            # Ask for confirmation
            print(f"\n=== CONFIRMATION ===")
            confirm = input(f"Do you want to add these {len(missing_words)} words to fullWordList.json? (Y/N): ").strip().upper()
            
            if confirm == 'Y':
                # Add missing words to the list
                full_word_list.extend(missing_words)
                
                # Sort alphabetically
                full_word_list.sort()
                
                # Save updated list
                with open(full_word_list_path, 'w', encoding='utf-8') as f:
                    json.dump(full_word_list, f, indent=2, ensure_ascii=False)
                
                print(f"\n✅ Successfully added {len(missing_words)} words and sorted the list.")
                print(f"fullWordList.json now contains {len(full_word_list)} words.")
            else:
                print("\n❌ Operation cancelled. No changes were made.")
        else:
            print("✅ No missing words found. fullWordList.json is already complete.")
    
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format - {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    compare_and_update_word_lists()
