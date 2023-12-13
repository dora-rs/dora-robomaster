#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Optional, Union

from time import sleep
from enum import Enum
import numpy as np
import pyarrow as pa
from utils import LABELS
from dora import DoraStatus

CAMERA_HEIGHT = 540
DISTANCE = 2


class Operator:
    """
    Infering object from images
    """

    def __init__(self):
        self.over = False
        self.start = False

    def on_event(
        self,
        dora_event: dict,
        send_output: Callable[[str, Union[bytes, pa.Array], Optional[dict]], None],
    ) -> DoraStatus:
        if dora_event["type"] == "INPUT":
            return self.on_input(dora_event, send_output)
        return DoraStatus.CONTINUE

    def on_input(
        self,
        dora_input: dict,
        send_output: Callable[[str, Union[bytes, pa.array], Optional[dict]], None],
    ) -> DoraStatus:
        if dora_input["id"] == "position":
            [x, y, z] = dora_input["value"].to_numpy()
            print(x, y, z, flush=True)
            if x > DISTANCE:
                send_output("led", pa.array([0, 0, 255]), dora_input["metadata"])
                send_output("stop", pa.array([""]), dora_input["metadata"])
                return DoraStatus.CONTINUE
        elif dora_input["id"] == "bbox":
            if not self.start:
                send_output("led", pa.array([255, 0, 0]), dora_input["metadata"])
                self.start = True
            blaster = 0
            x, y, z, acc = 0, 0, 0, 0
            bboxs = dora_input["value"].to_numpy()
            bboxs = np.reshape(bboxs, (-1, 6))
            arrays = pa.array([0, 0, 0, 0])
            obstacle = False
            box = False
            for bbox in bboxs:
                box = True
                [
                    min_x,
                    min_y,
                    max_x,
                    max_y,
                    confidence,
                    label,
                ] = bbox
                if LABELS[int(label)] == "ABC":
                    continue

                if (
                    (min_x + max_x) / 2 > 385
                    and (min_x + max_x) / 2 < 575
                    and LABELS[int(label)] == "bottle"
                ):
                    blaster = 128
                d = ((12 * 22) / (max_y - (CAMERA_HEIGHT / 2))) / 2.77 - 0.08
                if d < 0.5 and (
                    (max_x > 385 and min_x <= 385)
                    or (min_x < 575 and max_x >= 575)
                    or (min_x < 385 and max_x > 575)
                    or (min_x > 385 and max_x < 575)
                ):
                    if (min_x + max_x) / 2 > 470:
                        y = -0.15
                        acc = 0.4
                    elif (min_x + max_x) / 2 <= 470:
                        y = 0.15
                        acc = 0.4

                    obstacle = True
                    break
            if obstacle == False and box == True:
                x = 0.2
                acc = 0.6
            arrays = pa.array([x, y, z, acc])

            if box == True:
                send_output("blaster", pa.array([blaster]), dora_input["metadata"])
                send_output("control", arrays, dora_input["metadata"])
                blaster = 0

        return DoraStatus.CONTINUE
