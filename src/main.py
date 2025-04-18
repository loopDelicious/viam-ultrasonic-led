import asyncio
from threading import Event
from typing import ClassVar, Mapping, Optional, Sequence, cast

from typing_extensions import Self
from viam.logging import getLogger
from viam.components.board import Board
from viam.components.sensor import Sensor
from viam.services.generic import Generic
from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict, ValueTypes

LOGGER = getLogger("ultrasonic-dimled")

class UltrasonicDimled(Generic, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("joyce", "ultrasonic-dimled"), "ultrasonic-dimLED"
    )

    auto_start = True
    task = None
    event = Event()

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        attrs = struct_to_dict(config.attributes)
        required_dependencies = ["board", "sensor"]
        required_attributes = ["led_pin"]
        implicit_dependencies = []

        for component in required_dependencies:
            if component not in attrs or not isinstance(attrs[component], str):
                raise ValueError(f"{component} is required and must be a string")
            else:
                implicit_dependencies.append(attrs[component])

        for attribute in required_attributes:
            if attribute not in attrs or not isinstance(attrs[attribute], str):
                raise ValueError(f"{attribute} is required and must be a string")

        return implicit_dependencies

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        attrs = struct_to_dict(config.attributes)
        self.auto_start = bool(attrs.get("auto_start", self.auto_start))

        LOGGER.error("Reconfiguring ultrasonic dimmed LED module...")

        board_resource = dependencies.get(Board.get_resource_name(str(attrs.get("board"))))
        self.board = cast(Board, board_resource)

        sensor_resource = dependencies.get(Sensor.get_resource_name(str(attrs.get("sensor"))))
        self.sensor = cast(Sensor, sensor_resource)

        self.led_pin_attr = str(attrs.get("led_pin"))
        self.max_distance = float(attrs.get("max_distance", 1.0))  # meters
        self.blinking_distance = float(attrs.get("blinking_distance", 0.15))

        if self.board and self.led_pin_attr:
            asyncio.create_task(self.flash_test()) # blink the LED upon booting

        if self.auto_start:
            self.start()

        return super().reconfigure(config, dependencies)

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        result = {key: False for key in command.keys()}
        for name, _args in command.items():
            if name == "start":
                self.start()
                result[name] = True
            elif name == "stop":
                self.stop()
                result[name] = True
            elif name == "test":
                await self.flash_test()
                result[name] = True
        return result

    async def on_loop(self):
        self.led_pin = await self.board.gpio_pin_by_name(self.led_pin_attr)
        last_mode = None  # Track current LED mode: 'flash' or 'fade'
        last_duty = None  # Track last set duty cycle

        while not self.event.is_set():
            try:
                distance = (await self.sensor.get_readings())["distance"]
                # LOGGER.error(f"Sensor distance reading: {distance:.3f} m")

                clamped_distance = min(self.max_distance, max(0.0, distance))
                linear_ratio = clamped_distance / self.max_distance

                if clamped_distance < self.blinking_distance:
                    LOGGER.error(f"Distance < {self.blinking_distance:.2f} m — entering blinking loop")
                    while clamped_distance < self.blinking_distance and not self.event.is_set():
                        await self.flash_test()
                        distance = (await self.sensor.get_readings())["distance"]
                        clamped_distance = min(self.max_distance, max(0.0, distance))

                else:
                    duty_cycle = max(0.05, (1.0 - linear_ratio) ** 2)
                    if last_mode != "fade" or abs(duty_cycle - (last_duty or 0)) > 0.01:
                        LOGGER.error(f"Distance: {distance:.3f} m -> PWM duty cycle: {duty_cycle:.2f}")
                        await self.led_pin.set_pwm(duty_cycle=duty_cycle, frequency=1000)
                        last_mode = "fade"
                        last_duty = duty_cycle

            except Exception as e:
                LOGGER.error(f"Error updating LED brightness: {e}")

            await asyncio.sleep(0.2)

    def start(self):
        if self.task is None or self.task.done():
            self.event.clear()
            self.task = asyncio.create_task(self.control_loop())

    def stop(self):
        self.event.set()
        if self.task is not None:
            self.task.cancel()

    async def control_loop(self):
        while not self.event.is_set():
            await self.on_loop()
            await asyncio.sleep(0)

    async def flash_test(self):
        self.led_pin = await self.board.gpio_pin_by_name(self.led_pin_attr)
        for _ in range(3):
            await self.led_pin.set_pwm(duty_cycle=1.0, frequency=1000)
            await asyncio.sleep(0.2)
            await self.led_pin.set_pwm(duty_cycle=0.0, frequency=1000)
            await asyncio.sleep(0.2)

    def __del__(self):
        self.stop()

    async def close(self):
        self.stop()

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())
