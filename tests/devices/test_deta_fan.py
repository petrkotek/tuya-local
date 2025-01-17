from homeassistant.components.fan import SUPPORT_SET_SPEED
from homeassistant.components.light import COLOR_MODE_ONOFF

from ..const import DETA_FAN_PAYLOAD
from ..helpers import assert_device_properties_set
from ..mixins.light import BasicLightTests
from ..mixins.switch import BasicSwitchTests, SwitchableTests
from .base_device_tests import TuyaDeviceTestCase

SWITCH_DPS = "1"
SPEED_DPS = "3"
LIGHT_DPS = "9"
MASTER_DPS = "101"
TIMER_DPS = "102"
LIGHT_TIMER_DPS = "103"


class TestDetaFan(
    BasicLightTests, BasicSwitchTests, SwitchableTests, TuyaDeviceTestCase
):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("deta_fan.yaml", DETA_FAN_PAYLOAD)
        self.subject = self.entities["fan"]
        self.setUpSwitchable(SWITCH_DPS, self.subject)
        self.setUpBasicLight(LIGHT_DPS, self.entities["light"])
        self.setUpBasicSwitch(MASTER_DPS, self.entities["switch_master"])

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_SET_SPEED,
        )

    def test_speed(self):
        self.dps[SPEED_DPS] = "1"
        self.assertAlmostEqual(self.subject.percentage, 33.3, 1)

    def test_speed_step(self):
        self.assertAlmostEqual(self.subject.percentage_step, 33.3, 1)

    async def test_set_speed(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 2}):
            await self.subject.async_set_percentage(66.7)

    async def test_auto_stringify_speed(self):
        self.dps[SPEED_DPS] = "1"
        self.assertAlmostEqual(self.subject.percentage, 33.3, 1)
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: "2"}):
            await self.subject.async_set_percentage(66.7)

    async def test_set_speed_snaps(self):
        async with assert_device_properties_set(self.subject._device, {SPEED_DPS: 2}):
            await self.subject.async_set_percentage(55)

    def test_device_state_attributes(self):
        self.dps[TIMER_DPS] = "5"
        self.assertEqual(self.subject.device_state_attributes, {"timer": 5})

    def test_basic_light_state_attributes(self):
        self.dps[LIGHT_TIMER_DPS] = "6"
        self.assertEqual(self.basicLight.device_state_attributes, {"timer": 6})
