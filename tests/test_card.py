"""The integration serves its dashboard card and loads it on every dashboard."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.qn_kitchen_scale import CARD_PATH, CARD_URL
from custom_components.qn_kitchen_scale.const import DOMAIN


async def test_card_is_served_and_loaded_with_the_frontend(hass: HomeAssistant) -> None:
    # The frontend itself needs the hass_frontend package; marking it loaded is enough here.
    hass.config.components.add("frontend")
    with patch("custom_components.qn_kitchen_scale.add_extra_js_url") as add_js:
        assert await async_setup_component(hass, DOMAIN, {})

    routes = {r.canonical for r in hass.http.app.router.resources()}
    assert CARD_URL in routes
    assert CARD_PATH.is_file()
    add_js.assert_called_once_with(hass, f"{CARD_URL}?v=0.1.0")


async def test_no_card_without_the_frontend(hass: HomeAssistant) -> None:
    with patch("custom_components.qn_kitchen_scale.add_extra_js_url") as add_js:
        assert await async_setup_component(hass, DOMAIN, {})
    add_js.assert_not_called()
