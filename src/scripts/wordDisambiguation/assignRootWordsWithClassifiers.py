import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add the project root to the Python path to import Firebase utilities
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Load environment variables from the .env file (same as firebaseRename.py)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app', '.env'))

# Import Firebase utilities
try:
    import firebase_admin
    from firebase_admin import credentials, storage
except ImportError:
    print("Error: firebase_admin not installed. Please install with: pip install firebase-admin")
    sys.exit(1)

def load_json_file(filepath):
    """Load and return JSON data from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file - {filepath}")
        return None

def initialize_firebase():
    """Initialize Firebase Admin SDK using environment variables (same as firebaseRename.py)"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        print("Firebase already initialized")
    except ValueError:
        # Retrieve credentials from environment variables (same as firebaseRename.py)
        firebase_credentials = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
        }

        # Check if any credential is missing
        if None in firebase_credentials.values():
            print("Error: Firebase credentials not found in .env file.")
            print("Please ensure your .env file contains all required Firebase credentials.")
            return None

        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'storageBucket': 'auslan-194e5.appspot.com'})
        print("Firebase initialized with environment credentials")
    
    return storage.bucket()

def get_firebase_files_with_extension(bucket, extension=".pose"):
    """Get list of files in Firebase storage with specified extension."""
    try:
        blobs = bucket.list_blobs()
        files = [blob.name for blob in blobs if blob.name.endswith(extension)]
        return files
    except Exception as e:
        print(f"Error getting Firebase files: {e}")
        return []

def copy_and_rename_file(bucket, source_filename, new_filename):
    """Copy a file in Firebase storage and rename it."""
    try:
        # Get the source blob
        source_blob = bucket.blob(source_filename)
        
        if not source_blob.exists():
            print(f"Warning: Source file {source_filename} does not exist in Firebase")
            return False
        
        # Copy to new blob with new name
        new_blob = bucket.blob(new_filename)
        new_blob.upload_from_string(source_blob.download_as_bytes())
        
        print(f"Successfully copied {source_filename} to {new_filename}")
        return True
        
    except Exception as e:
        print(f"Error copying {source_filename} to {new_filename}: {e}")
        return False

def sanitize_filename(filename):
    """Sanitize filename to remove invalid characters."""
    # Remove or replace characters that might be problematic in filenames
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename.strip()

def save_firebase_filenames_to_txt(bucket, output_dir="output"):
    """Save all Firebase filenames to a text file."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all files from Firebase
        print("Fetching all files from Firebase storage...")
        blobs = bucket.list_blobs()
        filenames = [blob.name for blob in blobs]
        
        # Sort filenames for better readability
        filenames.sort()
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(output_dir, f"firebase_filenames_{timestamp}.txt")
        
        # Write to file
        with open(output_filename, 'w', encoding='utf-8') as file:
            file.write(f"Firebase Storage Filenames\n")
            file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Total files: {len(filenames)}\n")
            file.write("=" * 50 + "\n\n")
            
            for filename in filenames:
                file.write(f"{filename}\n")
        
        print(f"Successfully saved {len(filenames)} filenames to: {output_filename}")
        return output_filename
        
    except Exception as e:
        print(f"Error saving Firebase filenames to file: {e}")
        return None

def main():
    print("Auslan Sign App - Word Disambiguation with Classifiers")
    print("=" * 60)
    
    # Initialize Firebase first
    bucket = initialize_firebase()
    if not bucket:
        print("Failed to initialize Firebase. Exiting.")
        return
    
    # Ask if user wants to save Firebase filenames to file
    while True:
        response = input("\nDo you want to save all Firebase filenames to a text file? (Y/N): ").strip().upper()
        if response in ['Y', 'YES']:
            save_firebase_filenames_to_txt(bucket)
            break
        elif response in ['N', 'NO']:
            break
        else:
            print("Please enter Y or N.")
    
    # Load the clarified definitions
    clarified_definitions_path = r"C:\Users\alber\Downloads\clarified_definitions_openai.json"
    clarified_definitions = load_json_file(clarified_definitions_path)
    
    if not clarified_definitions:
        print("Failed to load clarified definitions. Exiting.")
        return
    
    # show small preview of clarified definitions
    print(f"Loaded {len(clarified_definitions)} clarified definitions. Sample:")
    sample_items = list(clarified_definitions.items())[:10]
    for word, definition in sample_items:
        print(f"  - {word}: {definition}")
    
    # Load the full word list
    full_word_list_path = 'src/fullWordList.json'
    full_word_list = load_json_file(full_word_list_path)
    
    # show small preview of full word list
    if full_word_list:
        print(f"Loaded {len(full_word_list)} words from full word list. Sample:")
        print(", ".join(full_word_list[:10]) + ("..." if len(full_word_list) > 10 else ""))
    
    if not full_word_list:
        print("Failed to load full word list. Exiting.")
        return
    
    # Convert word list to set for faster lookup
    word_set = set(full_word_list)
    
    # Get existing .pose files from Firebase
    print("Fetching existing .pose files from Firebase...")
    existing_pose_files = get_firebase_files_with_extension(bucket, ".pose")
    print(f"Found {len(existing_pose_files)} .pose files in Firebase.")
    existing_pose_names = {file.replace('.pose', '') for file in existing_pose_files}
    
    # show small preview of existing pose names
    print("Sample of existing .pose files:")
    sample_pose_names = list(existing_pose_names)[:10]
    for name in sample_pose_names:
        print(f"  - {name}")
    
    # Find matches and prepare operations
    operations = []
    
    for key, value in clarified_definitions.items():
        # print if key exists in firebase
        print(f"  - {key} exists in Firebase: {key in existing_pose_names}")
        if key in word_set and key in existing_pose_names:
            source_filename = f"{key}.pose"
            print(f"Found matching file: {source_filename}")
            new_filename = sanitize_filename(f"{key} ({value}).pose")
            operations.append((source_filename, new_filename, key, value))
    
    # Show preview
    print(f"\nPreview of operations to be performed:")
    print("=" * 60)
    
    if not operations:
        print("No matching files found for renaming operations.")
        return
    
    for i, (source, target, word, definition) in enumerate(operations, 1):
        print(f"{i:3d}. {source} → {target}")
    
    print(f"\nTotal operations: {len(operations)}")
    
    # Ask for confirmation
    print("\nThis will copy and rename the files in Firebase storage.")
    print("The original files will remain unchanged.")
    
    while True:
        response = input("\nDo you want to proceed? (Y/N): ").strip().upper()
        if response in ['Y', 'YES']:
            break
        elif response in ['N', 'NO']:
            print("Operation cancelled.")
            return
        else:
            print("Please enter Y or N.")
    
    # Perform operations
    print("\nPerforming operations...")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, (source_filename, new_filename, word, definition) in enumerate(operations, 1):
        print(f"[{i}/{len(operations)}] Processing: {word}")
        
        if copy_and_rename_file(bucket, source_filename, new_filename):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\nOperation Summary:")
    print("=" * 60)
    print(f"Total operations attempted: {len(operations)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print(f"\nSome operations failed. Please check the error messages above.")
    else:
        print(f"\nAll operations completed successfully!")

if __name__ == "__main__":
    main()
