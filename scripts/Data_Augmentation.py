import os
import cv2
import numpy as np

# Define the paths to the input and output video directories
input_dir = 'data/New_Gloss_RGB_Data'  # Change this to your directory with videos
output_dir = 'data/augmented_vid'        # Directory to save new video files
output_dir_drop = 'data/augmented_drop'     # Directory for frame drop augmented videos
output_dir_warp = 'data/augmented_warp'     # Directory for time warp augmented videos

# Define augmentation functions
def random_rotate(frame, angle=10):
    """Rotate the frame by a random angle between -angle and angle (less drastic)."""
    h, w = frame.shape[:2]
    center = (w // 2, h // 2)
    angle = np.random.uniform(-angle, angle)  # Smaller range for less drastic rotation
    rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated_frame = cv2.warpAffine(frame, rot_matrix, (w, h))
    return rotated_frame

def random_resize(frame, scale=0.05):
    """Resize the frame by a random factor between 1-scale and 1+scale (less drastic)."""
    h, w = frame.shape[:2]
    scale_factor = np.random.uniform(1 - scale, 1 + scale)  # Smaller range for subtle resizing
    resized_frame = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
    
    # Crop or pad the frame back to the original size
    if resized_frame.shape[0] > h or resized_frame.shape[1] > w:
        # Crop
        resized_frame = resized_frame[:h, :w]
    else:
        # Pad
        pad_h = h - resized_frame.shape[0]
        pad_w = w - resized_frame.shape[1]
        resized_frame = np.pad(resized_frame, ((0, pad_h), (0, pad_w), (0, 0)), 'constant', constant_values=0)
    
    return resized_frame

def frame_drop(frames, drop_prob=0.1):
    """Randomly drop frames from the video sequence."""
    return [frame for frame in frames if np.random.rand() > drop_prob]

def time_warp(frames, speed_factor=1.2):
    """Randomly speed up or slow down the video by a speed factor."""
    indices = np.round(np.arange(0, len(frames), speed_factor)).astype(int)
    indices = np.clip(indices, 0, len(frames) - 1)
    return [frames[i] for i in indices]


def augment_and_save_videos(input_dir, output_dir, augmentation_func):
    #Applies augmentation_func to each video in input_dir and saves it to output_dir.
    # Loop over each video file in the input directory
    for file in os.listdir(os.path.join(input_dir)):
        video_path = os.path.join(input_dir, file)
        # Load the video file
        cap = cv2.VideoCapture(video_path)

        # Define the output video writer
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_path = os.path.join(output_dir, file)
        out = cv2.VideoWriter(out_path, fourcc, fps, frame_size)

        # Collect all frames of the video
        frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            else:
                break
        cap.release()

        # Apply augmentation function to frames
        augmented_frames = augmentation_func(frames)

        # Write augmented frames to new video
        for frame in augmented_frames:
            out.write(frame)
        out.release()

#apply Frame drop augment
#augment_and_save_videos(input_dir,output_dir_drop, frame_drop)
#apply Time warp augment
augment_and_save_videos(input_dir,output_dir_warp, time_warp)