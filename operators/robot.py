#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from robomaster import robot, blaster, led
from typing import Callable, Optional, Union

# from robot import RobotController
import pyarrow as pa

from dora import DoraStatus

# Global variables, change it to adapt your needs
FREQ = 20
CONN = "ap"


class Operator:
    def __init__(self):
        self.ep_robot = robot.Robot()
        print("Initializing robot...")
        assert self.ep_robot.initialize(conn_type=CONN), "Could not initialize ep_robot"
        assert self.ep_robot.camera.start_video_stream(
            display=False
        ), "Could not start video stream"

        self.ep_robot.gimbal.recenter().wait_for_completed()
        self.position = [0, 0, 0]
        self.gimbal_position = [0, 0]
        self.event = None

    def on_event(
        self,
        dora_event: str,
        send_output: Callable[[str, Union[bytes, pa.UInt8Array], Optional[dict]], None],
    ) -> DoraStatus:
        event_type = dora_event["type"]
        if event_type == "INPUT":
            if dora_event["id"] == "tick":
                send_output(
                    "position",
                    pa.array(self.position + self.gimbal_position),
                    dora_event["metadata"],
                )

            elif dora_event["id"] == "control":
                if not (
                    self.event is not None
                    and not (self.event._event.isSet() and self.event.is_completed)
                ):
                    [x, y, z, xy_speed, z_speed] = dora_event["value"].to_numpy()
                    print(f"received control: {x, y, z, xy_speed, z_speed}", flush=True)
                    self.event = self.ep_robot.chassis.move(
                        x=x, y=y, z=z, xy_speed=xy_speed, z_speed=z_speed
                    )
                    self.position[0] += x
                    self.position[1] += y
                    self.position[2] += z
                else:
                    print("control not completed", flush=True)
                    print("Set: ", self.event._event.isSet(), flush=True)
                    print("Completed:", self.event.is_completed, flush=True)

            elif dora_event["id"] == "gimbal_control":
                if not (
                    self.event is not None
                    and not (self.event._event.isSet() and self.event.is_completed)
                ):
                    [
                        gimbal_pitch,
                        gimbal_yaw,
                        gimbal_pitch_speed,
                        gimbal_yaw_speed,
                    ] = dora_event["value"].to_numpy()

                    self.event = self.ep_robot.gimbal.moveto(
                        pitch=gimbal_pitch,
                        yaw=gimbal_yaw,
                        pitch_speed=gimbal_pitch_speed,
                        yaw_speed=gimbal_yaw_speed,
                    )
                    self.gimbal_position[0] = gimbal_pitch
                    self.gimbal_position[1] = gimbal_yaw

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

        return DoraStatus.CONTINUE
