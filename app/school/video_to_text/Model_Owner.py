import json
import numpy as np
import asyncio
import os
import logging

class Model:
    def __init__(self, model_path):
        self.logger = logging.getLogger("connectinator")

        # ---- resolve app directory for stats/labels, independent of CWD ----
        # this file: .../app/school/video_to_text/Model_Owner.py
        THIS_DIR = os.path.dirname(os.path.abspath(__file__))
        APP_DIR = os.path.normpath(os.path.join(THIS_DIR, "..", ".."))  # .../app

        # sanity check model path
        self.model_path = os.path.abspath(model_path)
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        # Load label map (gloss -> class index)
        label_map_path = os.path.join(APP_DIR, 'label_map.json')
        with open(label_map_path, encoding="utf-8") as f:
            self.label_map = json.load(f)

        # Create reverse mapping (class index -> gloss)
        self.index_to_gloss = {v: k for k, v in self.label_map.items()}

        # Load stats for z-scoring
        stats_path = os.path.join(APP_DIR, 'stats.json')
        with open(stats_path, encoding="utf-8") as f:
            stats = json.load(f)
            self.mean = np.array(stats['mean'], dtype=np.float32)
            self.std = np.array(stats['std'], dtype=np.float32)
            # Avoid division by zero for very small std values
            self.std = np.where(self.std < 1e-8, 1.0, self.std)

        # ---- Load the BiLSTM model robustly (.h5/SavedModel via tf.keras, .keras via Keras 3) ----
        self.model = None
        # 1) try tf.keras (for SavedModel or .h5)
        try:
            import tensorflow as tf
            self.logger.info(f"Loading model with tf.keras from {self.model_path}")
            self.model = tf.keras.models.load_model(self.model_path, compile=False)
            self.logger.info("Loaded model with tf.keras")
        except Exception as e:
            self.logger.warning(f"tf.keras load failed: {type(e).__name__}: {e}")

        # 2) fallback to Keras 3 loader (for .keras format)
        if self.model is None:
            try:
                import keras  # Keras 3 (separate package)
                self.logger.info(f"Loading model with keras (Keras 3) from {self.model_path}")
                self.model = keras.models.load_model(self.model_path, compile=False, safe_mode=False)
                self.logger.info("Loaded model with keras (Keras 3)")
            except Exception as e:
                self.logger.error(f"Keras 3 load failed: {type(e).__name__}: {e}")
                raise

        print(f"Model loaded successfully. Number of classes: {len(self.index_to_gloss)}")

    async def query_model(self, keypoints):
        """
        keypoints: numpy array (64, 84)
        returns: dict with top-5 predictions and top-1 prediction
        """
        formatted_keypoints = self.__format_input_keypoints(keypoints)
        result = await self.__get_model_result(formatted_keypoints)
        final_result = self.__format_model_results(result)
        return final_result

    def __format_input_keypoints(self, keypoints):
        if keypoints.shape != (64, 84):
            raise ValueError(f"Expected keypoints shape (64, 84), got {keypoints.shape}")
        x_normalized = (keypoints - self.mean) / self.std
        x_batch = np.expand_dims(x_normalized, axis=0)
        return x_batch

    async def __get_model_result(self, keypoints_batch):
        """
        keypoints_batch: numpy array (1, 64, 84)
        returns: numpy array (num_classes,) softmax probabilities
        """
        # defer to a thread so we don't block the event loop
        def _predict():
            return self.model.predict(keypoints_batch, verbose=0)

        result = await asyncio.to_thread(_predict)
        return result[0]

    async def predict_from_normalized(self, x_normalized_batch):
        """
        x_normalized_batch: numpy array (1, 64, 84) already z-scored
        returns: numpy array (num_classes,) softmax
        """
        def _predict():
            return self.model.predict(x_normalized_batch, verbose=0)

        result = await asyncio.to_thread(_predict)
        return result[0]

    def __format_model_results(self, probs):
        # top-5
        top_5_indices = np.argsort(probs)[-5:][::-1]
        top_5_predictions = [[self.index_to_gloss[int(i)], float(probs[int(i)])] for i in top_5_indices]
        # top-1
        top_1_idx = int(np.argmax(probs))
        top_1 = {
            "label": self.index_to_gloss[top_1_idx],
            "probability": float(probs[top_1_idx]),
        }
        return {
            "model_output": top_5_predictions,
            "top_1": top_1,
            "top_5": top_5_predictions,
        }


   