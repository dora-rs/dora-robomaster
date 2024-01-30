#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Callable, Optional, Union

import cv2
import numpy as np
import pyarrow as pa
from utils import LABELS

from dora import DoraStatus

pa.array([])

CI = os.environ.get("CI")
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540

font = cv2.FONT_HERSHEY_SIMPLEX

writer = cv2.VideoWriter(
    "output01.avi",
    cv2.VideoWriter_fourcc(*"MJPG"),
    30,
    (CAMERA_WIDTH, CAMERA_HEIGHT),
)


class Operator:
    """
    Plot image and bounding box
    """

    def __init__(self):
        self.image = []
        self.bboxs = []
        self.bounding_box_messages = 0
        self.image_messages = 0

    def on_event(
        self,
        dora_event: dict,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        if dora_event["type"] == "INPUT":
            return self.on_input(dora_event, send_output)
        return DoraStatus.CONTINUE

    def on_input(
        self,
        dora_input: dict,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        """
        Put image and bounding box on cv2 window.

        Args:
            dora_input["id"] (str): Id of the dora_input declared in the yaml configuration
            dora_input["value"] (arrow array): message of the dora_input
            send_output Callable[[str, bytes | pa.UInt8Array, Optional[dict]], None]:
                Function for sending output to the dataflow:
                - First argument is the `output_id`
                - Second argument is the data as either bytes or `pa.UInt8Array`
                - Third argument is dora metadata dict
                e.g.: `send_output("bbox", pa.array([100], type=pa.uint8()), dora_event["metadata"])`
        """
        if dora_input["id"] == "image":
            frame = (
                dora_input["value"]
                .to_numpy()
                .reshape((CAMERA_HEIGHT, CAMERA_WIDTH, 3))
                .copy()  # copy the image because we want to modify it below
            )
            self.image = frame

            self.image_messages += 1
            print("received " + str(self.image_messages) + " images")

        elif dora_input["id"] == "bbox" and len(self.image) != 0:
            bboxs = dora_input["value"].to_numpy()
            self.bboxs = np.reshape(bboxs, (-1, 6))

            self.bounding_box_messages += 1
            print("received " + str(self.bounding_box_messages) + " bounding boxes")

        for bbox in self.bboxs:
            [
                min_x,
                min_y,
                max_x,
                max_y,
                confidence,
                label,
            ] = bbox
            cv2.rectangle(
                self.image,
                (int(min_x), int(min_y)),
                (int(max_x), int(max_y)),
                (0, 255, 0),
                2,
            )

            d = ((12 * 22) / (max_y - (CAMERA_HEIGHT / 2))) / 2.77 - 0.08
            cv2.putText(
                self.image,
                LABELS[int(label)] + f", d={d:.2f}",
                (int(max_x), int(max_y)),
                font,
                0.75,
                (0, 255, 0),
                2,
                1,
            )

        if CI != "true":
            writer.write(self.image)
            cv2.imshow("frame", self.image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                return DoraStatus.STOP

        return DoraStatus.CONTINUE

    def __del__(self):
        cv2.destroyAllWindows()
