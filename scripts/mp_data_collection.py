import cv2
import mediapipe as mp
import json
import os
from glob import glob

# Initialize Model
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

# Directories for input output
input_dir = 'data/practice_signs'  # Change this to your directory with videos
output_dir = 'data/practice_signs_keypoints'        # Directory to save JSON files

# Make sure directory is real
os.makedirs(output_dir, exist_ok=True)

# List Video files
video_files = glob(os.path.join(input_dir, '*.mov'))  # Change extension if needed

# Fill non-present model arrays
def fill_zeroes(num_lm):
    return[{'x':0,'y':0,'z':0,"visibility":0} for point in range(num_lm)]

# add function to complete missing keypoints
def fill_keypoints(lms, total_lms):
    if lms is None:
        return fill_zeroes(total_lms)
    keypoints = [{'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility} for lm in lms.landmark]
    while len(keypoints) < total_lms:
        keypoints.append({'x': 0, 'y': 0, 'z': 0, 'visibility': 0})
    return keypoints

# Process each video
for video_file in video_files:
    # Extract video name
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    
    # Open the video file
    cap = cv2.VideoCapture(video_file)
    
    # Initialize dictionary to store keypoints for each frame
    keypoints_data = []

    # Initialize the Holistic model
    with mp_holistic.Holistic(static_image_mode=False, 
                              model_complexity=1, 
                              smooth_landmarks=True, 
                              min_detection_confidence=0.5, 
                              min_tracking_confidence=0.5) as holistic:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Convert the BGR frame to RGB for Mediapipe processing
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process the frame with the Holistic model
            results = holistic.process(frame_rgb)

            # Initialize a dictionary for the current frame's keypoints
            frame_keypoints = {'frame': frame_idx}

            # Extract pose landmarks (ensure 33 keypoints)
            frame_keypoints['pose_landmarks'] = fill_keypoints(results.pose_landmarks, 33)

            # Extract left hand landmarks (ensure 21 keypoints)
            frame_keypoints['left_hand_landmarks'] = fill_keypoints(results.left_hand_landmarks, 21)

            # Extract right hand landmarks (ensure 21 keypoints)
            frame_keypoints['right_hand_landmarks'] = fill_keypoints(results.right_hand_landmarks, 21)

            # Append keypoint data and increment frame index
            keypoints_data.append(frame_keypoints)
            frame_idx += 1

    # Save keypoints to JSON file
    json_output_path = os.path.join(output_dir, f"{video_name}_keypoints.json")
    with open(json_output_path, 'w') as f:
        json.dump(keypoints_data, f, indent=4)

    cap.release()

print(f"Collected Keypoints from {len(video_files)} Videos")