"""Binary sensor: is the scale awake and connected."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import QnKitchenScaleConfigEntry, QnKitchenScaleCoordinator
from .entity import QnKitchenScaleEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QnKitchenScaleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create the connectivity sensor."""
    async_add_entities([ConnectedSensor(entry.runtime_data)])


class ConnectedSensor(QnKitchenScaleEntity, BinarySensorEntity):
    """On while Home Assistant holds a connection to the scale."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: QnKitchenScaleCoordinator) -> None:
        """Set up the connectivity sensor."""
        super().__init__(coordinator, "connected")

    @property
    def is_on(self) -> bool:
        """Connected right now."""
        return self.coordinator.data.connected
