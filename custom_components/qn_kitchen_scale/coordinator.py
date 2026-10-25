"""Keep a QN-KS scale connected while it is awake and publish its readings."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field, replace
from typing import Any

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN, STORAGE_VERSION
from .protocol import (
    BATTERY_LEVEL_CHARACTERISTIC_UUID,
    NOTIFY_CHARACTERISTIC_UUID,
    Frame,
    parse_frame,
)
from .session import Measurement, MeasurementLog

_LOGGER = logging.getLogger(__name__)

_CONNECT_ATTEMPTS = 3
_SAVE_DELAY_S = 2.0

type QnKitchenScaleConfigEntry = ConfigEntry[QnKitchenScaleCoordinator]


@dataclass(frozen=True, slots=True)
class ScaleState:
    """Everything the entities show."""

    connected: bool = False
    weight_g: float | None = None
    stable: bool = False
    tare: bool = False
    display_unit: str = "g"
    battery: int | None = None
    measurements: tuple[Measurement, ...] = field(default_factory=tuple)

    @property
    def last_measurement(self) -> Measurement | None:
        """Newest measurement, if any."""
        return self.measurements[0] if self.measurements else None


class QnKitchenScaleCoordinator(DataUpdateCoordinator[ScaleState]):
    """Connect on advertisement, stream FFF1, detect measurements, persist them."""

    config_entry: QnKitchenScaleConfigEntry

    def __init__(self, hass: HomeAssistant, entry: QnKitchenScaleConfigEntry, address: str) -> None:
        """Set up the coordinator for one scale."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}:{address}",
            update_interval=None,
        )
        self.address = address
        self.log = MeasurementLog()
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{address.replace(':', '').lower()}"
        )
        self._client: BleakClient | None = None
        self._connect_lock = asyncio.Lock()
        self._unregister_advertisements: CALLBACK_TYPE | None = None
        self.data = ScaleState()

    async def async_start(self) -> None:
        """Load history and start listening for the scale."""
        stored = await self._store.async_load()
        if stored:
            self.log.measurements = [
                Measurement.from_dict(item) for item in stored.get("measurements", [])
            ]
            self.log.session = int(stored.get("session", 0))
        self._publish()
        self._unregister_advertisements = bluetooth.async_register_callback(
            self.hass,
            self._on_advertisement,
            BluetoothCallbackMatcher(address=self.address, connectable=True),
            BluetoothScanningMode.ACTIVE,
        )
        if bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True):
            self.hass.async_create_task(self._async_connect())

    async def async_stop(self) -> None:
        """Stop listening and drop the connection."""
        if self._unregister_advertisements:
            self._unregister_advertisements()
            self._unregister_advertisements = None
        client = self._client
        self._client = None
        if client and client.is_connected:
            try:
                await client.disconnect()
            except BleakError:  # pragma: no cover - best effort on shutdown
                _LOGGER.debug("Disconnect on stop failed", exc_info=True)

    async def async_clear_measurements(self) -> None:
        """Forget the measurement history."""
        self.log.clear()
        self._publish()
        await self._store.async_save(self._serialise())

    @callback
    def _on_advertisement(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        if self._client is None:
            self.hass.async_create_task(self._async_connect())

    async def _async_connect(self) -> None:
        async with self._connect_lock:
            if self._client is not None:
                return
            device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if device is None:
                return
            try:
                client = await establish_connection(
                    BleakClientWithServiceCache,
                    device,
                    self.address,
                    disconnected_callback=self._on_disconnected,
                    max_attempts=_CONNECT_ATTEMPTS,
                    ble_device_callback=lambda: bluetooth.async_ble_device_from_address(
                        self.hass, self.address, connectable=True
                    ),
                )
            except (BleakError, TimeoutError) as err:
                _LOGGER.debug("Connection to %s failed: %s", self.address, err)
                return
            self._client = client
            self.log.start_session()
            battery = await self._read_battery(client)
            try:
                await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, self._on_notification)
            except BleakError as err:
                _LOGGER.warning("Subscribing to %s failed: %s", self.address, err)
                self._client = None
                await client.disconnect()
                return
            _LOGGER.debug("Connected to %s", self.address)
            self.data = replace(self.data, connected=True, battery=battery)
            self._publish()

    async def _read_battery(self, client: BleakClient) -> int | None:
        try:
            value = await client.read_gatt_char(BATTERY_LEVEL_CHARACTERISTIC_UUID)
        except BleakError:
            return None
        return int(value[0]) if value else None

    @callback
    def _on_notification(self, _: BleakGATTCharacteristic, data: bytearray) -> None:
        frame = parse_frame(bytes(data))
        if frame is None:
            _LOGGER.debug("Ignoring frame %s", data.hex())
            return
        self._handle_frame(frame)

    @callback
    def _handle_frame(self, frame: Frame) -> None:
        measurement = self.log.feed(frame, dt_util.utcnow())
        if measurement is not None:
            self._store.async_delay_save(self._serialise, _SAVE_DELAY_S)
        changed = measurement is not None or (
            frame.weight_g,
            frame.stable,
            frame.tare,
            frame.display_unit,
        ) != (self.data.weight_g, self.data.stable, self.data.tare, self.data.display_unit)
        if changed:
            self.data = replace(
                self.data,
                connected=True,
                weight_g=frame.weight_g,
                stable=frame.stable,
                tare=frame.tare,
                display_unit=frame.display_unit,
            )
            self._publish()

    @callback
    def _on_disconnected(self, _: BleakClient) -> None:
        _LOGGER.debug("Disconnected from %s", self.address)
        self._client = None
        self.data = replace(self.data, connected=False, weight_g=None, stable=False)
        self._publish()

    @callback
    def _publish(self) -> None:
        self.async_set_updated_data(replace(self.data, measurements=tuple(self.log.measurements)))

    def _serialise(self) -> dict[str, Any]:
        return {
            "session": self.log.session,
            "measurements": [m.as_dict() for m in self.log.measurements],
        }
