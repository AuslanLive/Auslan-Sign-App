import numpy as np

# Parameters for the new BiLSTM model
TARGET_FRAMES = 48  # Fixed sequence length
FEATURE_DIM = 84    # 42 hand keypoints * 2 coordinates (x, y)
HAND_LANDMARKS = 21 # MediaPipe hand landmarks per hand
THRESHOLD = 0.05    # Motion threshold for word segmentation
WINDOW_SIZE = 15    # Pause detection window
HANDS_DOWN_THRESHOLD = 0.02
HANDS_DOWN_TIME = 30

class InputParser:
    def __init__(self, threshold=THRESHOLD, window_size=WINDOW_SIZE):
        self.threshold = threshold
        self.window_size = window_size
        self.pause_count = 0
        self.previous_keypoints = None
        self.current_chunk = []
        self.handsDownCounter = 0
        self.endOfPhrase = False
        
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

    def calculate_velocity(self, keypoints_current, keypoints_previous):
        """Calculate the velocity of keypoints between two frames."""
        if keypoints_previous is None:
            return 0.0
        
        # Reshape to (42, 2) for velocity calculation
        current_reshaped = keypoints_current.reshape(42, 2)
        previous_reshaped = keypoints_previous.reshape(42, 2)
        
        velocities = np.linalg.norm(current_reshaped - previous_reshaped, axis=1)
        return np.mean(velocities)

    def hands_down(self, keypoints):
        """Check if both hands are below a certain threshold."""
        # Reshape to (42, 2) to get y coordinates
        keypoints_reshaped = keypoints.reshape(42, 2)
        
        # Get left and right hand y coordinates
        left_hand_y = keypoints_reshaped[:21, 1]  # Left hand y coordinates
        right_hand_y = keypoints_reshaped[21:, 1]  # Right hand y coordinates
        
        left_hand_avg_y = np.mean(left_hand_y)
        right_hand_avg_y = np.mean(right_hand_y)
        
        return left_hand_avg_y < HANDS_DOWN_THRESHOLD and right_hand_avg_y < HANDS_DOWN_THRESHOLD

    def pad_sequence(self, sequence, target_length=TARGET_FRAMES):
        """
        Pad or trim sequence to target length
        Args:
            sequence: list of frames
            target_length: target sequence length (48)
        Returns:
            numpy array of shape (target_length, 84)
        """
        if len(sequence) == 0:
            return np.zeros((target_length, FEATURE_DIM), dtype=np.float32)
        
        if len(sequence) >= target_length:
            # Trim to target length
            return np.array(sequence[:target_length], dtype=np.float32)
        else:
            # Pad with zeros
            padded = np.zeros((target_length, FEATURE_DIM), dtype=np.float32)
            padded[:len(sequence)] = sequence
            return padded

    def process_frame(self, frame):
        """
        Process a single frame of keypoint data for the BiLSTM model
        Args:
            frame: dict with 'keypoints' containing [pose, left_hand, right_hand]
        Returns:
            tuple: (processed_chunk, end_of_phrase_flag)
        """
        # Extract hands from frame
        keypoints_data = frame['keypoints']
        left_hand = keypoints_data[1] if len(keypoints_data) > 1 else None  # Index 1 is left hand
        right_hand = keypoints_data[2] if len(keypoints_data) > 2 else None  # Index 2 is right hand
        
        # Combine hands into required format
        current_keypoints, current_mask = self.combine_hands(left_hand, right_hand)
        
        chunk_result = None
        locEOP = False
        
        # Check if hands are down
        if self.hands_down(current_keypoints):
            self.handsDownCounter += 1
            if self.handsDownCounter >= HANDS_DOWN_TIME:
                chunk_result, locEOP = self.end_phrase()
                return chunk_result, locEOP
            return None, False
        else:
            self.handsDownCounter = 0
        
        # Add frame to current chunk
        self.current_chunk.append(current_keypoints)
        
        # Check for motion and word boundaries
        if self.previous_keypoints is not None:
            velocity = self.calculate_velocity(current_keypoints, self.previous_keypoints)
            
            if velocity < self.threshold:
                self.pause_count += 1
            else:
                self.pause_count = 0
            
            # End chunk if pause detected or max length reached
            if self.pause_count >= self.window_size or len(self.current_chunk) >= TARGET_FRAMES:
                chunk_result, locEOP = self.save_chunk()
                self.current_chunk = []
                self.pause_count = 0
        
        self.previous_keypoints = current_keypoints
        
        return chunk_result, locEOP

    def save_chunk(self):
        """
        Save the current chunk in the required format for the BiLSTM model
        Returns:
            tuple: (processed_chunk, end_of_phrase_flag)
        """
        if len(self.current_chunk) == 0:
            return None, False
        
        # Pad sequence to 48 frames
        padded_chunk = self.pad_sequence(self.current_chunk, TARGET_FRAMES)
        
        return padded_chunk, False

    def end_phrase(self):
        """End the current phrase and save the chunks."""
        self.call_func()
        return None, True

    def call_func(self):
        """Reset the parser state."""
        self.reset()

    def reset(self):
        """Reset the state for the next real-time session."""
        self.pause_count = 0
        self.previous_keypoints = None
        self.current_chunk = []
        self.handsDownCounter = 0
        self.endOfPhrase = False