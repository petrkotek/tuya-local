from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_SWING_MODE,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE

from custom_components.tuya_local.purline_m100_heater.climate import PurlineM100Heater
from custom_components.tuya_local.purline_m100_heater.const import (
    ATTR_POWER_LEVEL,
    ATTR_TARGET_TEMPERATURE,
    POWER_LEVEL_AUTO,
    POWER_LEVEL_FANONLY,
    POWER_LEVEL_TO_DPS_LEVEL,
    PRESET_AUTO,
    PRESET_FAN,
    PROPERTY_TO_DPS_ID,
)

from ..const import PURLINE_M100_HEATER_PAYLOAD
from ..helpers import (
    assert_device_properties_set,
    assert_device_properties_set_optional,
)


class TestPulineM100Heater(IsolatedAsyncioTestCase):
    def setUp(self):
        device_patcher = patch("custom_components.tuya_local.device.TuyaLocalDevice")
        self.addCleanup(device_patcher.stop)
        self.mock_device = device_patcher.start()

        self.subject = PurlineM100Heater(self.mock_device())

        self.dps = PURLINE_M100_HEATER_PAYLOAD.copy()
        self.subject._device.get_property.side_effect = lambda id: self.dps[id]

    def test_supported_features(self):
        self.assertEqual(
            self.subject.supported_features,
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_SWING_MODE,
        )

    def test_should_poll(self):
        self.assertTrue(self.subject.should_poll)

    def test_name_returns_device_name(self):
        self.assertEqual(self.subject.name, self.subject._device.name)

    def test_unique_id_returns_device_unique_id(self):
        self.assertEqual(self.subject.unique_id, self.subject._device.unique_id)

    def test_device_info_returns_device_info_from_device(self):
        self.assertEqual(self.subject.device_info, self.subject._device.device_info)

    def test_icon(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_AUTO
        self.assertEqual(self.subject.icon, "mdi:radiator")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.icon, "mdi:radiator-disabled")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_FANONLY
        self.assertEqual(self.subject.icon, "mdi:fan")

    def test_temperature_unit_returns_device_temperature_unit(self):
        self.assertEqual(
            self.subject.temperature_unit, self.subject._device.temperature_unit
        )

    def test_target_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]] = 25
        self.assertEqual(self.subject.target_temperature, 25)

    def test_target_temperature_step(self):
        self.assertEqual(self.subject.target_temperature_step, 1)

    def test_minimum_target_temperature(self):
        self.assertEqual(self.subject.min_temp, 15)

    def test_maximum_target_temperature(self):
        self.assertEqual(self.subject.max_temp, 35)

    async def test_legacy_set_temperature_with_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25}
        ):
            await self.subject.async_set_temperature(temperature=25)

    async def test_legacy_set_temperature_with_no_valid_properties(self):
        await self.subject.async_set_temperature(something="else")
        self.subject._device.async_set_property.assert_not_called

    async def test_set_target_temperature(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25}
        ):
            await self.subject.async_set_target_temperature(25)

    async def test_set_target_temperature_rounds_value_to_closest_integer(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_TARGET_TEMPERATURE]: 25},
        ):
            await self.subject.async_set_target_temperature(24.6)

    async def test_set_target_temperature_fails_outside_valid_range(self):
        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(4\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(4)

        with self.assertRaisesRegex(
            ValueError, "Target temperature \\(36\\) must be between 15 and 35"
        ):
            await self.subject.async_set_target_temperature(36)

    def test_current_temperature(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_TEMPERATURE]] = 25
        self.assertEqual(self.subject.current_temperature, 25)

    def test_hvac_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = True
        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_AUTO
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_HEAT)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_FANONLY
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_FAN_ONLY)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = False
        self.assertEqual(self.subject.hvac_mode, HVAC_MODE_OFF)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]] = None
        self.assertEqual(self.subject.hvac_mode, STATE_UNAVAILABLE)

    def test_hvac_modes(self):
        self.assertCountEqual(
            self.subject.hvac_modes, [HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_FAN_ONLY]
        )

    async def test_turn_on(self):
        async with assert_device_properties_set_optional(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: True},
            {PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]: POWER_LEVEL_AUTO},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_HEAT)

    async def test_turn_off(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: False},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_OFF)

    async def test_turn_on_fan(self):
        async with assert_device_properties_set_optional(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_HVAC_MODE]: True},
            {PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]: POWER_LEVEL_FANONLY},
        ):
            await self.subject.async_set_hvac_mode(HVAC_MODE_FAN_ONLY)

    def test_preset_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_AUTO
        self.assertEqual(self.subject.preset_mode, PRESET_AUTO)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_FANONLY
        self.assertEqual(self.subject.preset_mode, PRESET_FAN)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = POWER_LEVEL_TO_DPS_LEVEL["4"]
        self.assertEqual(self.subject.preset_mode, "4")

        self.dps[PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]] = None
        self.assertIs(self.subject.preset_mode, None)

    def test_preset_modes(self):
        self.assertCountEqual(
            self.subject.preset_modes,
            [PRESET_FAN, "1", "2", "3", "4", "5", PRESET_AUTO],
        )

    async def test_set_preset_mode_numeric(self):
        async with assert_device_properties_set(
            self.subject._device,
            {PROPERTY_TO_DPS_ID[ATTR_POWER_LEVEL]: POWER_LEVEL_TO_DPS_LEVEL["3"]},
        ):
            await self.subject.async_set_preset_mode("3")

    def test_swing_mode(self):
        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]] = True
        self.assertEqual(self.subject.swing_mode, SWING_VERTICAL)

        self.dps[PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]] = False
        self.assertEqual(self.subject.swing_mode, SWING_OFF)

    def test_swing_modes(self):
        self.assertCountEqual(
            self.subject.swing_modes,
            [SWING_OFF, SWING_VERTICAL],
        )

    async def test_set_swing_mode_on(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]: True}
        ):
            await self.subject.async_set_swing_mode(SWING_VERTICAL)

    async def test_set_swing_mode_off(self):
        async with assert_device_properties_set(
            self.subject._device, {PROPERTY_TO_DPS_ID[ATTR_SWING_MODE]: False}
        ):
            await self.subject.async_set_swing_mode(SWING_OFF)

    async def test_update(self):
        result = AsyncMock()
        self.subject._device.async_refresh.return_value = result()

        await self.subject.async_update()

        self.subject._device.async_refresh.assert_called_once()
        result.assert_awaited()