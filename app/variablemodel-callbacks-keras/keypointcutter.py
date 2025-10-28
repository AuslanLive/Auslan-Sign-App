from __future__ import annotations
import os, json, math, re
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import cv2
import numpy as np
from tqdm import tqdm

BASE_DIR = r"C:\Users\kabil\Downloads\Honours\New Potential Dataset\CUTDOWNNEWDATASET"
OUT_DIR  = r"C:\Users\kabil\Downloads\Honours\New Potential Dataset\variable-keypoints"

SAMPLE_STRIDE  = 2
PROCESS_EVERY  = 1
MAX_ALLOWED_FRAMES = 300
MIN_FRAMES = 15
SAVE_MOSAIC_EVERY_N_CLIPS = 30
SAVE_EVERY_10TH_FRAME      = True
CARRY_LIMIT   = 8
INTERP_LIMIT  = 4

VIDEO_DIRS = {
    'train'   : os.path.join(BASE_DIR, 'Cutdown-Train-rgb'),
    'valid'   : os.path.join(BASE_DIR, 'Cutdown-Valid-rgb'),
    'test_itw': os.path.join(BASE_DIR, 'Cutdown-Test-ITW-rgb'),
    'test_stu': os.path.join(BASE_DIR, 'Cutdown-Test-STU-rgb'),
    'test_syn': os.path.join(BASE_DIR, 'Cutdown-Test-SYN-rgb'),
    'test_ted': os.path.join(BASE_DIR, 'Cutdown-Test-TED-rgb'),
}
JSON_DIR = os.path.join(BASE_DIR, 'Cutdown-json')
JSON_IN = {
    'train'   : os.path.join(JSON_DIR, 'Train_150.json'),
    'valid'   : os.path.join(JSON_DIR, 'Valid_150.json'),
    'test_itw': os.path.join(JSON_DIR, 'Test_ITW_150.json'),
    'test_stu': os.path.join(JSON_DIR, 'Test_STU_150.json'),
    'test_syn': os.path.join(JSON_DIR, 'Test_SYN_150.json'),
    'test_ted': os.path.join(JSON_DIR, 'Test_TED_150.json'),
}

KP_ROOT   = Path(OUT_DIR)
KP_DIRS   = {
    'train'   : KP_ROOT / 'keypoints-Train',
    'valid'   : KP_ROOT / 'keypoints-Valid',
    'test_itw': KP_ROOT / 'keypoints-Test_ITW',
    'test_stu': KP_ROOT / 'keypoints-Test_STU',
    'test_syn': KP_ROOT / 'keypoints-Test_SYN',
    'test_ted': KP_ROOT / 'keypoints-Test_TED',
}
JSON_OUT  = KP_ROOT / 'Cutdown-json'
PREV_ROOT = KP_ROOT / 'previews'

for p in list(KP_DIRS.values()) + [JSON_OUT, PREV_ROOT]:
    p.mkdir(parents=True, exist_ok=True)

print(f"✓ Created output directory: {OUT_DIR}")

import mediapipe as mp
mp_hands  = mp.solutions.hands
mp_draw   = mp.solutions.drawing_utils

N_HAND   = 21
N_PER_FR = N_HAND * 2
N_DIMS   = 2

def load_json(path: str) -> Dict[str, str]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

_digit_re = re.compile(r'(\d+)')

def normalize_to_digits(s: str) -> str:
    m = _digit_re.search(s)
    return m.group(1) if m else ""

def scan_videos_by_id(root: str) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    dupe_counts: Dict[str, List[str]] = {}
    exts = ('*.mp4','*.MP4','*.m4v','*.avi','*.AVI','*.mov','*.MOV','*.mkv','*.MKV','*.webm','*.WEBM','*.wmv','*.WMV')
    for ext in exts:
        for p in Path(root).rglob(ext):
            stem = p.stem
            did  = normalize_to_digits(stem)
            if not did:
                continue
            if did in lookup:
                cur = Path(lookup[did]).stem
                if len(stem) < len(cur):
                    lookup[did] = str(p)
                dupe_counts.setdefault(did, []).append(stem)
            else:
                lookup[did] = str(p)
    if dupe_counts:
        print(f"[scan] duplicates by id: {sum(len(v) for v in dupe_counts.values())} (keeping shortest stems)")
    return lookup

def _hand_center_and_scale(pts_xy: np.ndarray) -> np.ndarray:
    if pts_xy.shape != (N_HAND, 2) or not np.any(pts_xy):
        return np.zeros((N_HAND, 2), dtype=np.float32)
    wrist = pts_xy[0, :]
    mcps  = pts_xy[[5,9,13,17], :]
    dists = np.linalg.norm(mcps - wrist, axis=1)
    scale = float(max(np.mean(dists), 1e-6))
    return (pts_xy - wrist) / scale

def _extract_hands_xy(results) -> Tuple[np.ndarray, np.ndarray]:
    L = np.zeros((N_HAND, 2), dtype=np.float32)
    R = np.zeros((N_HAND, 2), dtype=np.float32)
    if not (hasattr(results, "multi_hand_landmarks") and results.multi_hand_landmarks and
            hasattr(results, "multi_handedness") and results.multi_handedness):
        return L, R
    left_set = None
    right_set = None
    for lms, handed in zip(results.multi_hand_landmarks, results.multi_handedness):
        label = handed.classification[0].label.lower()
        if label == 'left' and left_set is None:
            left_set = lms
        elif label == 'right' and right_set is None:
            right_set = lms
    def lm_to_xy(lms):
        if lms is None:
            return np.zeros((N_HAND, 2), dtype=np.float32)
        out = []
        for lm in lms.landmark:
            x = float(np.clip(lm.x, 0.0, 1.0))
            y = float(np.clip(lm.y, 0.0, 1.0))
            out.append([x, y])
        return np.asarray(out, dtype=np.float32)
    if left_set is not None:  L = lm_to_xy(left_set)
    if right_set is not None: R = lm_to_xy(right_set)
    return L, R

def read_video_to_seq(path: str, per_frame_dir: Optional[Path] = None) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray], int]:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return np.zeros((0, 42, 2), np.float32), np.zeros((0, 42), np.uint8), [], 0
    frames: List[np.ndarray] = []
    masks : List[np.ndarray] = []
    previews: List[np.ndarray] = []
    save_counter = 0
    if per_frame_dir is not None:
        per_frame_dir.mkdir(parents=True, exist_ok=True)
    prev_L = None
    prev_R = None
    carry_L = carry_R = 0
    with mp_hands.Hands(static_image_mode=False,
                        max_num_hands=2,
                        model_complexity=1,
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5) as hands:
        idx = 0
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            if (idx % SAMPLE_STRIDE) != 0:
                idx += 1
                continue
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            res = hands.process(rgb)
            L_xy, R_xy = _extract_hands_xy(res)
            L_det = bool(np.any(L_xy))
            R_det = bool(np.any(R_xy))
            L_norm = _hand_center_and_scale(L_xy) if L_det else np.zeros((N_HAND, 2), np.float32)
            R_norm = _hand_center_and_scale(R_xy) if R_det else np.zeros((N_HAND, 2), np.float32)
            mL = np.ones(N_HAND, np.uint8) if L_det else np.zeros(N_HAND, np.uint8)
            mR = np.ones(N_HAND, np.uint8) if R_det else np.zeros(N_HAND, np.uint8)
            if not L_det and prev_L is not None and carry_L < CARRY_LIMIT:
                L_norm = prev_L.copy()
                mL[:] = 0
                carry_L += 1
            else:
                carry_L = 0
            if not R_det and prev_R is not None and carry_R < CARRY_LIMIT:
                R_norm = prev_R.copy()
                mR[:] = 0
                carry_R += 1
            else:
                carry_R = 0
            prev_L, prev_R = L_norm.copy(), R_norm.copy()
            pair = np.vstack([L_norm, R_norm]).astype(np.float32)
            mask = np.concatenate([mL, mR]).astype(np.uint8)
            frames.append(pair)
            masks.append(mask)
            if len(previews) < 6:
                draw = bgr.copy()
                if res.multi_hand_landmarks:
                    for lms in res.multi_hand_landmarks:
                        mp_draw.draw_landmarks(draw, lms, mp_hands.HAND_CONNECTIONS)
                previews.append(draw)
            if per_frame_dir is not None and SAVE_EVERY_10TH_FRAME:
                if (save_counter % 10) == 0:
                    draw = bgr.copy()
                    if res.multi_hand_landmarks:
                        for lms in res.multi_hand_landmarks:
                            mp_draw.draw_landmarks(draw, lms, mp_hands.HAND_CONNECTIONS)
                    outpng = per_frame_dir / f"f{idx:04d}.png"
                    cv2.imwrite(str(outpng), draw)
                save_counter += 1
            idx += 1
            if len(frames) >= MAX_ALLOWED_FRAMES:
                break
    cap.release()
    T = len(frames)
    if T < MIN_FRAMES:
        print(f"    Video too short ({T} frames < {MIN_FRAMES}): {path}")
        return np.zeros((0, 42, 2), np.float32), np.zeros((0, 42), np.uint8), [], 0
    if T == 0:
        return np.zeros((0, 42, 2), np.float32), np.zeros((0, 42), np.uint8), [], 0
    X = np.stack(frames, 0)
    M = np.stack(masks,  0)
    for j in range(42):
        good = M[:, j] == 1
        if good.sum() >= 2:
            edges = np.diff(np.concatenate(([0], (~good).astype(np.int8), [0])))
            runs  = np.where(edges != 0)[0].reshape(-1, 2)
            for a, b in runs:
                run_len = b - a
                if 0 < run_len <= INTERP_LIMIT and a > 0 and b < T:
                    for ax in range(2):
                        X[a:b, j, ax] = np.linspace(X[a-1, j, ax], X[b, j, ax], run_len+2)[1:-1]
    return X, M, previews, T

def save_preview_grid(frames_bgr: List[np.ndarray], out_png: Path, cols: int = 3):
    if not frames_bgr:
        return
    h, w = frames_bgr[0].shape[:2]
    rows = math.ceil(len(frames_bgr)/cols)
    grid = np.zeros((rows*h, cols*w, 3), dtype=np.uint8)
    for i, img in enumerate(frames_bgr[:rows*cols]):
        r, c = divmod(i, cols)
        grid[r*h:(r+1)*h, c*w:(c+1)*w] = img
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_png), grid)

def process_split(name: str, split_map: Dict[str,str], video_root: str, out_root: Path,
                  manifest_out: Path, previews_dir: Path, process_every: int = PROCESS_EVERY):
    lookup_by_id = scan_videos_by_id(video_root)
    pairs: List[Tuple[str, str]] = []
    missing: List[str] = []
    for json_id, gloss in split_map.items():
        did = normalize_to_digits(json_id)
        path = lookup_by_id.get(did, None)
        if path is None:
            missing.append(json_id)
        else:
            vid_stem = Path(path).stem
            pairs.append((vid_stem, gloss))
    if missing:
        print(f"[{name}] WARNING: {len(missing)} ids from JSON not found in folder {video_root}. Example: {missing[:5]}")
    pairs.sort(key=lambda x: x[0])
    kept = [pairs[i] for i in range(0, len(pairs), max(1, process_every))]
    print(f"[{name}] {len(kept)}/{len(pairs)} videos will be processed (every {process_every}th).")
    out_root.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    mosaic_counter = 0
    frame_lengths = []
    for vid_stem, gloss in tqdm(kept, desc=f"Extracting {name}"):
        src = str(Path(video_root) / (vid_stem + Path(lookup_by_id[normalize_to_digits(vid_stem)]).suffix))
        npz_path = out_root / f"{vid_stem}.npz"
        per_video_dir = previews_dir / vid_stem / "frames"
        if npz_path.exists():
            data = np.load(npz_path)
            T = data['x'].shape[0]
            frame_lengths.append(T)
            manifest[vid_stem] = {"gloss": gloss, "npz": str(npz_path.relative_to(KP_ROOT)), "frames": T}
            continue
        x, m, preview_frames, T = read_video_to_seq(src, per_frame_dir=per_video_dir)
        if T == 0:
            continue
        frame_lengths.append(T)
        np.savez_compressed(npz_path,
            x=x.astype(np.float32),
            m=m.astype(np.uint8),
            y=str(gloss),
            vid=str(vid_stem),
            num_frames=T
        )
        manifest[vid_stem] = {"gloss": gloss, "npz": str(npz_path.relative_to(KP_ROOT)), "frames": T}
        if (mosaic_counter % SAVE_MOSAIC_EVERY_N_CLIPS) == 0:
            save_preview_grid(preview_frames, previews_dir / f"{vid_stem}.png")
        mosaic_counter += 1
    with open(manifest_out, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    if frame_lengths:
        print(f"  [{name}] Frame length stats:")
        print(f"    Min: {min(frame_lengths)}, Max: {max(frame_lengths)}, Mean: {np.mean(frame_lengths):.1f}, Median: {np.median(frame_lengths):.1f}")

def main():
    print("\n" + "="*60)
    print("VARIABLE-LENGTH KEYPOINT EXTRACTION")
    print("="*60)
    print(f"Output directory: {OUT_DIR}")
    print(f"Min frames: {MIN_FRAMES}, Max frames: {MAX_ALLOWED_FRAMES}")
    print(f"Sample stride: {SAMPLE_STRIDE}")
    print("="*60 + "\n")
    splits: Dict[str, Dict[str,str]] = {}
    for k, p in JSON_IN.items():
        if not os.path.exists(p):
            print(f"Missing {k} JSON: {p}")
            return
        splits[k] = load_json(p)
    process_split("train", splits['train'], VIDEO_DIRS['train'],
                  KP_DIRS['train'], JSON_OUT / "Train_150_kp_variable.json", PREV_ROOT / "train")
    process_split("valid", splits['valid'], VIDEO_DIRS['valid'],
                  KP_DIRS['valid'], JSON_OUT / "Valid_150_kp_variable.json", PREV_ROOT / "valid")
    process_split("test_itw", splits['test_itw'], VIDEO_DIRS['test_itw'],
                  KP_DIRS['test_itw'], JSON_OUT / "Test_ITW_150_kp_variable.json", PREV_ROOT / "test_itw")
    process_split("test_stu", splits['test_stu'], VIDEO_DIRS['test_stu'],
                  KP_DIRS['test_stu'], JSON_OUT / "Test_STU_150_kp_variable.json", PREV_ROOT / "test_stu")
    process_split("test_syn", splits['test_syn'], VIDEO_DIRS['test_syn'],
                  KP_DIRS['test_syn'], JSON_OUT / "Test_SYN_150_kp_variable.json", PREV_ROOT / "test_syn")
    process_split("test_ted", splits['test_ted'], VIDEO_DIRS['test_ted'],
                  KP_DIRS['test_ted'], JSON_OUT / "Test_TED_150_kp_variable.json", PREV_ROOT / "test_ted")
    print("\n Done.")
    print(f"Keypoints root: {KP_ROOT}")
    print(f"Preview PNGs  : {PREV_ROOT}")
    print(f"Manifests     : {JSON_OUT}")
    print("\nEach .npz file contains:")
    print("  - x: [T, 42, 2] variable-length keypoints")
    print("  - m: [T, 42] mask")
    print("  - num_frames: actual T value")
    print("  - y: gloss label")
    print("  - vid: video id")

if __name__ == "__main__":
    main()
