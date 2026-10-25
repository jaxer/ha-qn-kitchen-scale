"""Frame format of QN-KS kitchen scales.

The scale advertises as ``QN-KS`` with service ``FFE0`` in the advertisement
and streams readings over characteristic ``FFF1`` of service ``FFF0`` at about
5 Hz as soon as a client subscribes. No command or handshake is needed.

A frame is 18 bytes::

    10 12 00 4c 01 02 05 01 FF WW WW 7e 1f 02 58 02 01 CS

* byte 8 ``FF``: flags, bit 3 set when the reading is stable
  (``0xB9`` stable, ``0xB1`` moving at zero, ``0xB3`` moving under load)
* bytes 9-10 ``WW WW``: weight, big-endian, in 0.1 g
* byte 17 ``CS``: sum of the preceding 17 bytes modulo 256

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
_STABLE_BIT = 0x08
_WEIGHT_UNIT_G = 0.1


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
    raw = int.from_bytes(data[_WEIGHT_SLICE], "big")
    return Frame(
        weight_g=round(raw * _WEIGHT_UNIT_G, 1),
        stable=bool(flags & _STABLE_BIT),
        flags=flags,
    )
