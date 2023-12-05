#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Optional, Union

from time import sleep
from enum import Enum
import numpy as np
import pyarrow as pa
from utils import LABELS
from dora import DoraStatus

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
        if dora_input["id"] == "bbox":
            if not self.start:
                send_output("led", pa.array([255, 0, 0]), dora_input["metadata"])
                self.start = True
            bboxs = dora_input["value"].to_numpy()
            bboxs = np.reshape(bboxs, (-1, 6))
            bottle = False
            laser = False
            obstacle = False
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

                if (
                    (min_x + max_x) / 2 > 240
                    and (min_x + max_x) / 2 < 400
                    and LABELS[int(label)] == "cup"
                ):
                    laser = True
                if (
                    (min_x + max_x) / 2 > 240
                    and (min_x + max_x) / 2 < 400
                    and LABELS[int(label)] == "bottle"
                ):
                    bottle = True

                if LABELS[int(label)] != "ABC" and not obstacle:
                    obstacle = True
            if laser:
                send_output("blaster", pa.array([128]), dora_input["metadata"])
            else:
                send_output("blaster", pa.array([0]), dora_input["metadata"])
                if bottle:
                    send_output("led", pa.array([0, 0, 255]), dora_input["metadata"])
                elif obstacle:
                    send_output("led", pa.array([0, 255, 0]), dora_input["metadata"])
                else:
                    send_output("led", pa.array([0, 0, 0]), dora_input["metadata"])
            obstacle = False
            bottle = False
            laser = False
        return DoraStatus.CONTINUE
