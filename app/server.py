from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.school.Connectinator import Connectinator
import os

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

model_path = os.path.join('app', r'loaded_bananamode_AAAAAAAAAAAAAAAAAAAAAAAAaa.keras')

# MAIN CLASS WHICH CONNECTS TO ALL THE BACK END STUFF
connectinator = Connectinator(model_path)


@app.route("/")
def index():
    return render_template('keypoints.html')

@app.route('/sign_to_text')
def run_text_to_sign():
    return render_template('text_to_sign.html')


@app.route('/api/keypoints', methods=['POST'])
async def receive_keypoints():
    data = request.json  # Get the JSON data from the request

    # You can process, store, or log the keypoints here
    # print("Received landmarks:", data)  # Print keypoints for demonstration

    # Sending data to the connectinator
    await connectinator.process_frame(data)

    return jsonify({"message": "Keypoints received successfully!"})


@app.route('/model_output', methods=['GET', 'POST'])
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


@app.route('/get_sign_to_text', methods=["GET", "POST"])
def get_sign_to_text():
    translated_message = connectinator.get_transltion()

    return jsonify({"translation": translated_message}), 200


@app.route('/getGemFlag', methods=["GET", "POST"])
def get_gem_flag():
    gem_flag = connectinator.get_gem_flag()

    return jsonify({"flag": gem_flag}), 200


@app.route('/t2s', methods=['POST'])
def t2s_parse():
    # try:
    t2s_input = request.get_json()
    connectinator.logger.info('Received request on /t2s: %s', t2s_input)

    processed_t2s_phrase = connectinator.format_sign_text(
        t2s_input['t2s_input'])

    return jsonify({"message": processed_t2s_phrase}), 200
    # except Exception as e:
    #     connectinator.logger.error(f'Error processing request: {e}')
    #     return jsonify({"error": "Internal Server Error. Check JSON Format"}), 500


@app.route('/get_phrase')
def get_phrase():
    return connectinator.front_end_translation_variable  # the end


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))