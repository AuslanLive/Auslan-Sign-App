import subprocess
import sys
import os
import signal
import time

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n Shutting down servers...")
    sys.exit(0)

def main():
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print(" Starting AuslanLive Application...\n")
    
    # Check if we're in the right directory
    if not os.path.exists("app/server.py"):
        print(" Error: Cannot find app/server.py")
        print("   Please run this script from the project root directory.")
        sys.exit(1)
    
    if not os.path.exists("package.json"):
        print(" Error: Cannot find package.json")
        print("   Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("  Warning: .env file not found in root directory")
        print("   The application may not work without environment variables.\n")
    
    processes = []
    
    try:
        # Start Flask backend
        print(" Starting Flask server...")
        flask_process = subprocess.Popen(
            [sys.executable, "-m", "app.server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        processes.append(("Flask", flask_process))
        print(" Flask server started\n")
        
        # Give Flask a moment to start
        time.sleep(2)
        
        # Start npm dev server
        print(" Starting frontend dev server...")
        npm_process = subprocess.Popen(
            ["npm", "run", "dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            shell=True  # Required for Windows
        )
        processes.append(("NPM", npm_process))
        print("Frontend dev server started\n")
        
        print("=" * 60)
        print(" AuslanLive is running!")
        print("=" * 60)
        print("\n Server Output:\n")
        
        # Monitor both processes and display their output
        while True:
            # Check Flask output
            if flask_process.poll() is None:
                flask_line = flask_process.stdout.readline()
                if flask_line:
                    print(f"[Flask] {flask_line.strip()}")
            else:
                print(" Flask server stopped unexpectedly")
                break
            
            # Check NPM output
            if npm_process.poll() is None:
                npm_line = npm_process.stdout.readline()
                if npm_line:
                    print(f"[NPM] {npm_line.strip()}")
            else:
                print(" NPM dev server stopped unexpectedly")
                break
            
            time.sleep(0.1)
    
    except FileNotFoundError as e:
        print(f"\n Error: {e}")
        print("\nMake sure you have:")
        print("  1. Python installed and in PATH")
        print("  2. Node.js and npm installed")
        print("  3. Run 'pip install -r requirements.txt'")
        print("  4. Run 'npm install'")
    
    except Exception as e:
        print(f"\n Unexpected error: {e}")
    
    finally:
        # Clean up processes
        print("\n Cleaning up...")
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f" {name} server stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"  {name} server force killed")
            except Exception as e:
                print(f"  Error stopping {name} server: {e}")

if __name__ == "__main__":
    main()

