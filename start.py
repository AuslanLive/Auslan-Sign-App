#!/usr/bin/env python3
"""
Start script for Auslan Sign App
Runs both the Flask server and Vite client development server simultaneously.
Works on both Windows and Mac/Linux.
"""

import subprocess
import sys
import os
import signal
import time
import threading
from pathlib import Path

# Use simple ASCII characters for better Windows compatibility

class AppRunner:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_server(self):
        """Start the Flask server"""
        print(">>> Starting Flask server...")
        try:
            # Use python -m app.server as specified
            server_cmd = [sys.executable, "-m", "app.server"]
            server_process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(("Flask Server", server_process))
            
            # Print server output in a separate thread
            def print_server_output():
                for line in iter(server_process.stdout.readline, ''):
                    if self.running:
                        print(f"[SERVER] {line.rstrip()}")
                    else:
                        break
                        
            threading.Thread(target=print_server_output, daemon=True).start()
            
        except Exception as e:
            print(f"ERROR: Failed to start Flask server: {e}")
            return False
        return True
    
    def start_client(self):
        """Start the Vite client development server"""
        print(">>> Starting Vite client...")
        try:
            # Check if npm is available
            try:
                subprocess.run(["npm", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("ERROR: npm not found. Please install Node.js and npm.")
                return False
            
            # Check if package.json exists
            if not Path("package.json").exists():
                print("ERROR: package.json not found. Are you in the correct directory?")
                return False
            
            # Install dependencies if node_modules doesn't exist
            if not Path("node_modules").exists():
                print(">>> Installing npm dependencies...")
                install_process = subprocess.run(
                    ["npm", "install"],
                    capture_output=True,
                    text=True
                )
                if install_process.returncode != 0:
                    print(f"ERROR: Failed to install dependencies: {install_process.stderr}")
                    return False
                print("SUCCESS: Dependencies installed successfully")
            
            # Start the Vite dev server
            client_cmd = ["npm", "run", "dev"]
            client_process = subprocess.Popen(
                client_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(("Vite Client", client_process))
            
            # Print client output in a separate thread
            def print_client_output():
                for line in iter(client_process.stdout.readline, ''):
                    if self.running:
                        print(f"[CLIENT] {line.rstrip()}")
                    else:
                        break
                        
            threading.Thread(target=print_client_output, daemon=True).start()
            
        except Exception as e:
            print(f"ERROR: Failed to start Vite client: {e}")
            return False
        return True
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n>>> Shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up all running processes"""
        for name, process in self.processes:
            if process.poll() is None:  # Process is still running
                print(f">>> Stopping {name}...")
                try:
                    # Try graceful termination first
                    process.terminate()
                    # Wait a bit for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't stop gracefully
                        process.kill()
                        process.wait()
                except Exception as e:
                    print(f"WARNING: Error stopping {name}: {e}")
    
    def run(self):
        """Main run method"""
        print(">>> Starting Auslan Sign App...")
        print("=" * 50)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start both processes
        server_success = self.start_server()
        if not server_success:
            print("ERROR: Failed to start server. Exiting.")
            return
        
        # Give server a moment to start
        time.sleep(2)
        
        client_success = self.start_client()
        if not client_success:
            print("ERROR: Failed to start client. Stopping server.")
            self.cleanup()
            return
        
        print("=" * 50)
        print("SUCCESS: Both servers started successfully!")
        print("Client: http://localhost:5173")
        print("Server: http://localhost:5001")
        print("Press Ctrl+C to stop both servers")
        print("=" * 50)
        
        try:
            # Keep the main thread alive and monitor processes
            while self.running:
                # Check if any process has died
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"ERROR: {name} has stopped unexpectedly")
                        self.running = False
                        break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    # Check if we're in the right directory
    if not Path("app").exists() or not Path("package.json").exists():
        print("ERROR: Please run this script from the project root directory")
        print("   (the directory containing 'app' folder and 'package.json')")
        sys.exit(1)
    
    runner = AppRunner()
    runner.run()

if __name__ == "__main__":
    main()
