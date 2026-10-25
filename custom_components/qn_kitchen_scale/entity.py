"""Shared entity base."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import QnKitchenScaleCoordinator
from .protocol import LOCAL_NAME


class QnKitchenScaleEntity(CoordinatorEntity[QnKitchenScaleCoordinator]):
    """An entity of one scale."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: QnKitchenScaleCoordinator, key: str) -> None:
        """Bind to the coordinator and set identity."""
        super().__init__(coordinator)
        self._attr_translation_key = key
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name=LOCAL_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )
