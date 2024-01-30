# forward-backward: [-1,1]
X = 0
# left-right: [-1,1]
Y = 0
# rotation: [-1800,1800]
Z = 1000
# xy speed in m/s: [0.5, 2]
XY_SPEED = 1
# z rotation speed in °/s: [10, 540]
Z_SPEED = 10
# pitch-axis angle in degrees: [-55, 55]
GIMBAL_PITCH = 0
# yaw-axis angle in degrees: [-55, 55]
GIMBAL_YAW = 0
GOAL_OBJECTIVES = [X, Y, Z]
GIMBAL_POSITION_GOAL = [GIMBAL_PITCH, GIMBAL_YAW]

from typing import Callable, Optional, Union

import numpy as np
import pyarrow as pa
from dora import DoraStatus


CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540


def do_rectangles_overlap(rect1, rect2):
    """
    Check if two rectangles overlap.
    Each rectangle is defined by two points (x1, y1, x2, y2)
    where (x1, y1) is the top left corner, and (x2, y2) is the bottom right corner.
    """
    # Extract coordinates
    [x11, y11, x12, y12] = rect1
    [x21, y21, x22, y22] = rect2

    # Check for overlap
    return not (x12 < x21 or x22 < x11 or y12 < y21 or y22 < y11)


def estimated_distance(y):
    return ((12 * 22) / (y - (CAMERA_HEIGHT / 2))) / 2.77 - 0.08


class Operator:
    """
    Infering object from images
    """

    def __init__(self):
        self.over = False
        self.start = False
        self.position = [0, 0, 0]
        self.gimbal_position = [0, 0]

    def on_event(
        self,
        dora_event: dict,
        send_output: Callable[[str, Union[bytes, pa.Array], Optional[dict]], None],
    ) -> DoraStatus:
        if dora_event["type"] != "INPUT":
            return DoraStatus.CONTINUE

        if dora_event["id"] == "position":
            [x, y, z, gimbal_pitch, gimbal_yaw] = dora_event["value"].to_numpy()
            self.position = [x, y, z]
            self.gimbal_position = [gimbal_pitch, gimbal_yaw]

            direction = np.array(GOAL_OBJECTIVES) - np.array(self.position)
            print("position ", dora_event["value"].to_numpy(), flush=True)
            print(direction, flush=True)
            if any(abs(direction) > 0.1):
                if abs(direction[0]) > 0.1:
                    x = direction[0]
                else:
                    x = 0
                if abs(direction[1]) > 0.1:
                    y = direction[1]
                else:
                    y = 0
                if abs(direction[2]) > 0.1:
                    z = direction[2]
                else:
                    z = 0

                print("control ", x, y, flush=True)
                send_output(
                    "control",
                    pa.array([x, y, 0, XY_SPEED, Z_SPEED]),
                    dora_event["metadata"],
                )

            if (
                abs(gimbal_pitch - GIMBAL_PITCH) > 0.2
                or abs(gimbal_yaw - GIMBAL_YAW) > 0.2
            ):
                send_output(
                    "gimbal_control",
                    pa.array([GIMBAL_PITCH, GIMBAL_YAW, 20, 20]),
                    dora_event["metadata"],
                )

        return DoraStatus.CONTINUE


a = """

        elif dora_event["id"] == "bbox":
            if not self.start:
                send_output("led", pa.array([255, 0, 0]), dora_event["metadata"])
                self.start = True
            blaster = 0
            x, y, z, acc = 0, 0, 0, 0
            bboxs = dora_event["value"].to_numpy()
            bboxs = np.reshape(bboxs, (-1, 6))
            obstacle = False
            if bboxs.len() > 0:
                for bbox in bboxs:
                    [
                        min_x,
                        min_y,
                        max_x,
                        max_y,
                        confidence,
                        label,
                    ] = bbox

                    x_center = (min_x + max_x) / 2
                    if LABELS[int(label)] == "ABC":
                        continue

                    # Blast light into bottle if it's in the middle
                    if (
                        abs(x_center - CAMERA_WIDTH / 2) < 100
                        and LABELS[int(label)] == "bottle"
                    ):
                        blaster = 128

                    overlap_planning = do_rectangles_overlap(
                        [
                            min_x,
                            estimated_distance(max_y),
                            max_x,
                            estimated_distance(min_y),
                        ],
                        [CAMERA_WIDTH / 2 - 100, 0, CAMERA_WIDTH / 2 + 100, 0.5],
                    )
                    # Computed depth based on expirmental measurement of the bottom of the rectangle
                    if overlap_planning:
                        if x_center > CAMERA_WIDTH / 2:
                            y = -0.15
                            acc = 0.4
                        else:
                            y = 0.15
                            acc = 0.4

                        obstacle = True

                        break
                if obstacle == False:
                    x = 0.2
                    acc = 0.6
                arrays = pa.array([x, y, z, acc])

                send_output("blaster", pa.array([blaster]), dora_event["metadata"])
                send_output("control", arrays, dora_event["metadata"])

        return DoraStatus.CONTINUE
"""
