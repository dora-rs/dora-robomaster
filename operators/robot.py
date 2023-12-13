#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from robomaster import robot, blaster, led, gimbal
from typing import Callable, Optional, Union

# from robot import RobotController
import cv2
import numpy as np
import pyarrow as pa
from utils import LABELS

from dora import DoraStatus

# Global variables, change it to adapt your needs
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540
FREQ = 20
CONN = "ap"
font = cv2.FONT_HERSHEY_SIMPLEX


class Operator:
    """
    Sending image from webcam to the dataflow
    """

    def __init__(self):
        self.ep_robot = robot.Robot()
        self.ep_robot.initialize(conn_type=CONN)
        self.ep_robot.camera.start_video_stream(display=False)
        self.bboxs = []
        self.ep_robot.gimbal.recenter().wait_for_completed()
        self.position = [0, 0, 0]
        self.ep_robot.chassis.sub_position(freq=FREQ, callback=self.position_callback)
        self.event = None

    def position_callback(self, position_info):
        x, y, z = position_info
        print(x, y, z, flush=True)
        print(position_info, flush=True)
        self.position = [x, y, z]

    def on_event(
        self,
        dora_event: str,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        event_type = dora_event["type"]
        if event_type == "INPUT":
            if dora_event["id"] == "tick":
                frame = self.ep_robot.camera.read_cv2_image(
                    timeout=3, strategy="newest"
                )
                frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
                send_output(
                    "image",
                    pa.array(frame.ravel()),
                    dora_event["metadata"],
                )
                send_output(
                    "position",
                    pa.array(self.position),
                    dora_event["metadata"],
                )

            elif dora_event["id"] == "control":
                print("received control", flush=True)
                if not (
                    self.event is not None
                    and not (self.event._event.isSet() and self.event.is_completed)
                ):
                    [x, y, z, speed] = dora_event["value"].to_numpy()
                    self.event = self.ep_robot.chassis.move(
                        x=x, y=y, z=z, xy_speed=speed
                    )
            elif dora_event["id"] == "blaster":
                [brightness] = dora_event["value"].to_numpy()
                if brightness > 0:
                    self.ep_robot.blaster.set_led(
                        brightness=brightness, effect=blaster.LED_ON
                    )
                else:
                    self.ep_robot.blaster.set_led(brightness=0, effect=blaster.LED_OFF)
            elif dora_event["id"] == "led":
                print("received led", flush=True)
                [r, g, b] = dora_event["value"].to_numpy()
                self.ep_robot.led.set_led(
                    comp=led.COMP_ALL, r=r, g=g, b=b, effect=led.EFFECT_ON
                )

            elif dora_event["id"] == "stop":
                return DoraStatus.STOP
            return DoraStatus.CONTINUE

        elif event_type == "STOP":
            print("received stop")
            return DoraStatus.STOP
        else:
            print("received unexpected event:", event_type)
        return DoraStatus.CONTINUE

    def __del__(self):
        self.ep_robot.unsub_position()
        self.ep_robot.camera.stop_video_stream()
        self.ep_robot.close()
