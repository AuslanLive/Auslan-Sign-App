from flask import Flask, jsonify
import subprocess
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({'message': 'Test endpoint is working!'})

@app.route('/run-animation-script', methods=['POST'])  # Changed the name here
def run_animation_script():
    try:
        # Run the Python script using subprocess
        result = subprocess.run(
            ['python', 'text-to-animation/pose_video_creator.py'], 
            capture_output=True, text=True
        )

        # Check for errors in the result
        if result.returncode != 0:
            return jsonify({'error': result.stderr.strip()}), 500
        
        # Return the output of the script
        return jsonify({'output': result.stdout.strip()})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run-test-script', methods=['POST'])
def run_test_script():
    result = subprocess.run(['python', 'test_script.py'], capture_output=True, text=True)
    return jsonify({'output': result.stdout.strip(), 'error': result.stderr.strip()})

if __name__ == '__main__':
    print("Current working directory:", os.getcwd())  # Debugging line
    app.run(host='0.0.0.0', port=5000, debug=True)
