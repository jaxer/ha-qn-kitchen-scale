"""Entities react to frames and remember measurements across restarts."""

from unittest.mock import patch

from homeassistant.const import CONF_ADDRESS, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.qn_kitchen_scale.const import DOMAIN
from custom_components.qn_kitchen_scale.protocol import parse_frame

from .frames import moving, stable

ADDRESS = "FF:03:00:5F:EB:3A"


async def setup_scale(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS})
    entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.qn_kitchen_scale.coordinator.bluetooth.async_register_callback",
            return_value=lambda: None,
        ),
        patch(
            "custom_components.qn_kitchen_scale.coordinator.bluetooth.async_ble_device_from_address",
            return_value=None,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def push(entry: MockConfigEntry, frames: list[bytes]) -> None:
    coordinator = entry.runtime_data
    coordinator.log.start_session()
    for raw in frames:
        frame = parse_frame(raw)
        assert frame is not None
        coordinator._handle_frame(frame)


async def test_weight_is_unavailable_while_the_scale_sleeps(hass: HomeAssistant) -> None:
    await setup_scale(hass)
    assert hass.states.get("sensor.qn_ks_weight").state == STATE_UNAVAILABLE
    assert hass.states.get("binary_sensor.qn_ks_connected").state == "off"
    assert hass.states.get("sensor.qn_ks_last_measurement").state == "unknown"


async def test_frames_drive_live_weight_and_measurements(hass: HomeAssistant) -> None:
    entry = await setup_scale(hass)
    push(entry, [moving(300)] + [stable(652.5)] * 3)
    await hass.async_block_till_done()

    weight = hass.states.get("sensor.qn_ks_weight")
    assert weight.state == "652.5"
    assert weight.attributes["stable"] is True

    last = hass.states.get("sensor.qn_ks_last_measurement")
    assert last.state == "652.5"
    assert last.attributes["delta_g"] is None
    assert last.attributes["session"] == 1
    assert [m["weight_g"] for m in last.attributes["measurements"]] == [652.5]


async def test_measurements_survive_a_reload(hass: HomeAssistant) -> None:
    entry = await setup_scale(hass)
    push(entry, [stable(100)] * 3 + [moving(150)] + [stable(180)] * 3)
    await hass.async_block_till_done()
    await entry.runtime_data._store.async_save(entry.runtime_data._serialise())

    with (
        patch(
            "custom_components.qn_kitchen_scale.coordinator.bluetooth.async_register_callback",
            return_value=lambda: None,
        ),
        patch(
            "custom_components.qn_kitchen_scale.coordinator.bluetooth.async_ble_device_from_address",
            return_value=None,
        ),
    ):
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    last = hass.states.get("sensor.qn_ks_last_measurement")
    assert last.state == "180.0"
    assert [m["weight_g"] for m in last.attributes["measurements"]] == [180.0, 100.0]


async def test_clear_service_empties_the_history(hass: HomeAssistant) -> None:
    entry = await setup_scale(hass)
    push(entry, [stable(100)] * 3)
    await hass.async_block_till_done()
    await hass.services.async_call(DOMAIN, "clear_measurements", blocking=True)
    assert hass.states.get("sensor.qn_ks_last_measurement").attributes["measurements"] == []
