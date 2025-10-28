import sys
import os

print("=" * 60)
print("Flask Server Test")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print()

print("Checking required files...")
required_files = [
    "app/server.py",
    "app/variablemodel-callbacks-keras/variablehonoursmodel1.keras",
    "app/variablemodel-callbacks-keras/label_map (1).json",
    "app/variablemodel-callbacks-keras/stats (1).json"
]

all_exist = True
for file_path in required_files:
    exists = os.path.exists(file_path)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {file_path}")
    if not exists:
        all_exist = False

print()

if not all_exist:
    print("Some required files are missing!")
    input("Press Enter to exit...")
    sys.exit(1)

print("All files found. Testing imports...")

try:
    print("  Importing Flask...", end=" ")
    import flask
    print(f"OK (version {flask.__version__})")
except ImportError as e:
    print(f"FAILED: {e}")
    print("\nRun: pip install flask flask-cors")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    print("  Importing TensorFlow...", end=" ")
    import tensorflow as tf
    print(f"OK (version {tf.__version__})")
except ImportError as e:
    print(f"FAILED: {e}")
    print("\nRun: pip install tensorflow")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    print("  Importing numpy...", end=" ")
    import numpy as np
    print(f"OK (version {np.__version__})")
except ImportError as e:
    print(f"FAILED: {e}")
    print("\nRun: pip install numpy")
    input("Press Enter to exit...")
    sys.exit(1)

print()
print("All imports successful. Attempting to start Flask server...")
print("If this hangs, check the model loading...")
print()

try:
    from app.school.Connectinator import Connectinator
    
    model_path = os.path.join('app', 'variablemodel-callbacks-keras', 'variablehonoursmodel1.keras')
    label_map_path = os.path.join('app', 'variablemodel-callbacks-keras', 'label_map (1).json')
    stats_path = os.path.join('app', 'variablemodel-callbacks-keras', 'stats (1).json')
    
    print("Initializing Connectinator with honors model...")
    print(f"  Model: {model_path}")
    print(f"  Labels: {label_map_path}")
    print(f"  Stats: {stats_path}")
    print()
    
    connectinator = Connectinator(model_path, label_map_path, stats_path)
    
    print("SUCCESS! Connectinator initialized successfully.")
    print()
    print("Model info:")
    print(f"  Classes: {len(connectinator.model.label_map)}")
    print(f"  Input shape: {connectinator.model.model.input_shape}")
    print(f"  Output shape: {connectinator.model.model.output_shape}")
    print()
    print("Flask server should start normally.")
    
except Exception as e:
    print(f"ERROR during initialization: {e}")
    print(f"Error type: {type(e).__name__}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("This is the error preventing Flask from starting!")

print()
input("Press Enter to exit...")

