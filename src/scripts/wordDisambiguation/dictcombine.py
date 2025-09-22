import json
import os

def load_json_file(filepath):
    """Load and return JSON data from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{filepath}'")
        return None

def save_json_file(filepath, data):
    """Save data to JSON file with proper formatting"""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving file '{filepath}': {e}")
        return False

def combine_dictionaries():
    """Combine ambiguous dictionary keys with firebase filenames"""
    
    # Define file paths relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    firebase_path = os.path.join(script_dir, '..', '..', '..', 'firebase_filenames.json')
    ambiguous_path = os.path.join(script_dir, '..', '..', '..', 'app', 'school', 'text_to_animation', 'ambiguous_dict.json')
    
    # Load both files
    print("Loading firebase_filenames.json...")
    firebase_filenames = load_json_file(firebase_path)
    if firebase_filenames is None:
        return
    
    print("Loading ambiguous_dict.json...")
    ambiguous_dict = load_json_file(ambiguous_path)
    if ambiguous_dict is None:
        return
    
    # Get keys from ambiguous dictionary
    ambiguous_keys = list(ambiguous_dict.keys())
    
    # Find keys that aren't already in firebase filenames
    existing_keys = [key for key in ambiguous_keys if key in firebase_filenames]
    new_keys = [key for key in ambiguous_keys if key not in firebase_filenames]
    
    # Display summary
    print(f"\nSummary:")
    print(f"Total ambiguous keys: {len(ambiguous_keys)}")
    print(f"Already in firebase_filenames: {len(existing_keys)}")
    print(f"New keys to be added: {len(new_keys)}")
    
    if new_keys:
        print(f"\nNew keys that will be added:")
        for key in sorted(new_keys):
            print(f"  - {key}")
        
        # Ask for confirmation
        response = input(f"\nDo you want to add these {len(new_keys)} keys to firebase_filenames.json? (y/n): ")
        
        if response.lower() in ['y', 'yes']:
            # Combine and sort
            updated_filenames = sorted(firebase_filenames + new_keys)
            
            # Save updated file
            if save_json_file(firebase_path, updated_filenames):
                print(f"\nSuccess! Added {len(new_keys)} new keys to firebase_filenames.json")
            else:
                print("\nFailed to save updated file")
        else:
            print("\nOperation cancelled")
    else:
        print("\nNo new keys to add - all ambiguous keys already exist in firebase_filenames.json")

def preview_only():
    """Show what would be added without making changes"""
    
    # Define file paths relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    firebase_path = os.path.join(script_dir, '..', '..', '..', 'firebase_filenames.json')
    ambiguous_path = os.path.join(script_dir, '..', '..', '..', 'app', 'school', 'text_to_animation', 'ambiguous_dict.json')
    
    # Load both files
    firebase_filenames = load_json_file(firebase_path)
    ambiguous_dict = load_json_file(ambiguous_path)
    
    if firebase_filenames is None or ambiguous_dict is None:
        return
    
    ambiguous_keys = list(ambiguous_dict.keys())
    existing_keys = [key for key in ambiguous_keys if key in firebase_filenames]
    new_keys = [key for key in ambiguous_keys if key not in firebase_filenames]
    
    print(f"Preview Mode - No changes will be made")
    print(f"=" * 50)
    print(f"Total ambiguous keys: {len(ambiguous_keys)}")
    print(f"Already in firebase_filenames: {len(existing_keys)}")
    print(f"Would be added: {len(new_keys)}")
    
    if existing_keys:
        print(f"\nKeys already present:")
        for key in sorted(existing_keys)[:10]:  # Show first 10
            print(f"  - {key}")
        if len(existing_keys) > 10:
            print(f"  ... and {len(existing_keys) - 10} more")
    
    if new_keys:
        print(f"\nKeys that would be added:")
        for key in sorted(new_keys):
            print(f"  - {key}")

if __name__ == "__main__":
    print("Firebase Filenames and Ambiguous Dictionary Combiner")
    print("=" * 55)
    
    mode = input("Choose mode:\n1. Preview only (no changes)\n2. Combine files\nEnter choice (1 or 2): ")
    
    if mode == "1":
        preview_only()
    elif mode == "2":
        combine_dictionaries()
    else:
        print("Invalid choice. Please run the script again and choose 1 or 2.")