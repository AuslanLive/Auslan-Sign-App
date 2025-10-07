import json
import os
from datetime import datetime

def load_json_file(filepath):
    """Load and return JSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file - {filepath}")
        return None

def check_missing_poses():
    """Compare clarified definitions with Firebase pose files and find missing entries."""
    
    # File paths
    clarified_definitions_path = r"C:\Users\alber\Downloads\clarified_definitions_openai.json"
    firebase_poses_path = r"output\firebase_pose_files_20250923_182046.json"
    
    # Load JSON files
    clarified_definitions = load_json_file(clarified_definitions_path)
    firebase_poses = load_json_file(firebase_poses_path)
    
    if clarified_definitions is None or firebase_poses is None:
        return
    
    # Extract Firebase pose filenames from the "files" array
    firebase_entries = set()
    if isinstance(firebase_poses, dict) and "files" in firebase_poses:
        firebase_entries.update(firebase_poses["files"])
        print(f"Found {len(firebase_entries)} Firebase pose files")
    else:
        print("Error: Firebase data doesn't have expected 'files' array structure")
        return
    
    # Debug: Show some Firebase entries
    firebase_list = list(firebase_entries)
    print(f"Sample Firebase entries: {firebase_list[:10]}")
    
    # Check for missing entries
    missing_entries = []
    
    for word, definition in clarified_definitions.items():
        # Format as "word (definition).pose"
        formatted_entry = f"{word} ({definition}).pose"
        
        print(f"Checking: {formatted_entry}")
        
        # Check if this formatted entry exists in Firebase
        if formatted_entry not in firebase_entries:
            missing_entries.append(formatted_entry)
            print(f"Missing: {formatted_entry}")
        else:
            print(f"Found: {formatted_entry}")
    
    # Save missing entries to output file
    if missing_entries:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"missing_poses_{timestamp}.json"
        output_path = os.path.join("src", "scripts", "wordDisambiguation", output_filename)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(missing_entries, output_file, indent=2, ensure_ascii=False)
        
        print(f"\nFound {len(missing_entries)} missing entries.")
        print(f"Results saved to: {output_path}")
    else:
        print("No missing entries found.")

if __name__ == "__main__":
    check_missing_poses()
