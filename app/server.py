from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.school.Connectinator import Connectinator
import os
from time import time
import asyncio
import numpy as np
import json

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

model_path = os.path.join('app', r'bilstm_best.keras')

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
    translated_message = connectinator.get_transltion()
    top_5_predictions = connectinator.get_top_predictions()
    top_1_prediction = connectinator.get_top_1_prediction()

    return jsonify({
        "translation": translated_message,
        "top_5": top_5_predictions,
        "top_1": top_1_prediction
    }), 200


# Batch recording endpoint: accept an array of frames and process sequentially
@app.route('/api/recording', methods=['POST'])
def process_recording():
    try:
        payload = request.get_json()
        frames = payload.get('frames', [])
        if not isinstance(frames, list) or len(frames) == 0:
            return jsonify({"error": "No frames provided"}), 400

        # Build tensors per spec: stride=2, hand-only, wrist-center + MCP scale, pad/trim to 64
        kept = frames[::2]
        x_list = []  # (84,)
        m_list = []  # (42,)

        def norm_hand(hand):
            if not hand:
                return np.zeros((21, 2), dtype=np.float32), np.zeros(21, dtype=np.float32)
            pts = np.array([[max(0.0, min(1.0, p.get('x', 0.0))),
                             max(0.0, min(1.0, p.get('y', 0.0)))] for p in hand[:21]], dtype=np.float32)
            wrist = pts[0]
            mcps = pts[[5, 9, 13, 17]]
            scale = float(np.mean(np.linalg.norm(mcps - wrist, axis=1)))
            if scale < 1e-6:
                scale = 1.0
            norm = (pts - wrist) / scale
            mask = np.ones(21, dtype=np.float32)
            return norm, mask

        for fr in kept:
            kp = fr.get('keypoints', [None, None, None])
            L, mL = norm_hand(kp[1]) if len(kp) > 1 else (np.zeros((21,2), np.float32), np.zeros(21, np.float32))
            R, mR = norm_hand(kp[2]) if len(kp) > 2 else (np.zeros((21,2), np.float32), np.zeros(21, np.float32))
            feat = np.concatenate([L, R], axis=0).reshape(-1)
            mask = np.concatenate([mL, mR], axis=0)
            x_list.append(feat)
            m_list.append(mask)

        T = 64
        if len(x_list) >= T:
            x = np.stack(x_list[:T], axis=0)
            m = np.stack(m_list[:T], axis=0)
        else:
            pad_f = T - len(x_list)
            x = np.vstack([np.stack(x_list, 0) if x_list else np.zeros((0,84), np.float32), np.zeros((pad_f, 84), np.float32)])
            m = np.vstack([np.stack(m_list, 0) if m_list else np.zeros((0,42), np.float32), np.zeros((pad_f, 42), np.float32)])

        # zero-out missing (repeat mask to features)
        m_feat = np.repeat(m, 2, axis=1)
        x_masked = x * m_feat

        # z-score using training stats
        with open(os.path.join('app', 'stats.json'), 'r') as f:
            stats = json.load(f)
        mu = np.array(stats['mean'], dtype=np.float32)
        sd = np.array(stats['std'], dtype=np.float32)
        sd[sd < 1e-6] = 1.0
        x_norm = (x_masked - mu) / sd

        # predict (batch=1)
        x_batch = np.expand_dims(x_norm.astype(np.float32), axis=0)
        probs = asyncio.run(connectinator.model.predict_from_normalized(x_batch))

        # map to labels
        with open(os.path.join('app', 'label_map.json'), 'r') as f:
            lm = json.load(f)
        inv = {v: k for k, v in lm.items()}
        top5_idx = np.argsort(probs)[-5:][::-1]
        top5 = [[inv[int(i)], float(probs[i])] for i in top5_idx]
        top1 = {"label": inv[int(top5_idx[0])], "probability": float(probs[top5_idx[0]])}

        connectinator.front_end_translation_variable = top1['label']
        # Store last model output so polling endpoints can surface top-5
        try:
            connectinator.last_model_output = {
                "top_1": top1,
                "top_5": top5,
                "model_output": top5,
            }
        except Exception:
            # Be resilient if attribute missing
            pass

        return jsonify({
            "message": "Recording processed",
            "top_1": top1,
            "top_5": top5,
            "translation": connectinator.get_transltion(),
            "shapes": {"x": list(x.shape), "mask": list(m.shape)}
        }), 200
    except Exception as e:
        connectinator.logger.error(f'Error processing recording: {e}')
        return jsonify({"error": "Failed to process recording"}), 500


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
        print(f"Time taken {time()-start:0.4f}")

        return jsonify({"message": processed_t2s_phrase}), 200
    
    except Exception as e:
        connectinator.logger.error(f'Error processing request: {e}')
        return jsonify({"error": "Internal Server Error. Check JSON Format"}), 500


@app.route('/api/get_phrase')
def get_phrase():
    return connectinator.front_end_translation_variable  # the end


@app.route('/api/get_top_predictions', methods=["GET"])
def get_top_predictions():
    """Get the top-5 predictions from the last model output"""
    top_5 = connectinator.get_top_predictions()
    return jsonify({"top_5": top_5}), 200


@app.route('/api/get_top_1', methods=["GET"])
def get_top_1():
    """Get the top-1 prediction from the last model output"""
    top_1 = connectinator.get_top_1_prediction()
    return jsonify({"top_1": top_1}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5173)