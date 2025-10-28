import subprocess
import sys
import os
import signal
import time
import urllib.request
import urllib.error

def is_admin():
    if sys.platform != 'win32':
        return True
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if sys.platform == 'win32' and not is_admin():
        print("Not running as administrator. Requesting elevation...")
        try:
            import ctypes
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",
                sys.executable,
                f'"{script}" {params}',
                None,
                1
            )
            
            if ret <= 32:
                print("Failed to elevate. Please run manually as administrator.")
                input("Press Enter to exit...")
                sys.exit(1)
            else:
                print("Relaunching with administrator privileges...")
                sys.exit(0)
                
        except Exception as e:
            print(f"Error requesting admin privileges: {e}")
            print("Please run this script as administrator manually:")
            print(f"  Right-click Command Prompt and Run as administrator")
            print(f"  Then run: python {sys.argv[0]}")
            input("Press Enter to exit...")
            sys.exit(1)

def signal_handler(sig, frame):
    print("\n\nShutting down servers...")
    sys.exit(0)

def wait_for_flask(url="http://localhost:5173/api/get_sign_to_text", timeout=60, check_interval=1):
    """
    Wait for Flask server to be ready by polling a simple endpoint.
    Returns True if Flask is ready, False if timeout reached.
    """
    import sys
    print("Waiting for Flask server to be ready", end="", flush=True)
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.getcode() == 200:
                print(" ✓")
                return True
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionRefusedError):
            pass
        except Exception:
            pass
        
        print(".", end="", flush=True)
        time.sleep(check_interval)
    
    print(" ✗ (timeout)")
    return False

def main():
    try:
        run_as_admin()
    except Exception as e:
        print(f"Error during admin elevation: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting AuslanLive Application...\n")
    
    if is_admin() and sys.platform == 'win32':
        print("Running with administrator privileges\n")
    
    if not os.path.exists("app/server.py"):
        print("Error: Cannot find app/server.py")
        print("Please run this script from the project root directory.")
        print(f"Current directory: {os.getcwd()}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    if not os.path.exists("package.json"):
        print("Error: Cannot find package.json")
        print("Please run this script from the project root directory.")
        print(f"Current directory: {os.getcwd()}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    if not os.path.exists(".env"):
        print("Warning: .env file not found in root directory")
        print("The application may not work without environment variables.\n")
    
    processes = []
    
    try:
        print("Starting Flask server...")
        print(f"Python executable: {sys.executable}")
        print(f"Working directory: {os.getcwd()}\n")
        
        flask_process = subprocess.Popen(
            [sys.executable, "-m", "app.server"]
        )
        processes.append(("Flask", flask_process))
        print("Flask server process started\n")
        
        time.sleep(2)
        
        if flask_process.poll() is not None:
            print("Flask server exited immediately!")
            print("Check the output above for errors")
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        # Wait for Flask to be ready before starting frontend
        if not wait_for_flask():
            print("\nFlask server failed to start within 60 seconds")
            print("Check the output above for errors")
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        print("\nStarting frontend dev server...")
        npm_process = subprocess.Popen(
            ["npm", "run", "dev"],
            shell=True
        )
        processes.append(("NPM", npm_process))
        print("Frontend dev server process started\n")
        
        time.sleep(3)
        
        if npm_process.poll() is not None:
            print("NPM dev server exited immediately!")
            print("Check the output above for errors")
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("AuslanLive is running!")
        print("=" * 60)
        print("Frontend: http://localhost:3173")
        print("Backend:  http://localhost:5173")
        print("\nOpen your browser and navigate to: http://localhost:3173")
        print("Press Ctrl+C to stop servers\n")
        
        print("Servers are running. Output will appear below:")
        print("-" * 60)
        
        while True:
            flask_running = flask_process.poll() is None
            npm_running = npm_process.poll() is None
            
            if not flask_running or not npm_running:
                if not flask_running:
                    print("\nFlask server has stopped")
                if not npm_running:
                    print("\nNPM dev server has stopped")
                break
            
            time.sleep(1)
    
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("  1. Python installed and in PATH")
        print("  2. Node.js and npm installed")
        print("  3. Run 'pip install -r requirements.txt'")
        print("  4. Run 'npm install'")
        input("\nPress Enter to exit...")
    
    except KeyboardInterrupt:
        print("\n\nReceived keyboard interrupt, shutting down...")
    
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
    
    finally:
        print("\nCleaning up...")
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"{name} server stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"{name} server force killed")
            except Exception as e:
                print(f"Error stopping {name} server: {e}")

if __name__ == "__main__":
    main()
