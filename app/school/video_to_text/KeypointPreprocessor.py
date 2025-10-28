"""
KeypointPreprocessor.py

This model expects:
- 21 landmarks per hand (42 total)
- Per-hand wrist centering
- Per-hand MCP-based scaling
- Z-score normalization using precomputed stats
- Shape: [T, 84] where T is 32-300 frames, 84 = 42 keypoints × 2 coords (x,y)
"""

import numpy as np
import json


class KeypointPreprocessor:
    """
    Preprocesses hand keypoints for the variable-length honors model.
    Applies wrist centering, MCP scaling, and z-score normalization.
    Supports sequences of 32-300 frames.
    """
    
    # MediaPipe hand landmark indices
    WRIST = 0
    MCP_INDICES = [5, 9, 13, 17]  # INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP
    NUM_HAND_LANDMARKS = 21
    
    def __init__(self, stats_path):
        """
        Initialize preprocessor with normalization statistics.
        
        Args:
            stats_path: Path to stats.json containing mean and std
        """
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        
        self.mean = np.array(stats['mean'], dtype=np.float32)
        self.std = np.array(stats['std'], dtype=np.float32)
        
        # Avoid division by zero
        self.std[self.std < 1e-6] = 1.0
        
    def extract_hand_coords(self, hand_landmarks):
        """
        Extract x,y coordinates from hand landmarks.
        
        Args:
            hand_landmarks: List of 21 landmarks with x, y, z properties
            
        Returns:
            np.array of shape [21, 2] with x,y coordinates
        """
        if hand_landmarks is None or len(hand_landmarks) == 0:
            return None
        
        if len(hand_landmarks) != self.NUM_HAND_LANDMARKS:
            print(f"Warning: Expected 21 landmarks, got {len(hand_landmarks)}")
            return None
        
        coords = np.zeros((self.NUM_HAND_LANDMARKS, 2), dtype=np.float32)
        
        try:
            for i, landmark in enumerate(hand_landmarks):
                if isinstance(landmark, dict):
                    coords[i, 0] = float(landmark.get('x', 0.0))
                    coords[i, 1] = float(landmark.get('y', 0.0))
                else:
                    coords[i, 0] = float(getattr(landmark, 'x', 0.0))
                    coords[i, 1] = float(getattr(landmark, 'y', 0.0))
        except (AttributeError, TypeError, ValueError) as e:
            print(f"Error extracting hand coords: {e}")
            return None
        
        return coords
    
    def center_by_wrist(self, hand_coords):
        """
        Center hand coordinates by subtracting the wrist position.
        
        Args:
            hand_coords: [21, 2] array of hand coordinates
            
        Returns:
            Centered coordinates [21, 2]
        """
        if hand_coords is None:
            return None
        
        wrist_pos = hand_coords[self.WRIST]  # [2]
        centered = hand_coords - wrist_pos
        return centered
    
    def scale_by_mcp(self, hand_coords):
        """
        Scale hand coordinates by average distance from wrist to MCP knuckles.
        This removes person scale / camera distance effects.
        
        Args:
            hand_coords: [21, 2] centered hand coordinates
            
        Returns:
            Scaled coordinates [21, 2]
        """
        if hand_coords is None:
            return None
        
        # Already centered, so wrist is at [0, 0]
        wrist_pos = np.zeros(2)
        
        # Calculate distances from wrist to each MCP
        distances = []
        for mcp_idx in self.MCP_INDICES:
            mcp_pos = hand_coords[mcp_idx]
            dist = np.linalg.norm(mcp_pos - wrist_pos)
            distances.append(dist)
        
        # Average distance
        avg_distance = np.mean(distances)
        
        # Avoid division by zero
        if avg_distance < 1e-6:
            avg_distance = 1.0
        
        # Scale all coordinates
        scaled = hand_coords / avg_distance
        return scaled
    
    def process_hand(self, hand_landmarks):
        """
        Complete preprocessing pipeline for a single hand.
        
        Args:
            hand_landmarks: List of 21 landmarks or None if hand not detected
            
        Returns:
            Flattened features [42] or None if hand missing
        """
        if hand_landmarks is None:
            return None
        
        # Extract x,y coordinates
        coords = self.extract_hand_coords(hand_landmarks)
        if coords is None:
            return None
        
        # Center by wrist
        centered = self.center_by_wrist(coords)
        
        # Scale by MCP distance
        scaled = self.scale_by_mcp(centered)
        
        # Flatten to [42] (21 landmarks × 2 coords)
        flattened = scaled.reshape(-1)
        
        return flattened
    
    def process_frame(self, left_hand, right_hand):
        """
        Process both hands for a single frame.
        
        Args:
            left_hand: List of 21 landmarks or None
            right_hand: List of 21 landmarks or None
            
        Returns:
            Combined features [84] and mask [84]
        """
        # Process each hand
        left_features = self.process_hand(left_hand)
        right_features = self.process_hand(right_hand)
        
        # Create feature array [84]
        features = np.zeros(84, dtype=np.float32)
        mask = np.zeros(84, dtype=np.float32)
        
        # Left hand: indices 0-41
        if left_features is not None:
            features[0:42] = left_features
            mask[0:42] = 1.0
        
        # Right hand: indices 42-83
        if right_features is not None:
            features[42:84] = right_features
            mask[42:84] = 1.0
        
        # Apply mask (zero out missing hands)
        features = features * mask
        
        return features, mask
    
    def normalize_sequence(self, sequence):
        """
        Apply z-score normalization to a sequence of frames.
        
        Args:
            sequence: [T, 84] array of features
            
        Returns:
            Normalized sequence [T, 84]
        """
        # Apply z-score normalization
        normalized = (sequence - self.mean) / self.std
        return normalized.astype(np.float32)
    
    def preprocess_sequence(self, frames_data):
        """
        Complete preprocessing for a variable-length sequence of frames.
        
        Args:
            frames_data: List of dicts with 'leftHand' and 'rightHand' keys (length T=32-300)
            
        Returns:
            Preprocessed sequence ready for model [1, 300, 84] (padded to max length)
        """
        MAX_T = 300  # Model expects padded sequences
        features_list = []
        
        try:
            for frame in frames_data:
                left_hand = frame.get('leftHand')
                right_hand = frame.get('rightHand')
                
                features, mask = self.process_frame(left_hand, right_hand)
                features_list.append(features)
            
            # Stack into [T_actual, 84]
            sequence = np.stack(features_list, axis=0)
            T_actual = sequence.shape[0]
            
            # Normalize
            normalized = self.normalize_sequence(sequence)
            
       
            if T_actual < MAX_T:
                padding = np.zeros((MAX_T - T_actual, 84), dtype=np.float32)
                normalized = np.vstack([normalized, padding])
            elif T_actual > MAX_T:
                # Truncate if somehow longer than max (shouldn't happen)
                normalized = normalized[:MAX_T]
            
            # Add batch dimension [1, 300, 84]
            batched = np.expand_dims(normalized, axis=0)
            
            return batched
            
        except Exception as e:
            print(f"Error in preprocess_sequence: {e}")
            import traceback
            traceback.print_exc()
            return None


