from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.school.Connectinator import Connectinator
import os
from time import time

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

model_path = os.path.join('app', r'sign_to_text_model.keras')

if not os.path.exists(model_path):
    print(f"(server.py) Error: Model file not found at {model_path}")
    print(f"(server.py) Current working directory: {os.getcwd()}")
    print(f"(server.py) Files in app directory: {os.listdir('app') if os.path.exists('app') else 'app directory not found'}")
    exit(1)

# MAIN CLASS WHICH CONNECTS TO ALL THE SYSTEM
connectinator = Connectinator(model_path)

@app.route('/api/keypoints', methods=['POST'])
async def receive_keypoints():
    data = request.json  # Get the JSON data from the request

    # You can process, store, or log the keypoints here
    # print("Received landmarks:", data)  # Print keypoints for demonstration

    # Sending data to the connectinator
    await connectinator.process_frame(data)

    return jsonify({"message": "Keypoints received successfully!"})


@app.route('/api/model_output', methods=['GET', 'POST'])
def model_output_parse():
    try:
        model_output = request.get_json()
        connectinator.logger.info(
            'Received request on /model_output: %s', model_output)  # Updated log message

        processed_output = connectinator.format_model_output(
            model_output['model_output'])

        return jsonify({"message": processed_output}), 200

    except Exception as e:
        connectinator.logger.error(f'Error processing request: {e}')
        return jsonify({"error": "Internal Server Error. Check JSON Format"}), 500


@app.route('/api/get_sign_to_text', methods=["GET", "POST"])
def get_sign_to_text():
    translated_message = connectinator.get_translation()

    return jsonify({"translation": translated_message}), 200


@app.route('/api/getGemFlag', methods=["GET", "POST"])
def get_gem_flag():
    gem_flag = connectinator.get_gem_flag()

    return jsonify({"flag": gem_flag}), 200


@app.route('/api/t2s', methods=['POST'])
def t2s_parse():
    try:
        start = time()

        t2s_input = request.get_json()
        connectinator.logger.info('Received request on /t2s: %s', t2s_input)
        processed_t2s_phrase = connectinator.format_sign_text(t2s_input['t2s_input'])
        print(f"POSE VIDEO CREATED - Time taken: {time()-start:0.4f}")

        return jsonify({"message": processed_t2s_phrase}), 200
    
    except Exception as e:
        connectinator.logger.error(f'Error processing request: {e}')
        return jsonify({"error": "Internal Server Error. Check JSON Format"}), 500


@app.route('/api/get_phrase')
def get_phrase():
    return connectinator.front_end_translation_variable  # the end


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5173)