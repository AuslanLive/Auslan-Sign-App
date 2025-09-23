import json
import os

def load_json_file(filepath):
    """Load and return JSON data from file"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_json_file(filepath, data):
    """Save data to JSON file with proper formatting"""
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def extract_root_word(word):
    """Extract root word by taking everything before the first opening parenthesis"""
    if '(' in word:
        return word.split('(')[0].strip()
    return None

def extract_parenthetical_content(word):
    """Extract content within parentheses"""
    if '(' in word and ')' in word:
        start = word.find('(')
        end = word.find(')')
        if start < end:
            return word[start+1:end].strip()
    return None

def main():
    # Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_word_list_path = 'src/fullWordList.json'
    ambiguous_dict_path = 'app/school/text_to_animation/ambiguous_dict.json'
    
    # Load JSON files
    print("Loading JSON files...")
    full_word_list = load_json_file(full_word_list_path)
    ambiguous_dict = load_json_file(ambiguous_dict_path)
    
    # Convert lists to sets for faster lookup
    full_word_set = set(full_word_list)
    ambiguous_keys_set = set(ambiguous_dict.keys())
    
    # Find root words to add
    root_words_to_add = []
    new_ambiguous_entries = {}
    
    print("Processing words with parentheses...")
    for word in full_word_list:
        if '(' in word:
            root_word = extract_root_word(word)
            if root_word:
                # Check if root word is not already in either dictionary
                if (root_word not in full_word_set and 
                    root_word not in ambiguous_keys_set and
                    root_word not in root_words_to_add):
                    
                    root_words_to_add.append(root_word)
                    print(f"Found new root word: '{root_word}' from '{word}'")
                    
                    # Create ambiguous dictionary entry
                    parenthetical_content = extract_parenthetical_content(word)
                    if parenthetical_content:
                        new_ambiguous_entries[root_word] = [word, parenthetical_content]
                        print(f"  Will add to ambiguous_dict: '{root_word}' -> {new_ambiguous_entries[root_word]}")
    
    # Add new root words to the full word list
    if root_words_to_add:
        print(f"\nAdding {len(root_words_to_add)} new root words...")
        full_word_list.extend(root_words_to_add)
        
        # Sort the list alphabetically
        print("Sorting word list alphabetically...")
        full_word_list.sort()
        
        # Save the updated list
        print("Saving updated word list...")
        save_json_file(full_word_list_path, full_word_list)
        
        print(f"Successfully added {len(root_words_to_add)} root words:")
        for root_word in sorted(root_words_to_add):
            print(f"  - {root_word}")
    
    # Add new entries to ambiguous dictionary
    if new_ambiguous_entries:
        print(f"\nAdding {len(new_ambiguous_entries)} new entries to ambiguous dictionary...")
        ambiguous_dict.update(new_ambiguous_entries)
        
        # Save the updated ambiguous dictionary
        print("Saving updated ambiguous dictionary...")
        save_json_file(ambiguous_dict_path, ambiguous_dict)
        
        print(f"Successfully added {len(new_ambiguous_entries)} ambiguous entries:")
        for key, value in sorted(new_ambiguous_entries.items()):
            print(f"  - '{key}' -> {value}")
    
    if not root_words_to_add and not new_ambiguous_entries:
        print("\nNo new root words or ambiguous entries found to add.")
    
    print("\nScript completed successfully!")

if __name__ == "__main__":
    main()
