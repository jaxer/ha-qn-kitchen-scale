"""QN Kitchen Scale: local Bluetooth integration for QN-KS kitchen scales."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .coordinator import QnKitchenScaleConfigEntry, QnKitchenScaleCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
SERVICE_CLEAR_MEASUREMENTS = "clear_measurements"
CARD_URL = f"/{DOMAIN}/qn-kitchen-scale-card.js"
CARD_PATH = Path(__file__).parent / "frontend" / "qn-kitchen-scale-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the integration-wide service and the dashboard card."""

    async def clear_measurements(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_clear_measurements()

    hass.services.async_register(DOMAIN, SERVICE_CLEAR_MEASUREMENTS, clear_measurements)
    await _async_register_card(hass)
    return True


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve the card and load it on every dashboard, so no resource has to be added by hand."""
    if hass.http is None or "frontend" not in hass.config.components:
        return
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=False)]
    )
    # The version in the URL makes browsers fetch the card again after an update.
    integration = await async_get_integration(hass, DOMAIN)
    add_extra_js_url(hass, f"{CARD_URL}?v={integration.version}")


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
