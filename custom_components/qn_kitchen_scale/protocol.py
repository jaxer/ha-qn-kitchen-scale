"""Frame format of QN-KS kitchen scales.

The scale advertises as ``QN-KS`` with service ``FFE0`` in the advertisement
and streams readings over characteristic ``FFF1`` of service ``FFF0`` at about
5 Hz as soon as a client subscribes. No command or handshake is needed.

A weight frame is 18 bytes::

    10 12 00 4c 01 02 05 UU FF WW WW RR 1f 02 58 02 DD CS

* byte 7 ``UU``: the unit the display shows, one bit each: ``01`` g, ``02`` ml,
  ``04`` ml of milk, ``08`` oz, ``10`` lb:oz. The weight in the frame is always
  in grams whatever the display shows.
* byte 8 ``FF``: flags. Bit 3 set when the reading is stable; bit 4 set while
  the scale works in 0.1 g steps (below 1 kg). Bits 0-1 carry the tare state:
  ``00`` no tare, ``01`` tare set and the net weight is zero or positive,
  ``11`` tare set and positive, ``10`` tare set and negative.
* bytes 9-10 ``WW WW``: magnitude of the weight, big-endian, in 0.1 g when
  flag bit 4 is set, else in 1 g
* byte 11 ``RR``: ``7e`` in 0.1 g steps, ``3e`` in 1 g steps
* byte 16 ``DD``: decimals of the *display* in the current unit (not needed
  to decode the weight)
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
_UNIT_INDEX = 7
_FLAGS_INDEX = 8
_WEIGHT_SLICE = slice(9, 11)
_TARE_MASK = 0x03
_TARE_NEGATIVE = 0x02
_STABLE_BIT = 0x08
_TENTHS_BIT = 0x10

DISPLAY_UNITS = {0x01: "g", 0x02: "ml", 0x04: "ml_milk", 0x08: "oz", 0x10: "lb_oz"}


@dataclass(frozen=True, slots=True)
class Frame:
    """One decoded reading."""

    weight_g: float
    stable: bool
    flags: int
    tare: bool = False
    display_unit: str = "g"


def parse_frame(data: bytes) -> Frame | None:
    """Decode one notification; ``None`` when it is not a valid weight frame."""
    if len(data) != FRAME_LENGTH or data[:2] != _HEADER:
        return None
    if sum(data[:-1]) & 0xFF != data[-1]:
        return None
    flags = data[_FLAGS_INDEX]
    magnitude = int.from_bytes(data[_WEIGHT_SLICE], "big")
    if flags & _TENTHS_BIT:
        magnitude /= 10
    weight = -magnitude if flags & _TARE_MASK == _TARE_NEGATIVE else magnitude
    return Frame(
        weight_g=round(float(weight), 1),
        stable=bool(flags & _STABLE_BIT),
        flags=flags,
        tare=bool(flags & _TARE_MASK),
        display_unit=DISPLAY_UNITS.get(data[_UNIT_INDEX], "unknown"),
    )
