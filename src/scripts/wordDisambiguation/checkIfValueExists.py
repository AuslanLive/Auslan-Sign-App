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

def main():
    # Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_word_list_path = 'src/fullWordList.json'
    ambiguous_dict_path = 'app/school/text_to_animation/ambiguous_dict.json'
    
    # Load JSON files
    print("Loading JSON files...")
    full_word_list = load_json_file(full_word_list_path)
    ambiguous_dict = load_json_file(ambiguous_dict_path)
    
    # Convert full word list to set for faster lookup
    full_word_set = set(full_word_list)
    
    # Track changes
    removed_values = []
    keys_processed = 0
    
    print("Checking values in ambiguous dictionary...")
    
    # Process each key in ambiguous dictionary
    for key, values in ambiguous_dict.items():
        keys_processed += 1
        original_count = len(values)
        
        # Filter out values that don't exist in full word list
        valid_values = []
        for value in values:
            if value in full_word_set:
                valid_values.append(value)
            else:
                removed_values.append((key, value))
                print(f"  Removing '{value}' from key '{key}' (not found in full word list)")
        
        # Update the dictionary with valid values only
        ambiguous_dict[key] = valid_values
        
        # Report if values were removed from this key
        if len(valid_values) < original_count:
            removed_count = original_count - len(valid_values)
            print(f"  Key '{key}': removed {removed_count} value(s), {len(valid_values)} remaining")
    
    # Save updated ambiguous dictionary if changes were made
    if removed_values:
        print(f"\nSaving updated ambiguous dictionary...")
        save_json_file(ambiguous_dict_path, ambiguous_dict)
        
        print(f"\nSummary:")
        print(f"  Processed {keys_processed} keys")
        print(f"  Removed {len(removed_values)} invalid values total")
        print(f"  Updated ambiguous dictionary saved")
        
        if len(removed_values) <= 20:  # Show details if not too many
            print(f"\nRemoved values:")
            for key, value in removed_values:
                print(f"  '{key}' -> '{value}'")
        else:
            print(f"\nFirst 20 removed values:")
            for key, value in removed_values[:20]:
                print(f"  '{key}' -> '{value}'")
            print(f"  ... and {len(removed_values) - 20} more")
    else:
        print(f"\nNo invalid values found!")
        print(f"All values in ambiguous dictionary exist in the full word list.")
        print(f"Processed {keys_processed} keys successfully.")
    
    print("\nScript completed successfully!")

if __name__ == "__main__":
    main()
