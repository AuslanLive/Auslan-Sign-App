from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.school.Connectinator import Connectinator
import os
from time import time

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

model_path = os.path.join('app', 'variablemodel-callbacks-keras', 'variablehonoursmodel1.keras')
label_map_path = os.path.join('app', 'variablemodel-callbacks-keras', 'label_map (1).json')
stats_path = os.path.join('app', 'variablemodel-callbacks-keras', 'stats (1).json')

if not os.path.exists(model_path):
    print(f"(server.py) Error: Model file not found at {model_path}")
    print(f"(server.py) Current working directory: {os.getcwd()}")
    exit(1)

if not os.path.exists(label_map_path):
    print(f"(server.py) Error: Label map not found at {label_map_path}")
    exit(1)

if not os.path.exists(stats_path):
    print(f"(server.py) Error: Stats file not found at {stats_path}")
    exit(1)

print(f"(server.py) Loading honors model from {model_path}")
print(f"(server.py) Using label map: {label_map_path}")
print(f"(server.py) Using stats: {stats_path}")

# MAIN CLASS WHICH CONNECTS TO ALL THE SYSTEM
connectinator = Connectinator(model_path, label_map_path, stats_path)

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
        
        if processed_t2s_phrase == ["TEXT_TO_SIGN_DISABLED"]:
            return jsonify({"error": "Text-to-sign feature is currently disabled. The grammar parser model failed to load."}), 503
        
        if processed_t2s_phrase == ["TEXT_TO_SIGN_ERROR"]:
            return jsonify({"error": "Error processing text-to-sign request."}), 500
        
        print(f"POSE VIDEO CREATED - Time taken: {time()-start:0.4f}")

        return jsonify({"message": processed_t2s_phrase}), 200
    
    except Exception as e:
        connectinator.logger.error(f'Error processing request: {e}')
        return jsonify({"error": "Internal Server Error. Check JSON Format"}), 500


@app.route('/api/get_phrase')
def get_phrase():
    return connectinator.front_end_translation_variable  # the end


# New endpoints for honors model top-5 predictions
@app.route('/api/get_pending_predictions', methods=['GET'])
def get_pending_predictions():
    """
    Get pending top-5 predictions waiting for user selection.
    """
    try:
        predictions = connectinator.get_pending_predictions()
        return jsonify({"predictions": predictions}), 200
    except Exception as e:
        connectinator.logger.error(f'Error getting pending predictions: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/select_word', methods=['POST'])
def select_word():
    """
    User selected a word from the top-5 predictions.
    """
    try:
        data = request.get_json()
        selected_word = data.get('word')
        
        if not selected_word:
            return jsonify({"error": "No word provided"}), 400
        
        connectinator.logger.info(f'User selected word: {selected_word}')
        connectinator.select_word_from_top5(selected_word)
        
        return jsonify({
            "status": "success",
            "word": selected_word,
            "current_sentence": connectinator.front_end_translation_variable
        }), 200
        
    except Exception as e:
        connectinator.logger.error(f'Error selecting word: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/skip_prediction', methods=['POST'])
def skip_prediction():
    """
    User wants to skip the current top-5 prediction.
    """
    try:
        connectinator.skip_current_prediction()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        connectinator.logger.error(f'Error skipping prediction: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/clear_sentence', methods=['POST'])
def clear_sentence():
    """
    Clear the current sentence.
    """
    try:
        connectinator.current_sentence_words = []
        connectinator.front_end_translation_variable = ''
        connectinator.clear_pending_predictions()
        connectinator.resume_processing()  # Resume if it was paused
        return jsonify({"status": "success"}), 200
    except Exception as e:
        connectinator.logger.error(f'Error clearing sentence: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/get_processing_status', methods=['GET'])
def get_processing_status():
    """
    Get the current processing status (paused or active).
    """
    try:
        return jsonify({
            "is_paused": connectinator.is_paused,
            "has_pending_predictions": len(connectinator.pending_predictions) > 0
        }), 200
    except Exception as e:
        connectinator.logger.error(f'Error getting processing status: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/get_frame_status', methods=['GET'])
def get_frame_status():
    """
    Get current frame collection status for progress UI.
    """
    try:
        status = connectinator.get_frame_buffer_status()
        return jsonify(status), 200
    except Exception as e:
        connectinator.logger.error(f'Error getting frame status: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/force_predict', methods=['POST'])
async def force_predict():
    """
    Force prediction on current buffer (manual spacebar trigger).
    """
    try:
        success = await connectinator.force_predict_current_buffer()
        if success:
            return jsonify({"status": "success", "message": "Prediction triggered"}), 200
        else:
            return jsonify({"status": "failed", "message": "Not enough frames or unable to predict"}), 400
    except Exception as e:
        connectinator.logger.error(f'Error forcing prediction: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/get_sentence_words', methods=['GET'])
def get_sentence_words():
    """
    Get the current sentence as a list of word objects with alternatives.
    Each word includes top-5 alternatives for click-to-fix functionality.
    """
    try:
        words_data = connectinator.get_sentence_with_words()
        return jsonify({"words": words_data}), 200
    except Exception as e:
        connectinator.logger.error(f'Error getting sentence words: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/replace_word', methods=['POST'])
def replace_word():
    """
    Replace a word in the sentence (click-to-fix).
    
    Request body: {"word_id": 0, "new_word": "HELLO"}
    """
    try:
        data = request.json
        word_id = data.get('word_id')
        new_word = data.get('new_word')
        
        if word_id is None or new_word is None:
            return jsonify({"error": "Missing word_id or new_word"}), 400
        
        success = connectinator.replace_word(word_id, new_word)
        if success:
            return jsonify({"status": "success", "message": f"Word {word_id} replaced with {new_word}"}), 200
        else:
            return jsonify({"status": "failed", "message": "Invalid word_id"}), 400
    except Exception as e:
        connectinator.logger.error(f'Error replacing word: {e}')
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5173)