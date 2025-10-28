"""
HonoursInputParser.py
change d to 32 caise model is trained for it
Handles:
- Hands-only keypoint extraction
- Variable-length window collection (32-300 frames)
- Flexible window sizes for fast/slow signing
- Hand detection quality checks
"""

import numpy as np
from collections import deque
from app.school.video_to_text.KeypointPreprocessor import KeypointPreprocessor


# Configuration for variable-length model
MIN_FRAMES = 32             # Minimum frames to trigger prediction (1.1s @ 30fps)
MAX_FRAMES = 300            # Maximum frames allowed (10s @ 30fps)
HANDS_OUT_TIME = 15         # Frames with hands out to trigger prediction (~0.5s @ 30fps)
HANDS_OUT_GRACE = 5         # Grace period frames to ignore brief hand losses
MAX_WORD_DURATION = 150     # Max frames for a single word (5 seconds)
MIN_HAND_CONFIDENCE = 0.5   # Minimum MediaPipe detection confidence


class HonoursInputParser:
    """
    Processes incoming hand keypoints and creates variable-length windows for the honors model.
    Uses hands-out-of-frame detection for natural word boundaries.
    - Collects frames while hands are in frame
    - Triggers prediction when hands exit frame
    - Supports 32-150 frame sequences per word
    """
    
    def __init__(self, stats_path):
        """
        Initialize the parser with preprocessing.
        
        Args:
            stats_path: Path to stats.json for normalization
        """
        self.preprocessor = KeypointPreprocessor(stats_path)
        
        # Variable-length frame buffer for current word
        self.frame_buffer = deque(maxlen=MAX_WORD_DURATION)
        self.frame_counter = 0
        
        # Hands out of frame detection
        self.hands_out_counter = 0
        self.is_signing = False  # Track if user is actively signing
        
        # Store frame data
        self.current_frames = []
        
    def is_hands_out(self, left_hand, right_hand):
        """
        Check if both hands are out of frame (not detected).
        
        Args:
            left_hand: Left hand landmarks or None
            right_hand: Right hand landmarks or None
            
        Returns:
            bool: True if both hands are out of frame
        """
        # Both hands must be None (out of frame)
        return left_hand is None and right_hand is None
    
    def check_hand_quality(self, left_hand, right_hand):
        """
        Check if hand detection quality is sufficient.
        
        Args:
            left_hand: Left hand landmarks or None
            right_hand: Right hand landmarks or None
            
        Returns:
            bool: True if quality is acceptable
        """
        # At least one hand should be detected
        return left_hand is not None or right_hand is not None
    
    def process_frame(self, frame_data):
        """
        Process a single frame of hand keypoints with hands-out-of-frame detection.
        
        Args:
            frame_data: Dict with 'keypoints' containing hand data
            
        Returns:
         (window_data, word_ended_flag)
            - window_data: Preprocessed [1, 300, 84] array (padded) or None
            - word_ended_flag: Bool indicating if word ended (hands out of frame)
        """
        try:
            # Extract hand keypoints from frame
            keypoints = frame_data.get('keypoints', {})
            left_hand = keypoints.get('leftHand')
            right_hand = keypoints.get('rightHand')
            
            # Check if hands are out of frame
            if self.is_hands_out(left_hand, right_hand):
                self.hands_out_counter += 1
                
                # If we were signing and hands have been out for enough frames
                if self.is_signing and self.hands_out_counter >= HANDS_OUT_TIME:
                    # Check if we have enough frames for a word
                    if len(self.frame_buffer) >= MIN_FRAMES:
                    
                        print(f"\n🤚  Hands out detected! ({len(self.frame_buffer)} frames collected)")
                        print(f"   Sending to model for prediction...\n")
                        window_data = self.create_window()
                        self.reset()  # Clear buffer for next word
                        return window_data, True
                    else:
                        # Not enough frames, just reset
                        self.reset()
                        return None, False
                
                # Still waiting for hands to be out long enough
                return None, False
            else:
                # Hands are in frame
                self.hands_out_counter = 0
                self.is_signing = True
                
                # Check hand detection quality
                if not self.check_hand_quality(left_hand, right_hand):
                    # Poor quality frame, skip but don't reset
                    return None, False
                
                # Store frame data
                frame_dict = {
                    'leftHand': left_hand,
                    'rightHand': right_hand,
                    'frame_num': self.frame_counter
                }
                
                self.frame_buffer.append(frame_dict)
                self.current_frames.append(frame_dict)
                self.frame_counter += 1
                
                # Safety: If word is getting too long, trigger prediction
                if len(self.frame_buffer) >= MAX_WORD_DURATION:
                    window_data = self.create_window()
                    self.reset()  # Clear for next word
                    return window_data, True
                
                return None, False
            
        except Exception as e:
            print(f"Error processing frame in HonoursInputParser: {e}")
            import traceback
            traceback.print_exc()
            return None, False
    
    def create_window(self):
        """
        Create a variable-length window from all collected frames and preprocess it.
        
        Returns:
            Preprocessed window [1, 300, 84] (padded to model's max length)
        """
        buffer_len = len(self.frame_buffer)
        
        # Need at least MIN_FRAMES
        if buffer_len < MIN_FRAMES:
            return None
        
        # Take all frames in buffer (they represent the complete word)
        window_frames = list(self.frame_buffer)
        
        # Preprocess the variable-length window (will pad to 300)
        try:
            preprocessed = self.preprocessor.preprocess_sequence(window_frames)
            return preprocessed
        except Exception as e:
            print(f"Error preprocessing window in create_window: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def reset(self):
        """
        Reset parser state for next word.
        """
        self.frame_buffer.clear()
        self.current_frames = []
        self.hands_out_counter = 0
        self.is_signing = False
        # Don't reset frame_counter - it's cumulative for debugging
    
    def get_buffer_status(self):
        """
        Get current buffer status for debugging/UI feedback.
        
        Returns:
            Dict with buffer information
        """
        return {
            'frames_collected': len(self.frame_buffer),
            'min_frames': MIN_FRAMES,
            'max_frames': MAX_WORD_DURATION,
            'is_signing': self.is_signing,
            'hands_out_count': self.hands_out_counter,
            'hands_out_needed': HANDS_OUT_TIME,
            'ready_to_predict': len(self.frame_buffer) >= MIN_FRAMES and self.hands_out_counter >= HANDS_OUT_TIME
        }


