import numpy as np
# Parameters (adjust for real-time speed and accuracy)
THRESHOLD = 0.05
VISIBILITY_THRESHOLD = 0.7
VISIBILITY_COUNT = 0.5
WINDOW_SIZE = 15
MAX_CHUNK_LENGTH = 145  # Maximum length of a chunk in frames
HANDS_DOWN_THRESHOLD = 0.02
HANDS_DOWN_TIME = 30


class InputParser:
    def __init__(self, threshold=THRESHOLD, window_size=WINDOW_SIZE, buffer_size=5):
        self.threshold = threshold
        self.window_size = window_size
        self.buffer_size = buffer_size
        self.pause_count = 0
        self.previous_keypoints = None
        self.word_boundaries = []
        self.current_chunk = []
        self.chunks = []
        self.buffer = []
        self.chunk_counter = 0
        self.handsDownCounter = 0
        self.endOfPhrase = False

    @staticmethod
    def normalise_keypoints(data):
        """Normalise the keypoints data."""
        data = np.array(data)  # Convert to NumPy array
        coords = data[..., :3]  # Extract x, y, z coordinates
        min_vals = np.min(coords, axis=0, keepdims=True)
        max_vals = np.max(coords, axis=0, keepdims=True)

        # Normalise the coordinates
        normalised_coords = (coords - min_vals) / (max_vals - min_vals + 1e-8)

        normalised_data = data.copy()
        # Replace with normalised x, y, z
        normalised_data[..., :3] = normalised_coords

        return normalised_data

    @staticmethod
    def extract_keypoints(landmarks):
        """Extract the keypoints (x, y, z, visibility) from the landmarks."""
        return np.array([[landmark['x'], landmark['y'], landmark['z'], landmark['visibility']] for landmark in landmarks])

    @staticmethod
    def pad_chunk(chunk, max_length=MAX_CHUNK_LENGTH):
        """Pads the chunk with the last frame to reach the max length of frames."""
        chunk_length = len(chunk)  # Get the length of the chunk (a list)
        if chunk_length < max_length:
            last_frame = chunk[-1]  # Replicate the last frame
            padding_needed = max_length - chunk_length
            chunk.extend([last_frame] * padding_needed)  # Add padding
        return chunk

    @staticmethod
    def calculate_velocity(keypoints_current, keypoints_previous):
        """Calculate the velocity of keypoints between two frames."""
        velocities = np.linalg.norm(
            keypoints_current[:, :3] - keypoints_previous[:, :3], axis=1)
        return np.mean(velocities)

    @staticmethod
    def visibility_check(keypoints):
        """Check if the visibility of keypoints is above a threshold."""
        visible_keypoints_count = (
            keypoints[..., 3] >= VISIBILITY_THRESHOLD).sum()
        total_keypoints = len(keypoints[..., 3])
        return visible_keypoints_count >= total_keypoints * VISIBILITY_COUNT

    @staticmethod
    def hands_down(left_hand, right_hand):
        """Check if both hands are below a certain threshold."""
        left_hand_y = np.mean(left_hand[:, 1])
        right_hand_y = np.mean(right_hand[:, 1])
        return left_hand_y < HANDS_DOWN_THRESHOLD and right_hand_y < HANDS_DOWN_THRESHOLD

    def combine_keypoints(self, frame):
        """Combine pose, left hand, and right hand keypoints into a single array."""
        full_data = []
        for index, keypoints in enumerate(frame):
            if keypoints is not None:
                full_data += keypoints
                continue

            pose_number = 33 if index == 0 else 21
            full_data += [{'x': 0, 'y': 0, 'z': 0, 'visibility': 0}
                          for _ in range(pose_number)]

        extracted_data = self.extract_keypoints(full_data)
        return self.normalise_keypoints(extracted_data)

    def process_frame(self, frame):
        """Process a single frame of keypoint data in real-time."""
        keypoints_current = self.combine_keypoints(frame['keypoints'])
        chunk_result = None
        locEOP = False

        if self.hands_down(keypoints_current[33:53], keypoints_current[54:74]):
            self.handsDownCounter += 1
            if self.handsDownCounter >= HANDS_DOWN_TIME:
                chunk_result, locEOP = self.end_phrase()
                return chunk_result, locEOP
            return None, False
        else:
            self.handsDownCounter = 0

        frame['data'] = keypoints_current.tolist()

        if self.previous_keypoints is not None:
            velocity = self.calculate_velocity(
                keypoints_current, self.previous_keypoints)

            if velocity < self.threshold:
                self.pause_count += 1
            else:
                self.pause_count = 0

            if self.pause_count >= self.window_size or len(self.current_chunk) >= MAX_CHUNK_LENGTH:
                chunk_result, locEOP = self.save_chunk(self.current_chunk)
                self.current_chunk = []
                self.pause_count = 0
            else:
                self.buffer = []

        self.current_chunk.append(frame)
        self.previous_keypoints = keypoints_current

        return chunk_result, locEOP

    def save_chunk(self, chunk):
        """Save the current chunk to a JSON file in the specified format, padding it to 145 frames."""
        padded_chunk = self.pad_chunk(chunk)
        chunk_data = [frame['data'] for frame in padded_chunk]
        padded_np_arr = np.array(chunk_data)
        final_chunk = padded_np_arr.reshape(145, 75, 4)
        return final_chunk, False

    def end_phrase(self):
        """End the current phrase and save the chunks to a file."""
        self.call_func()
        return None, True

    # IMPORTANT DO NOT DELETE
    def call_func(self):
        self.reset()

    def reset(self):
        """Reset the state for the next real-time session."""
        self.pause_count = 0
        self.previous_keypoints = None
        self.current_chunk = []
        self.chunks = []
        self.word_boundaries = []
        self.buffer = []
        self.handsDownCounter = 0
