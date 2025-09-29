import json
import numpy as np
import tensorflow as tf
import asyncio
import os

class Model:
    def __init__(self, model_path):
        # Setting base variables
        self.model_path = model_path
        
        # Load label map (gloss -> class index)
        label_map_path = os.path.join('app', 'label_map.json')
        with open(label_map_path) as f:
            self.label_map = json.load(f)
        
        # Create reverse mapping (class index -> gloss)
        self.index_to_gloss = {v: k for k, v in self.label_map.items()}
        
        # Load stats for z-scoring
        stats_path = os.path.join('app', 'stats.json')
        with open(stats_path) as f:
            stats = json.load(f)
            self.mean = np.array(stats['mean'], dtype=np.float32)
            self.std = np.array(stats['std'], dtype=np.float32)
            # Avoid division by zero for very small std values
            self.std = np.where(self.std < 1e-8, 1.0, self.std)
        
        # Load the BiLSTM model
        self.model = tf.keras.models.load_model(model_path)
        
        print(f"Model loaded successfully. Number of classes: {len(self.index_to_gloss)}")

    async def query_model(self, keypoints):
        """
        Query the model with formatted keypoints
        Args:
            keypoints: numpy array of shape (48, 84) - 48 frames, 84 features (42 joints * 2 coords)
        Returns:
            dict with top-5 predictions and top-1 prediction
        """
        # Format keypoints for model input
        formatted_keypoints = self.__format_input_keypoints(keypoints)
        
        # Query the model
        result = await self.__get_model_result(formatted_keypoints)
        
        # Parse results to get top-5 and top-1
        final_result = self.__format_model_results(result)
        
        return final_result

    def __format_input_keypoints(self, keypoints):
        """
        Format keypoints for model input
        Args:
            keypoints: numpy array of shape (48, 84)
        Returns:
            numpy array of shape (1, 48, 84) with z-scoring applied
        """
        # Ensure we have the right shape
        if keypoints.shape != (48, 84):
            raise ValueError(f"Expected keypoints shape (48, 84), got {keypoints.shape}")
        
        # Apply z-scoring using training statistics
        x_normalized = (keypoints - self.mean) / self.std
        
        # Add batch dimension
        x_batch = np.expand_dims(x_normalized, axis=0)
        
        return x_batch

    async def __get_model_result(self, keypoints):
        """
        Get model prediction
        Args:
            keypoints: numpy array of shape (1, 48, 84)
        Returns:
            numpy array of shape (num_classes,) - softmax probabilities
        """
        # Query the model with just the keypoints (no mask needed)
        result = await asyncio.to_thread(self.model.predict, keypoints, verbose=0)
        
        return result[0]  # Remove batch dimension

    async def predict_from_normalized(self, x_normalized_batch):
        """
        Predict assuming x_normalized_batch is already z-scored and batched.
        Args:
            x_normalized_batch: numpy array (1, 48, 84)
        Returns:
            numpy array (num_classes,) softmax
        """
        result = await asyncio.to_thread(self.model.predict, x_normalized_batch, verbose=0)
        return result[0]

    def __format_model_results(self, result):
        """
        Format model results to get top-5 predictions and top-1
        Args:
            result: numpy array of shape (num_classes,) - softmax probabilities
        Returns:
            dict with top-5 predictions and top-1 prediction
        """
        # Get top-5 predictions
        top_5_indices = np.argsort(result)[-5:][::-1]  # Sort descending, take top 5
        
        top_5_predictions = []
        for idx in top_5_indices:
            gloss = self.index_to_gloss[idx]
            probability = float(result[idx])
            top_5_predictions.append([gloss, probability])
        
        # Get top-1 prediction
        top_1_idx = np.argmax(result)
        top_1_gloss = self.index_to_gloss[top_1_idx]
        top_1_probability = float(result[top_1_idx])
        
        # Format for compatibility with existing code
        formatted_results = {
            "model_output": top_5_predictions,
            "top_1": {
                "label": top_1_gloss,
                "probability": top_1_probability
            },
            "top_5": top_5_predictions
        }
        
        return formatted_results