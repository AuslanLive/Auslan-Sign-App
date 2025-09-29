import os
import tempfile
import firebase_admin
from firebase_admin import credentials, storage
from app.school.text_to_animation.pose_format.pose import Pose
from app.school.text_to_animation.pose_format.pose_visualizer import PoseVisualizer
import io
import cv2
from concurrent.futures import ProcessPoolExecutor
from app.school.text_to_animation.spoken_to_signed.gloss_to_pose import concatenate_poses
from dotenv import load_dotenv
import numpy as np
import subprocess


# Load environment variables from the .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'app', '.env'))

# Retrieve credentials from environment variables
firebase_credentials = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
}

# Check if any credential is missing
if None in firebase_credentials.values():
    raise ValueError("Firebase credentials not found in .env file.")

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {'storageBucket': 'auslan-194e5.appspot.com'})

# Process pose file from Firebase Storage
def process_pose_file(blob_name):
    try:
        bucket = storage.bucket()
        # Assuming each word corresponds to a .pose file
        blob = bucket.blob(f"{blob_name}.pose")
        if not blob.exists():
            print(f"Blob {blob_name} does not exist.")
            return None

        data_buffer = io.BytesIO()
        blob.download_to_file(data_buffer)
        data_buffer.seek(0)
        pose = Pose.read(data_buffer.read())
        return pose
    except Exception as e:
        print(f"Error processing {blob_name}: {e}")
        return None

# Concatenate poses and upload the video back to Firebase
def concatenate_poses_and_upload(blob_names:list, sentence:list):
    all_poses = []
    valid_filenames = []

    with ProcessPoolExecutor() as executor:
        results = executor.map(process_pose_file, blob_names)

    for pose, blob_name in zip(results, blob_names):
        if pose:
            all_poses.append(pose)
            valid_filenames.append(os.path.splitext(
                os.path.basename(blob_name))[0])

    if len(all_poses) >= 1:
        concatenated_pose, frame_ranges = concatenate_poses(
            all_poses, valid_filenames)
        visualizer = PoseVisualizer(concatenated_pose)

        temp_video_path = os.path.join(tempfile.gettempdir(), f"{sentence}.gif")
        width  = visualizer.pose.header.dimensions.width
        height = visualizer.pose.header.dimensions.height
        fps    = visualizer.pose_fps

        print("Generation video ...")
        def frames_from_pose(visualizer: PoseVisualizer, frame_ranges):
            for frame in visualizer.draw_frame_with_filename(frame_ranges):
                yield frame  # raw BGR

        print("Uploading to firebase ... ")
        url = mp4_to_firebase(frames_from_pose(visualizer, frame_ranges), width, height, fps,  f"output_videos/{sentence}.mp4")
      
        print(f"Video uploaded to Firebase at 'output_videos/{sentence}.mp4' and accessible at: {url}")

        return temp_video_path
    else:
        print("Not enough .pose files to concatenate")

def _first_available_encoder(encoders):
    """Return the first encoder name present in this ffmpeg build."""
    try:
        out = subprocess.check_output(["ffmpeg", "-hide_banner", "-encoders"], stderr=subprocess.STDOUT).decode("utf-8", errors="ignore")
    except Exception:
        return None
    for enc in encoders:
        if enc in out:
            return enc
    return None

def mp4_to_firebase(frame_iter, width, height, fps, gcs_path,
                           resize_factor=0.5, target_fps=None):
    """
    Faster: write a seekable MP4 to a temp file using the fastest available encoder,
    then upload to Firebase Storage. Returns public URL. Filenames unchanged.

    - Tries GPU encoders (NVENC/QSV/AMF) first, falls back to libx264.
    - Uses speed-first settings; adjust CRF if you want more quality.
    """
    # Base dimensions (even for yuv420p/NVENC)
    w0, h0 = int(width), int(height)
    if resize_factor != 1.0:
        w0 = max(2, int(round(w0 * resize_factor)))
        h0 = max(2, int(round(h0 * resize_factor)))
    w = w0 + (w0 % 2)
    h = h0 + (h0 % 2)
    src_fps = float(fps)
    out_fps = float(target_fps or src_fps)

    # Pick encoder (fastest first)
    encoder = _first_available_encoder([
        "h264_nvenc",  # NVIDIA
        "h264_qsv",    # Intel QuickSync
        "h264_amf",    # AMD
        "libx264"      # CPU fallback
    ]) or "libx264"

    # Encoder-specific speed/quality knobs
    if encoder == "h264_nvenc":
        enc_args = [
            "-c:v", "h264_nvenc",
            "-preset", "p1",              # fastest
            "-tune", "ull",               # ultra low latency
            "-rc", "vbr", "-cq", "28",    # quality/size tradeoff; lower = better quality
            "-b:v", "0",
            "-pix_fmt", "yuv420p"
        ]
    elif encoder == "h264_qsv":
        enc_args = [
            "-c:v", "h264_qsv",
            "-preset", "veryfast",
            "-global_quality", "28",      # ~CRF; lower is higher quality
            "-look_ahead", "0",
            "-pix_fmt", "nv12"            # QSV friendly
        ]
    elif encoder == "h264_amf":
        enc_args = [
            "-c:v", "h264_amf",
            "-quality", "speed",
            "-usage", "ultralowlatency",
            "-rc", "vbr",
            "-qscale", "28",
            "-pix_fmt", "yuv420p"
        ]
    else:
        # libx264 (CPU) - speed first
        enc_args = [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-crf", "32",                 # raise to 34–36 for smaller/faster previews
            "-x264-params", "keyint=2*{k}:min-keyint={k}:scenecut=0:rc-lookahead=0:bframes=0".format(k=int(out_fps)),
            "-pix_fmt", "yuv420p"
        ]

    # Temp file for MP4
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(tmp_fd)

    # Input & output chain
    # - If you want to decimate FPS, we’ll push frames at src_fps but tell ffmpeg to output constant out_fps.
    # - Resize is done on the CPU before feeding (keeps ffmpeg simpler and avoids extra filters).
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24", 
           "-s", f"{w}x{h}", "-r", f"{out_fps}", "-i", "-", "-an", *enc_args, "-movflags", "+faststart", tmp_path]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10_000_000)

        # Feed frames
        try:
            frame_idx = 0
            for frame in frame_iter:
                if frame.shape[1] != w or frame.shape[0] != h:
                    frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
                proc.stdin.write(frame.astype(np.uint8).tobytes())
            proc.stdin.close()
        except BrokenPipeError:
            pass

        ret = proc.wait()
        if ret != 0:
            stderr_data = proc.stderr.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"ffmpeg failed (code {ret}). stderr:\n{stderr_data}")

        # Upload seekable MP4
        bucket = storage.bucket()
        blob = bucket.blob(gcs_path)
        blob.cache_control = "public, max-age=31536000"
        blob.upload_from_filename(tmp_path, content_type="video/mp4")
        blob.make_public()
        return blob.public_url

    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

# Check if a word has a corresponding pose file in Firebase
def get_valid_blobs_from_sentence(sentence):
    """Get valid blob names from the sentence.

    Args:
        sentence (list): The input sentence's words, as a list.

    Returns:
        list: A list of valid blob names.
    """
    
    # if sentence is a string, return
    if isinstance(sentence, str):
        print("(pose_video_creator) Input sentence is a string, expected a list of words.")
        return
    
    print("(pose_video_creator) Checking for valid pose files in Firebase Storage...")
    
    valid_blob_names = []

    bucket = storage.bucket()

    for word in sentence:
        # Check lowercase, capitalized, and title case versions of the word
        lowercase_blob = bucket.blob(f"{word.lower()}.pose")
        capitalized_blob = bucket.blob(f"{word.capitalize()}.pose")
        regular_case_blob = bucket.blob(f"{word}.pose")
        
        print(f"(pose_video_creator) Checking blobs for word '{word}': TITLE | "
              f"{regular_case_blob.name}")

        if lowercase_blob.exists():
            valid_blob_names.append(word.lower())  # Add lowercase if exists
        elif capitalized_blob.exists():
            # Add capitalized if exists
            valid_blob_names.append(word.capitalize())
        elif regular_case_blob.exists():
            valid_blob_names.append(word)
        else:
            print(f"(pose_video_creator) Skipping word '{word}', no corresponding .pose file found.")

    print(f"(pose_video_creator) Valid blob names found: {valid_blob_names}")
    return valid_blob_names


def process_sentence(sentence):
    # Get valid blob names (i.e., words that have a corresponding .pose file)
    valid_blob_names = get_valid_blobs_from_sentence(sentence)

    if len(valid_blob_names) == 0:
        print("(pose_video_creator) No valid words found with corresponding .pose files.")
        return None

    # Get the path to the temporary video file
    temp_video_path = concatenate_poses_and_upload(valid_blob_names, sentence)

    if temp_video_path:
        print(f"Video saved at {temp_video_path}")
        return temp_video_path
    else:
        print("Not enough .pose files to concatenate")
        return None
   
if __name__ == "__main__":
    # Example usage: replace with actual API response
    api_response_sentence = "I do himself make first new greatest little hers last day their"
    process_sentence(api_response_sentence)
