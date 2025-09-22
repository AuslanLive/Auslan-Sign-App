import os
import json
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
        # Retrieve credentials from environment variables
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

def extract_filenames_to_json(output_file="src/scripts/wordDisambiguation/WordList.json"):
    """Extract all filenames from Firebase Storage and save to JSON file"""
    bucket = initialize_firebase()
    if not bucket:
        print("Failed to initialize Firebase")
        return
    
    try:
        # Get all blobs from Firebase Storage
        blobs = bucket.list_blobs()
        
        filenames = []
        
        print("Extracting filenames from Firebase Storage...")
        print("-" * 60)
        
        file_count = 0
        for blob in blobs:
            # Skip folder markers (files ending with '/')
            if blob.name.endswith('/'):
                continue
                
            # Extract filename from full path
            # Get just the filename (last part after '/')
            full_filename = blob.name.split('/')[-1]
            
            # Check if file has .pose extension
            if not full_filename.lower().endswith('.pose'):
                continue
            
            # Remove extension
            filename_without_extension = os.path.splitext(full_filename)[0]
            
            # Add to list if not empty
            if filename_without_extension:
                filenames.append(filename_without_extension)
                file_count += 1
                print(f"File {file_count}: {blob.name} -> {filename_without_extension}")
        
        # Remove duplicates and sort
        unique_filenames = sorted(list(set(filenames)))
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_filenames, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print(f"Extraction completed!")
        print(f"Total files processed: {file_count}")
        print(f"Unique filenames extracted: {len(unique_filenames)}")
        print(f"Filenames saved to: {output_file}")
        
        # Display first few filenames as preview
        if unique_filenames:
            print("\nPreview of extracted filenames:")
            for i, filename in enumerate(unique_filenames[:10]):
                print(f"  {i+1}. {filename}")
            if len(unique_filenames) > 10:
                print(f"  ... and {len(unique_filenames) - 10} more")
        
        return unique_filenames
        
    except Exception as e:
        print(f"Error extracting filenames: {e}")
        return None

def main():
    """Main function to extract filenames"""
    print("Firebase Storage Filename Extractor")
    print("=" * 50)
    
    # Extract filenames and save to JSON
    output_filename = "firebase_filenames.json"
    filenames = extract_filenames_to_json(output_filename)
    
    if filenames:
        print(f"\nSuccessfully extracted {len(filenames)} unique filenames")
        print(f"Results saved to: {output_filename}")
    else:
        print("Failed to extract filenames")

if __name__ == "__main__":
    main()