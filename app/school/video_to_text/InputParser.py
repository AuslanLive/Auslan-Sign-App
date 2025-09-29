import numpy as np

# Parameters for the new BiLSTM model with sliding window
TARGET_FRAMES = 48  # Fixed sequence length
FEATURE_DIM = 84    # 42 hand keypoints * 2 coordinates (x, y)
HAND_LANDMARKS = 21 # MediaPipe hand landmarks per hand

# Sliding window parameters
WINDOW_STRIDE = 2    # Update every 2 frames
ACT_HIGH = 0.30      # High activity threshold (mask fraction)
ACT_LOW = 0.15       # Low activity threshold
MIN_ACTIVE_LENGTH = 24  # Minimum active frames before commit
MIN_CONFIDENCE = 0.75   # Minimum confidence for word commitment
STABILITY_CHECKS = 3    # Number of consecutive checks for same top-1
REFRACTORY_FRAMES = 8   # Frames to ignore after word commit

class InputParser:
    def __init__(self):
        # Ring buffer for sliding window
        self.ring_buffer = np.zeros((TARGET_FRAMES, FEATURE_DIM), dtype=np.float32)
        self.mask_buffer = np.zeros((TARGET_FRAMES, 42), dtype=np.float32)
        self.buffer_index = 0
        self.buffer_filled = False
        
        # Activity tracking
        self.activity_history = []
        self.is_active = False
        self.active_start_frame = 0
        self.active_frame_count = 0
        
        # Word commitment tracking
        self.prediction_history = []
        self.last_commit_frame = -REFRACTORY_FRAMES
        self.current_word_candidates = []
        
        # MediaPipe hand landmark order
        self.landmark_order = [
            'WRIST',
            'THUMB_CMC', 'THUMB_MCP', 'THUMB_IP', 'THUMB_TIP',
            'INDEX_MCP', 'INDEX_PIP', 'INDEX_DIP', 'INDEX_TIP',
            'MIDDLE_MCP', 'MIDDLE_PIP', 'MIDDLE_DIP', 'MIDDLE_TIP',
            'RING_MCP', 'RING_PIP', 'RING_DIP', 'RING_TIP',
            'PINKY_MCP', 'PINKY_PIP', 'PINKY_DIP', 'PINKY_TIP'
        ]

    def extract_hand_keypoints(self, landmarks):
        """
        Extract hand keypoints in the required order
        Args:
            landmarks: list of MediaPipe hand landmarks
        Returns:
            numpy array of shape (21, 2) - x, y coordinates
        """
        if landmarks is None or len(landmarks) == 0:
            return np.zeros((HAND_LANDMARKS, 2), dtype=np.float32)
        
        keypoints = np.zeros((HAND_LANDMARKS, 2), dtype=np.float32)
        
        for i, landmark in enumerate(landmarks):
            if i < HAND_LANDMARKS:
                keypoints[i] = [landmark['x'], landmark['y']]
        
        return keypoints

    def normalize_hand(self, keypoints):
        """
        Normalize hand keypoints: translate to wrist origin and scale by average finger length
        Args:
            keypoints: numpy array of shape (21, 2)
        Returns:
            normalized keypoints and mask indicating detected joints
        """
        if keypoints is None or len(keypoints) == 0:
            return np.zeros((HAND_LANDMARKS, 2), dtype=np.float32), np.zeros(HAND_LANDMARKS, dtype=np.float32)
        
        # Check if hand was detected (non-zero keypoints)
        mask = np.any(keypoints != 0, axis=1).astype(np.float32)
        
        if np.sum(mask) == 0:
            return np.zeros((HAND_LANDMARKS, 2), dtype=np.float32), mask
        
        # Translate to wrist origin (landmark 0)
        wrist = keypoints[0]
        translated = keypoints - wrist
        
        # Calculate scale factor from average wrist to MCP distances
        mcp_indices = [1, 5, 9, 13, 17]  # MCP joints for each finger
        mcp_distances = []
        for mcp_idx in mcp_indices:
            if mask[mcp_idx] > 0:  # Only use detected MCP joints
                dist = np.linalg.norm(translated[mcp_idx])
                mcp_distances.append(dist)
        
        if len(mcp_distances) > 0:
            scale_factor = np.mean(mcp_distances)
            if scale_factor > 0:
                normalized = translated / scale_factor
            else:
                normalized = translated
        else:
            normalized = translated
        
        return normalized.astype(np.float32), mask

    def combine_hands(self, left_hand, right_hand):
        """
        Combine left and right hand keypoints into the required format
        Args:
            left_hand: numpy array of shape (21, 2) or None
            right_hand: numpy array of shape (21, 2) or None
        Returns:
            numpy array of shape (84,) - flattened [L0.x, L0.y, ..., L20.x, L20.y, R0.x, R0.y, ..., R20.x, R20.y]
            numpy array of shape (42,) - mask for each joint
        """
        # Extract and normalize left hand
        left_keypoints = self.extract_hand_keypoints(left_hand)
        left_normalized, left_mask = self.normalize_hand(left_keypoints)
        
        # Extract and normalize right hand
        right_keypoints = self.extract_hand_keypoints(right_hand)
        right_normalized, right_mask = self.normalize_hand(right_keypoints)
        
        # Combine hands: Left first, then Right
        combined_keypoints = np.concatenate([left_normalized, right_normalized], axis=0)
        combined_mask = np.concatenate([left_mask, right_mask], axis=0)
        
        # Flatten to 84 features: [L0.x, L0.y, ..., L20.x, L20.y, R0.x, R0.y, ..., R20.x, R20.y]
        flattened = combined_keypoints.flatten()
        
        return flattened, combined_mask

    def calculate_activity_score(self, keypoints, mask):
        """
        Calculate activity score based on mask and motion
        Args:
            keypoints: numpy array of shape (84,)
            mask: numpy array of shape (42,)
        Returns:
            activity score (0.0 to 1.0)
        """
        # Mask-based activity: fraction of detected joints
        mask_activity = np.mean(mask)
        
        # Motion-based activity: difference from previous frame
        motion_activity = 0.0
        if hasattr(self, 'previous_keypoints') and self.previous_keypoints is not None:
            motion = np.linalg.norm(keypoints - self.previous_keypoints)
            motion_activity = min(motion / 0.1, 1.0)  # Normalize motion
        
        # Combine activities
        activity = max(mask_activity, motion_activity)
        return activity

    def update_ring_buffer(self, keypoints, mask):
        """
        Update the ring buffer with new frame data
        Args:
            keypoints: numpy array of shape (84,)
            mask: numpy array of shape (42,)
        """
        self.ring_buffer[self.buffer_index] = keypoints
        self.mask_buffer[self.buffer_index] = mask
        
        self.buffer_index = (self.buffer_index + 1) % TARGET_FRAMES
        if self.buffer_index == 0:
            self.buffer_filled = True

    def get_current_buffer(self):
        """
        Get the current ring buffer in the correct order
        Returns:
            tuple: (keypoints, mask) both of shape (48, 84) and (48, 42)
        """
        if not self.buffer_filled:
            # Buffer not full yet, return zeros
            return np.zeros((TARGET_FRAMES, FEATURE_DIM), dtype=np.float32), np.zeros((TARGET_FRAMES, 42), dtype=np.float32)
        
        # Reorder buffer to get chronological sequence
        ordered_keypoints = np.zeros((TARGET_FRAMES, FEATURE_DIM), dtype=np.float32)
        ordered_mask = np.zeros((TARGET_FRAMES, 42), dtype=np.float32)
        
        for i in range(TARGET_FRAMES):
            buffer_idx = (self.buffer_index + i) % TARGET_FRAMES
            ordered_keypoints[i] = self.ring_buffer[buffer_idx]
            ordered_mask[i] = self.mask_buffer[buffer_idx]
        
        return ordered_keypoints, ordered_mask

    def should_commit_word(self, prediction):
        """
        Check if a word should be committed (simplified - no confidence gating)
        Args:
            prediction: dict with 'top_1' and 'top_5' keys
        Returns:
            bool: True if word should be committed
        """
        if not prediction:
            return False
        
        # Simple commitment: just check if we have a valid prediction
        top_1 = prediction['top_1']
        if top_1 and top_1['label']:
            return True
        
        return False

    def process_frame(self, frame):
        """
        Process a single frame using sliding window approach
        Args:
            frame: dict with 'keypoints' containing [pose, left_hand, right_hand]
        Returns:
            tuple: (processed_chunk, end_of_phrase_flag)
        """
        # Extract ONLY hand keypoints (indices 1 and 2)
        keypoints_data = frame['keypoints']
        
        # Debug logging for keypoints (reduced verbosity)
        if len(self.activity_history) % 20 == 0:  # Log every 20th frame
            print(f"DEBUG: Frame {len(self.activity_history)} - keypoints with {len(keypoints_data)} components")
        
        # Only extract hand keypoints (ignore pose/face)
        left_hand = keypoints_data[1] if len(keypoints_data) > 1 else None
        right_hand = keypoints_data[2] if len(keypoints_data) > 2 else None
        
        # Combine hands into required format
        current_keypoints, current_mask = self.combine_hands(left_hand, right_hand)
        
        # Debug combined keypoints (reduced verbosity)
        if len(self.activity_history) % 20 == 0:
            print(f"DEBUG: Combined keypoints shape: {current_keypoints.shape}, non-zero: {np.count_nonzero(current_keypoints)}/{current_keypoints.size}")
        
        # Calculate activity score
        activity = self.calculate_activity_score(current_keypoints, current_mask)
        self.activity_history.append(activity)
        
        # Update ring buffer
        self.update_ring_buffer(current_keypoints, current_mask)
        
        # Check for word commitment (simplified)
        chunk_result = None
        end_of_phrase = False
        
        # Generate word segments more frequently (every 48 frames when buffer is full)
        if self.buffer_filled and len(self.activity_history) % 48 == 0:
            # Get current buffer for prediction
            buffer_keypoints, buffer_mask = self.get_current_buffer()
            chunk_result = buffer_keypoints
            print(f"CONSOLE: Word segment ready for prediction - frame: {len(self.activity_history)}")
            print(f"DEBUG: Buffer keypoints shape: {buffer_keypoints.shape}")
            print(f"DEBUG: Buffer non-zero: {np.count_nonzero(buffer_keypoints)}/{buffer_keypoints.size}")
        else:
            if len(self.activity_history) % 20 == 0:
                print(f"DEBUG: No segment - buffer_filled: {self.buffer_filled}, frame: {len(self.activity_history)}")
        
        # Update activity state
        if activity > ACT_HIGH and not self.is_active:
            self.is_active = True
            self.active_start_frame = len(self.activity_history)
            self.active_frame_count = 0
            print(f"CONSOLE: Activity started - activity: {activity:.3f}")
        elif activity < ACT_LOW and self.is_active:
            self.is_active = False
            print(f"CONSOLE: Activity ended - activity: {activity:.3f}")
        
        if self.is_active:
            self.active_frame_count += 1
        
        # Store previous keypoints for motion calculation
        self.previous_keypoints = current_keypoints
        
        return chunk_result, end_of_phrase

    def reset(self):
        """Reset the parser state for a new session"""
        self.ring_buffer.fill(0)
        self.mask_buffer.fill(0)
        self.buffer_index = 0
        self.buffer_filled = False
        self.activity_history.clear()
        self.is_active = False
        self.active_start_frame = 0
        self.active_frame_count = 0
        self.prediction_history.clear()
        self.last_commit_frame = -REFRACTORY_FRAMES
        self.current_word_candidates.clear()
        self.previous_keypoints = None