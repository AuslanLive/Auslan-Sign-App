from typing import List

import numpy as np
from pose_format import Pose
from pose_format.utils.generic import reduce_holistic, correct_wrists, pose_normalization_info

from .smoothing import smooth_concatenate_poses


def normalize_pose(pose: Pose) -> Pose:
    return pose.normalize(pose_normalization_info(pose.header))


def trim_pose(pose, start=True, end=True):
    if len(pose.body.data) == 0:
        return pose

    wrist_indexes = [
        pose.header._get_point_index('LEFT_HAND_LANDMARKS', 'WRIST'),
        pose.header._get_point_index('RIGHT_HAND_LANDMARKS', 'WRIST')
    ]
    either_hand = pose.body.confidence[:, 0, wrist_indexes].sum(axis=1) > 0

    first_non_zero_index = np.argmax(either_hand) if start else 0
    last_non_zero_index = (len(either_hand) - np.argmax(either_hand[::-1]) - 1) if end else len(either_hand)

    pose.body.data = pose.body.data[first_non_zero_index:last_non_zero_index]
    pose.body.confidence = pose.body.confidence[first_non_zero_index:last_non_zero_index]
    return pose

# # Singe pose processing, no concatenation
# def concatenate_poses(pose: Pose) -> Pose:
#     print('Reducing pose...')
#     pose = reduce_holistic(pose)

#     print('Normalizing pose...')
#     pose = normalize_pose(pose)

#     print('Trimming pose...')
#     pose = trim_pose(pose)

#     # Correct the wrists
#     print('Correcting wrists...')
#     pose = correct_wrists(pose)

#     # Scale the pose
#     print('Scaling pose...')
#     new_width = 500
#     shift = 1.25
#     shift_vec = np.full(shape=(pose.body.data.shape[-1]), fill_value=shift, dtype=np.float32)
#     pose.body.data = (pose.body.data + shift_vec) * new_width
#     pose.header.dimensions.height = pose.header.dimensions.width = int(new_width * shift * 2)

#     return pose

def concatenate_poses(poses: List[Pose], filenames: List[str]) -> tuple[Pose, List[tuple[int, int, str]]]:
    print('Reducing poses...')
    poses = [reduce_holistic(p) for p in poses]

    print('Normalizing poses...')
    poses = [normalize_pose(p) for p in poses]

    print('Trimming poses...')
    poses = [trim_pose(p, i > 0, i < len(poses) - 1) for i, p in enumerate(poses)]

    # Concatenate all poses
    print('Smooth concatenating poses...')
    concatenated_pose = smooth_concatenate_poses(poses)

    # Correct the wrists
    print('Correcting wrists...')
    concatenated_pose = correct_wrists(concatenated_pose)

    # Scale the newly created pose
    print('Scaling pose...')
    new_width = 500
    shift = 1.25
    shift_vec = np.full(shape=(concatenated_pose.body.data.shape[-1]), fill_value=shift, dtype=np.float32)
    concatenated_pose.body.data = (concatenated_pose.body.data + shift_vec) * new_width
    concatenated_pose.header.dimensions.height = concatenated_pose.header.dimensions.width = int(new_width * shift * 2)

    # Collect frame range information for filenames
    frame_ranges = []
    current_frame = 0
    for i, pose in enumerate(poses):
        num_frames = len(pose.body.data)
        frame_ranges.append((current_frame, current_frame + num_frames, filenames[i]))
        current_frame += num_frames

    return concatenated_pose, frame_ranges
