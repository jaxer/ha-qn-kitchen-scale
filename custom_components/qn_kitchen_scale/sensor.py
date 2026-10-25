"""Sensors: live weight, last measurement with history, battery."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import QnKitchenScaleConfigEntry, QnKitchenScaleCoordinator
from .entity import QnKitchenScaleEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QnKitchenScaleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create the sensors of one scale."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            WeightSensor(coordinator),
            LastMeasurementSensor(coordinator),
            BatterySensor(coordinator),
        ]
    )


class WeightSensor(QnKitchenScaleEntity, SensorEntity):
    """What the display shows right now; unavailable while the scale sleeps."""

    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.GRAMS
    _attr_suggested_display_precision = 1
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: QnKitchenScaleCoordinator) -> None:
        """Set up the live weight sensor."""
        super().__init__(coordinator, "weight")

    @property
    def available(self) -> bool:
        """Only while connected."""
        return super().available and self.coordinator.data.connected

    @property
    def native_value(self) -> float | None:
        """Current reading in grams."""
        return self.coordinator.data.weight_g

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Whether the reading has settled."""
        return {"stable": self.coordinator.data.stable}


class LastMeasurementSensor(QnKitchenScaleEntity, SensorEntity):
    """Newest measurement; the history rides along as an attribute."""

    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.GRAMS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: QnKitchenScaleCoordinator) -> None:
        """Set up the measurement sensor."""
        super().__init__(coordinator, "last_measurement")

    @property
    def native_value(self) -> float | None:
        """Weight of the newest measurement."""
        last = self.coordinator.data.last_measurement
        return None if last is None else last.weight_g

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Newest-first list of measurements plus details of the newest."""
        last = self.coordinator.data.last_measurement
        return {
            "measured_at": None if last is None else last.at.isoformat(),
            "delta_g": None if last is None else last.delta_g,
            "session": None if last is None else last.session,
            "measurements": [m.as_dict() for m in self.coordinator.data.measurements],
        }


class BatterySensor(QnKitchenScaleEntity, SensorEntity):
    """Battery level read once per connection."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: QnKitchenScaleCoordinator) -> None:
        """Set up the battery sensor."""
        super().__init__(coordinator, "battery")

    @property
    def native_value(self) -> int | None:
        """Battery percentage."""
        return self.coordinator.data.battery
