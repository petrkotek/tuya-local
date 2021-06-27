"""Tests for the config flow."""
from unittest.mock import ANY, AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_NAME
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import voluptuous as vol

from custom_components.tuya_local import config_flow
from custom_components.tuya_local.const import (
    CONF_CLIMATE,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_LOCK,
    CONF_SWITCH,
    CONF_TYPE,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def test_init_entry(hass):
    """Test initialisation of the config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="test",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_TYPE: "kogan_heater",
            CONF_CLIMATE: True,
            CONF_LOCK: True,
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("climate.test")
    assert state


async def test_flow_user_init(hass):
    """Test the initialisation of the form in the first step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    expected = {
        "data_schema": vol.Schema(config_flow.individual_config_schema()),
        "description_placeholders": None,
        "errors": {},
        "flow_id": ANY,
        "handler": DOMAIN,
        "step_id": "user",
        "type": "form",
        "last_step": ANY,
    }
    assert expected == result


@patch("custom_components.tuya_local.config_flow.TuyaLocalDevice")
async def test_async_test_connection_valid(mock_device, hass):
    """Test that device is returned when connection is valid."""
    mock_instance = AsyncMock()
    mock_instance.has_returned_state = True
    mock_device.return_value = mock_instance
    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
        },
        hass,
    )
    assert device == mock_instance


@patch("custom_components.tuya_local.config_flow.TuyaLocalDevice")
async def test_async_test_connection_invalid(mock_device, hass):
    """Test that None is returned when connection is invalid."""
    mock_instance = AsyncMock()
    mock_instance.has_returned_state = False
    mock_device.return_value = mock_instance
    device = await config_flow.async_test_connection(
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
        },
        hass,
    )
    assert device is None


@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_flow_user_init_invalid_config(mock_test, hass):
    """Test errors populated when config is invalid."""
    mock_test.return_value = None
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "badkey",
        },
    )
    assert {"base": "connection"} == result["errors"]


def setup_device_mock(mock, failure=False, type="test"):
    mock_type = MagicMock()
    mock_type.legacy_type = type
    mock_iter = MagicMock()
    mock_iter.__aiter__.return_value = [mock_type] if not failure else []
    mock.async_possible_types = MagicMock(return_value=mock_iter)


@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_flow_user_init_data_valid(mock_test, hass):
    """Test we advance to the next step when connection config is valid."""
    mock_device = MagicMock()
    setup_device_mock(mock_device)
    mock_test.return_value = mock_device

    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
        },
    )
    assert "form" == result["type"]
    assert "select_type" == result["step_id"]


@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_init(mock_device, hass):
    """Test the initialisation of the form in the 2nd step of the config flow."""
    setup_device_mock(mock_device)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    expected = {
        "data_schema": ANY,
        "description_placeholders": None,
        "errors": None,
        "flow_id": ANY,
        "handler": DOMAIN,
        "step_id": "select_type",
        "type": "form",
        "last_step": ANY,
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"]({CONF_TYPE: "test"})
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({CONF_TYPE: "not_test"})
        assert False
    except vol.MultipleInvalid:
        pass


@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_aborts_when_no_match(mock_device, hass):
    """Test the flow aborts when an unsupported device is used."""
    setup_device_mock(mock_device, failure=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


@patch.object(config_flow.ConfigFlowHandler, "device")
async def test_flow_select_type_data_valid(mock_device, hass):
    """Test the flow continues when valid data is supplied."""
    setup_device_mock(mock_device, type="kogan_switch")

    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_type"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        user_input={CONF_TYPE: "kogan_switch"},
    )
    assert "form" == result["type"]
    assert "choose_entities" == result["step_id"]


async def test_flow_choose_entities_init(hass):
    """Test the initialisation of the form in the 3rd step of the config flow."""

    with patch.dict(config_flow.ConfigFlowHandler.data, {CONF_TYPE: "kogan_switch"}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "choose_entities"}
        )

    expected = {
        "data_schema": ANY,
        "description_placeholders": None,
        "errors": None,
        "flow_id": ANY,
        "handler": DOMAIN,
        "step_id": "choose_entities",
        "type": "form",
        "last_step": ANY,
    }
    assert expected == result
    # Check the schema.  Simple comparison does not work since they are not
    # the same object
    try:
        result["data_schema"]({CONF_NAME: "test", CONF_SWITCH: True})
    except vol.MultipleInvalid:
        assert False
    try:
        result["data_schema"]({CONF_CLIMATE: True})
        assert False
    except vol.MultipleInvalid:
        pass


async def test_flow_choose_entities_creates_config_entry(hass):
    """Test the flow ends when data is valid."""

    with patch.dict(
        config_flow.ConfigFlowHandler.data,
        {
            CONF_DEVICE_ID: "deviceid",
            CONF_LOCAL_KEY: "localkey",
            CONF_HOST: "hostname",
            CONF_TYPE: "kogan_switch",
        },
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "choose_entities"}
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            user_input={CONF_NAME: "test", CONF_SWITCH: True},
        )
        expected = {
            "version": 2,
            "type": "create_entry",
            "flow_id": ANY,
            "handler": DOMAIN,
            "title": "test",
            "description": None,
            "description_placeholders": None,
            "result": ANY,
            "options": {},
            "data": {
                CONF_DEVICE_ID: "deviceid",
                CONF_HOST: "hostname",
                CONF_LOCAL_KEY: "localkey",
                CONF_SWITCH: True,
                CONF_TYPE: "kogan_switch",
            },
        }
        assert expected == result


async def test_options_flow_init(hass):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_SWITCH: True,
            CONF_TYPE: "kogan_switch",
        },
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert "form" == result["type"]
    assert "user" == result["step_id"]
    assert {} == result["errors"]
    assert result["data_schema"](
        {
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_SWITCH: True,
        }
    )


@patch("custom_components.tuya_local.config_flow.async_test_connection")
async def test_options_flow_modifies_config(mock_test, hass):
    mock_device = MagicMock()
    mock_test.return_value = mock_device

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="uniqueid",
        data={
            CONF_DEVICE_ID: "deviceid",
            CONF_HOST: "hostname",
            CONF_LOCAL_KEY: "localkey",
            CONF_NAME: "test",
            CONF_SWITCH: True,
            CONF_TYPE: "kogan_switch",
        },
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # show initial form
    form = await hass.config_entries.options.async_init(config_entry.entry_id)
    # submit updated config
    result = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input={
            CONF_HOST: "new_hostname",
            CONF_LOCAL_KEY: "new_key",
            CONF_SWITCH: False,
        },
    )
    expected = {
        CONF_HOST: "new_hostname",
        CONF_LOCAL_KEY: "new_key",
        CONF_SWITCH: False,
    }
    assert "create_entry" == result["type"]
    assert "" == result["title"]
    assert result["result"] is True
    assert expected == result["data"]