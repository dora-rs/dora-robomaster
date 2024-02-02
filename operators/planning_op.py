import numpy as np
import pyarrow as pa
from dora import DoraStatus

# forward-backward: [-1,1]
X = 0
# left-right: [-1,1]
Y = 0
SPEED = 0.5
# pitch-axis angle in degrees: [-55, 55]
PITCH = 0
# yaw-axis angle in degrees: [-55, 55]
ROTATION = 0
# RGB LED [0, 255]
RGB = [0, 0, 0]
BRIGHTNESS = [0]  # [0, 128]

GOAL_OBJECTIVES = [X, Y, 0]
GIMBAL_POSITION_GOAL = [PITCH, ROTATION]

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
    def __init__(self):
        self.over = False
        self.start = False
        self.position = [0, 0, 0]
        self.gimbal_position = [0, 0]
        self.brightness = [0]
        self.rgb = [0, 0, 0]
        self.bboxs = []
        self.objects_distances = []

    def on_event(
        self,
        dora_event: dict,
        send_output,
    ) -> DoraStatus:
        if dora_event["type"] != "INPUT":
            return DoraStatus.CONTINUE

        if dora_event["id"] == "bbox":
            bboxs = dora_event["value"].to_numpy()
            self.bboxs = np.reshape(
                bboxs, (-1, 6)
            )  # [ min_x, min_y, max_x, max_y, confidence, label ]
            if len(self.bboxs) > 0:
                self.objects_distances = estimated_distance(self.bboxs[:, 3])
        elif dora_event["id"] == "position":
            [x, y, z, gimbal_pitch, gimbal_yaw] = dora_event["value"].to_numpy()
            self.position = [x, y, z]
            self.gimbal_position = [gimbal_pitch, gimbal_yaw]

            direction = np.clip(
                np.array(GOAL_OBJECTIVES) - np.array(self.position), -1, 1
            )
            print("position ", dora_event["value"].to_numpy(), flush=True)
            print(direction, flush=True)
            if any(abs(direction) > 0.1):
                x = direction[0]
                y = direction[1]
                z = direction[2]

                print("control ", x, y, z, flush=True)
                send_output(
                    "control",
                    pa.array([x, y, 0, SPEED, 0]),
                    dora_event["metadata"],
                )

            if abs(gimbal_pitch - PITCH) > 0.2 or abs(gimbal_yaw - ROTATION) > 0.2:
                send_output(
                    "gimbal_control",
                    pa.array([PITCH, ROTATION, 20, 20]),
                    dora_event["metadata"],
                )
            if RGB != self.rgb:
                send_output(
                    "led",
                    pa.array(RGB),
                    dora_event["metadata"],
                )
                self.rgb = RGB
            if BRIGHTNESS != self.brightness:
                send_output(
                    "blaster",
                    pa.array(BRIGHTNESS),
                    dora_event["metadata"],
                )
                self.brightness = BRIGHTNESS

        return DoraStatus.CONTINUE
