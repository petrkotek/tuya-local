"""Tests for the Quto 03 Sprinkler."""
from homeassistant.components.binary_sensor import DEVICE_CLASS_PROBLEM

from ..const import QOTO_SPRINKLER_PAYLOAD
from ..mixins.binary_sensor import BasicBinarySensorTests
from ..mixins.number import MultiNumberTests
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

TARGET_DPS = "102"
CURRENT_DPS = "103"
COUNTDOWN_DPS = "104"
TIMER_DPS = "105"
ERROR_DPS = "108"


class TestQoboSprinkler(
    BasicBinarySensorTests,
    MultiNumberTests,
    MultiSensorTests,
    TuyaDeviceTestCase,
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("qoto_03_sprinkler.yaml", QOTO_SPRINKLER_PAYLOAD)
        self.setUpBasicBinarySensor(
            ERROR_DPS,
            self.entities.get("binary_sensor_error"),
            device_class=DEVICE_CLASS_PROBLEM,
            testdata=(1, 0),
        )
        self.setUpMultiNumber(
            [
                {
                    "name": "number",
                    "dps": TARGET_DPS,
                    "max": 100,
                    "step": 5,
                },
                {
                    "name": "number_timer",
                    "dps": TIMER_DPS,
                    "max": 86399,
                },
            ]
        )
        self.setUpMultiSensors(
            [
                {
                    "name": "sensor_open",
                    "dps": CURRENT_DPS,
                    "unit": "%",
                },
                {
                    "name": "sensor_timer",
                    "dps": COUNTDOWN_DPS,
                    "unit": "s",
                },
            ]
        )
