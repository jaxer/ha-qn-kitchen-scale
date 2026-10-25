"""QN Kitchen Scale: local Bluetooth integration for QN-KS kitchen scales."""

from __future__ import annotations

from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import QnKitchenScaleConfigEntry, QnKitchenScaleCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
SERVICE_CLEAR_MEASUREMENTS = "clear_measurements"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the integration-wide service."""

    async def clear_measurements(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_clear_measurements()

    hass.services.async_register(DOMAIN, SERVICE_CLEAR_MEASUREMENTS, clear_measurements)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: QnKitchenScaleConfigEntry) -> bool:
    """Start following one scale."""
    coordinator = QnKitchenScaleCoordinator(hass, entry, entry.data[CONF_ADDRESS])
    await coordinator.async_start()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: QnKitchenScaleConfigEntry) -> bool:
    """Stop following the scale."""
    await entry.runtime_data.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
