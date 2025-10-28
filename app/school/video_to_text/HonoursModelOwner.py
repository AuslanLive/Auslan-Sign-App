"""
HonoursModelOwner.py

Loads the trained model and provides prediction interface with top-K results.
Supports variable-length sequences (32-300 frames).
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import json
import asyncio
import os


class HonoursModelOwner:
    """
    Handles loading and querying the honors model.
    Returns top-K predictions with confidence scores.
    """
    
    def __init__(self, model_path, label_map_path, top_k=5):
        """
        Initialize the model owner.
        
        Args:
            model_path: Path to variablehonoursmodel1.keras
            label_map_path: Path to label_map.json
            top_k: Number of top predictions to return (default 5)
        """
        self.model_path = model_path
        self.top_k = top_k
        
        # Load label map
        with open(label_map_path, 'r') as f:
            self.label_map = json.load(f)
        
        # Create inverse mapping (index -> label)
        self.inv_label_map = {v: k for k, v in self.label_map.items()}
        self.num_classes = len(self.label_map)
        
        # Load model
        print(f"(HonoursModelOwner) Loading model from {model_path}...")
        try:
            self.model = load_model(model_path)
            print(f"(HonoursModelOwner) Model loaded successfully!")
            print(f"(HonoursModelOwner) Input shape: {self.model.input_shape}")
            print(f"(HonoursModelOwner) Output shape: {self.model.output_shape}")
            print(f"(HonoursModelOwner) Number of classes: {self.num_classes}")
        except Exception as e:
            print(f"(HonoursModelOwner) Error loading model: {e}")
            raise
    
    async def query_model(self, window_data):
        """
        Query the model with a padded window.
        
        Args:
            window_data: Preprocessed window [1, 300, 84] (padded to max length)
            
        Returns:
            Dict with top-K predictions
        """
        if window_data is None:
            return None
        
        # Validate shape dimensions (flexible on time dimension)
        if len(window_data.shape) != 3:
            print(f"(HonoursModelOwner) Error: Expected 3D array [batch, time, features], got {window_data.shape}")
            return None
        
        batch_size, seq_len, features = window_data.shape
        
        if batch_size != 1:
            print(f"(HonoursModelOwner) Warning: Batch size is {batch_size}, expected 1")
        
        if features != 84:
            print(f"(HonoursModelOwner) Error: Expected 84 features, got {features}")
            return None
        
        if seq_len != 300:
            print(f"(HonoursModelOwner) Warning: Sequence should be padded to 300, got {seq_len}. Model may fail.")
        
        # Run prediction asynchronously
        try:
            print(f"🤖 MODEL PROCESSING: Input shape {window_data.shape}")
            predictions = await asyncio.to_thread(
                self.model.predict,
                window_data,
                verbose=0
            )
            
            # predictions shape: [1, num_classes]
            probs = predictions[0]
            
            # Get top-K predictions
            top_k_results = self._get_top_k_predictions(probs)
            
            return top_k_results
            
        except Exception as e:
            print(f"(HonoursModelOwner) Error during prediction: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_top_k_predictions(self, probs):
        """
        Extract top-K predictions from probability array.
        
        Args:
            probs: Probability array [num_classes]
            
        Returns:
            Dict with top-K predictions and metadata
        """
        # Get top-K indices
        top_k_indices = np.argsort(probs)[-self.top_k:][::-1]
        
        # Build results
        top_k_predictions = []
        for idx in top_k_indices:
            label = self.inv_label_map.get(int(idx), f"UNKNOWN_{idx}")
            confidence = float(probs[idx])
            
            top_k_predictions.append({
                'label': label,
                'confidence': confidence,
                'index': int(idx)
            })
        
        # Get top-1 for quick access
        top_1 = top_k_predictions[0]
        
        return {
            'top1': top_1,
            'top5': top_k_predictions,
            'top1_label': top_1['label'],
            'top1_confidence': top_1['confidence'],
            'model_output': top_k_predictions  # For compatibility
        }
    
    def predict_sync(self, window_data):
        """
        Synchronous prediction (for testing).
        
        Args:
            window_data: Preprocessed window [1, 300, 84] (padded to max length)
            
        Returns:
            Dict with top-K predictions
        """
        if window_data is None:
            return None
        
        predictions = self.model.predict(window_data, verbose=0)
        probs = predictions[0]
        return self._get_top_k_predictions(probs)
    
    def get_label_name(self, index):
        """
        Get label name from index.
        
        Args:
            index: Class index
            
        Returns:
            Label string
        """
        return self.inv_label_map.get(index, f"UNKNOWN_{index}")
    
    def get_model_info(self):
        """
        Get model information for debugging.
        
        Returns:
            Dict with model metadata
        """
        return {
            'model_path': self.model_path,
            'num_classes': self.num_classes,
            'top_k': self.top_k,
            'input_shape': str(self.model.input_shape),
            'output_shape': str(self.model.output_shape),
            'labels': list(self.label_map.keys())
        }


