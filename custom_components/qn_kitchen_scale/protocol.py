"""Frame format of QN-KS kitchen scales.

The scale advertises as ``QN-KS`` with service ``FFE0`` in the advertisement
and streams readings over characteristic ``FFF1`` of service ``FFF0`` at about
5 Hz as soon as a client subscribes. No command or handshake is needed.

A weight frame is 18 bytes::

    10 12 00 4c 01 02 05 01 FF WW WW 7e 1f 02 58 02 DD CS

* byte 8 ``FF``: flags. Bit 0 set for a positive reading, clear for a
  negative one (after tare); bit 3 set when the reading is stable;
  bit 4 set while the scale works in 0.1 g steps.
* bytes 9-10 ``WW WW``: magnitude of the weight, big-endian
* byte 16 ``DD``: number of decimals: 1 below 1 kg (0.1 g steps),
  0 from 1 kg up (1 g steps)
* byte 17 ``CS``: sum of the preceding 17 bytes modulo 256

Pressing tare also sends a short ``15 04 01 1a`` frame, which is ignored.

This module is pure: no I/O, no clock.
"""

from __future__ import annotations

from dataclasses import dataclass

LOCAL_NAME = "QN-KS"
ADVERTISED_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
DATA_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
NOTIFY_CHARACTERISTIC_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

FRAME_LENGTH = 18
_HEADER = bytes((0x10, 0x12))
_FLAGS_INDEX = 8
_WEIGHT_SLICE = slice(9, 11)
_DECIMALS_INDEX = 16
_POSITIVE_BIT = 0x01
_STABLE_BIT = 0x08


@dataclass(frozen=True, slots=True)
class Frame:
    """One decoded reading."""

    weight_g: float
    stable: bool
    flags: int


def parse_frame(data: bytes) -> Frame | None:
    """Decode one notification; ``None`` when it is not a valid weight frame."""
    if len(data) != FRAME_LENGTH or data[:2] != _HEADER:
        return None
    if sum(data[:-1]) & 0xFF != data[-1]:
        return None
    flags = data[_FLAGS_INDEX]
    magnitude = int.from_bytes(data[_WEIGHT_SLICE], "big") / 10 ** data[_DECIMALS_INDEX]
    weight = magnitude if flags & _POSITIVE_BIT or magnitude == 0 else -magnitude
    return Frame(
        weight_g=round(weight, 1),
        stable=bool(flags & _STABLE_BIT),
        flags=flags,
    )
