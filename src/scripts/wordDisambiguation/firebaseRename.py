from ast import Or
import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials, storage as firebase_storage
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app', '.env'))

def initialize_firebase():
    """Initialize Firebase Admin SDK using environment variables"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        print("Firebase already initialized")
    except ValueError:
        # Retrieve credentials from environment variables (same as pose_video_creator.py)
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
    
    return firebase_storage.bucket()

def batch_rename_files(rename_mapping):
    """Rename multiple files using a dictionary mapping"""
    bucket = initialize_firebase()
    if not bucket:
        return
    
    success_count = 0
    failure_count = 0
    
    print(f"Starting batch rename of {len(rename_mapping)} files...")
    print("-" * 50)
    
    for old_name, new_name in rename_mapping.items():
        print(f"Renaming: {old_name} -> {new_name}")
        
        try:
            # Get the source blob
            source_blob = bucket.blob(old_name)
            
            # Check if source file exists
            if not source_blob.exists():
                print(f"Error: File '{old_name}' does not exist")
                failure_count += 1
                continue
            
            # Check if destination file already exists
            destination_blob = bucket.blob(new_name)
            if destination_blob.exists():
                print(f"Error: File '{new_name}' already exists")
                failure_count += 1
                continue
            
            # Copy the file to the new name
            bucket.copy_blob(source_blob, bucket, new_name)
            print(f"File copied from '{old_name}' to '{new_name}'")
            
            # Delete the original file
            source_blob.delete()
            print(f"Original file '{old_name}' deleted")
            
            print(f"Successfully renamed '{old_name}' to '{new_name}'")
            success_count += 1
            
        except Exception as e:
            print(f"Error renaming '{old_name}': {e}")
            failure_count += 1
        
        print()  # Add spacing between operations
    
    print(f"Batch rename completed:")
    print(f"Success: {success_count}")
    print(f"Failures: {failure_count}")

def replace_substring(substr, replacement=" "):
    """Replace specified substring with replacement string in all Firebase Storage filenames"""
    bucket = initialize_firebase()
    if not bucket:
        return
    
    try:
        blobs = bucket.list_blobs()
        
        rename_mapping = {}
        delete_mapping = {}
        
        # Find all files with substr in their names
        for blob in blobs:
            if substr in blob.name:
                new_name = blob.name.replace(substr, replacement)
                
                # Check if target file already exists
                target_blob = bucket.blob(new_name)
                if target_blob.exists():
                    delete_mapping[blob.name] = new_name
                else:
                    rename_mapping[blob.name] = new_name
        
        if rename_mapping or delete_mapping:
            print(f"Found {len(rename_mapping)} files with '{substr}' to be renamed")
            print(f"Found {len(delete_mapping)} files with '{substr}' to be deleted (target exists)")
            print("Files to be renamed:")
            print("-" * 60)
            for old, new in rename_mapping.items():
                print(f"  {old}")
                print(f"  -> {new}")
                print()
            
            print("Files to be deleted (target already exists):")
            print("-" * 60)
            for old, target in delete_mapping.items():
                print(f"  DELETE: {old}")
                print(f"  (target exists: {target})")
                print()
            
            # Ask for confirmation
            response = input(f"Proceed with replacing '{substr}' with '{replacement}'? (y/N): ")
            if response.lower() == 'y':
                # Process deletions first
                if delete_mapping:
                    print("Deleting files where target already exists...")
                    for old_name, target_name in delete_mapping.items():
                        try:
                            source_blob = bucket.blob(old_name)
                            source_blob.delete()
                            print(f"Deleted '{old_name}' (target '{target_name}' already exists)")
                        except Exception as e:
                            print(f"Error deleting '{old_name}': {e}")
                
                # Process renames
                if rename_mapping:
                    batch_rename_files(rename_mapping)
            else:
                print("Operation cancelled")
        else:
            print(f"No files found with '{substr}' in their names")
            
    except Exception as e:
        print(f"Error searching for files with {substr}: {e}")

def download_all_files():
    """Download all files from Firebase Storage to local machine"""
    bucket = initialize_firebase()
    if not bucket:
        return
    
    # Set the local download path
    local_path = '/Users/albert/Documents/pose files'
    
    try:
        # Create the directory if it doesn't exist
        os.makedirs(local_path, exist_ok=True)
        print(f"Download directory: {local_path}")
        
        # Get all blobs from Firebase Storage
        blobs = bucket.list_blobs()
        blob_list = list(blobs)  # Convert to list to get count
        
        if not blob_list:
            print("No files found in Firebase Storage")
            return
        
        print(f"Found {len(blob_list)} files in Firebase Storage")
        print("Starting download...")
        print("-" * 60)
        
        success_count = 0
        failure_count = 0
        
        for i, blob in enumerate(blob_list, 1):
            try:
                # Skip folder markers (files ending with '/')
                if blob.name.endswith('/'):
                    print(f"[{i}/{len(blob_list)}] Skipping folder: {blob.name}")
                    continue
                
                # Create local file path, preserving directory structure
                local_file_path = os.path.join(local_path, blob.name)
                
                # Create directories if they don't exist
                local_dir = os.path.dirname(local_file_path)
                if local_dir:
                    os.makedirs(local_dir, exist_ok=True)
                
                # Download the file
                print(f"[{i}/{len(blob_list)}] Downloading: {blob.name}")
                blob.download_to_filename(local_file_path)
                
                # Get file size for confirmation
                file_size = os.path.getsize(local_file_path)
                print(f"    → Downloaded to: {local_file_path}")
                print(f"    → File size: {file_size:,} bytes")
                
                success_count += 1
                
            except Exception as e:
                print(f"    → Error downloading {blob.name}: {e}")
                failure_count += 1
            
            print()  # Add spacing between files
        
        print("=" * 60)
        print(f"Download completed:")
        print(f"Success: {success_count}")
        print(f"Failures: {failure_count}")
        print(f"Files saved to: {local_path}")
        
    except Exception as e:
        print(f"Error during download process: {e}")

def create_dict_from_json(json_file):
    """Create a dictionary from a JSON file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if isinstance(data, dict):
                print (f"Dictionary contains {len(data)} items")
            elif isinstance(data, list):
                print(f"List contains {len(data)} items")
            else:
                print(f"Data is of type {type(data)}")
        
        return data
                
    except FileNotFoundError:
        print(f"Error: JSON file {json_file} not found")
        return None
    except json.JSONDecodeError:
        print(f"Error: JSON file {json_file} is not valid")
        return None
    except Exception as e:
        print(f"Error reading JSON file {json_file}: {e}")
        return None

def classifyUnclearWords(clarified_dict):
    """Rename Firebase files based on dictionary keys and values"""
    if not clarified_dict:
        print("Error: No dictionary provided")
        return
    
    bucket = initialize_firebase()
    if not bucket:
        return
    
    try:
        # Get all blobs from Firebase Storage
        blobs = bucket.list_blobs()
        
        # Create a dictionary to track files that need renaming
        rename_mapping = {}
        
        print(f"Searching for files matching {len(clarified_dict)} dictionary keys...")
        print("-" * 60)
        
        # Check each blob against dictionary keys
        for blob in blobs:
            filename = blob.name
            
            # Check if filename exactly matches any key in the dictionary
            for key, value in clarified_dict.items():
                if filename == key + ".pose":
                    new_filename = f"{key} ({value}).pose"
                    rename_mapping[filename] = new_filename
                    print(f"Found match: '{filename}' -> '{new_filename}'")
                    break
        
        if rename_mapping:
            print(f"\nFound {len(rename_mapping)} files to rename:")
            print("-" * 60)
            
            for old_name, new_name in rename_mapping.items():
                print(f"  {old_name}")
                print(f"  -> {new_name}")
                print()
            
            # Ask for confirmation
            response = input(f"Proceed with renaming {len(rename_mapping)} files? (y/N): ")
            if response.lower() == 'y':
                batch_rename_files(rename_mapping)
            else:
                print("Operation cancelled")
        else:
            print("No files found matching dictionary keys")
            
    except Exception as e:
        print(f"Error during classification process: {e}")

def main():
    """Rename operations in Firebase Storage"""
    print("Firebase Storage File Manager")
    print("=" * 50)
    
    # download all files for backup if needed
    # download_all_files()
    
    # Or replace any custom substring with whatever you want
    # replace_substring("_", "'")
    
    # create a dictionary from a JSON file
    dictionary = create_dict_from_json("/Users/albert/Downloads/clarified_definitions_openai.json")
    
    # print(dictionary)
    # use the dictionary to rename files in Firebase
    classifyUnclearWords(dictionary)

if __name__ == "__main__":
    main()