"""Frames captured from a real QN-KS scale (Yolanda CK10A, firmware V02.0)."""

# Scale switched on, nothing on it, reading settled at 0.0 g.
STABLE_ZERO = bytes.fromhex("1012004c01020501b900007e1f025802012a")
# Empty scale drifted to 1.5 g, reading settled.
STABLE_1_5 = bytes.fromhex("1012004c01020501b9000f7e1f0258020139")
# Nothing on the scale but the reading still moving.
MOVING_ZERO = bytes.fromhex("1012004c01020501b1000f7e1f0258020131")
# Hand pressing: 444.0 g, moving.
MOVING_444 = bytes.fromhex("1012004c01020501b311587e1f025802018d")
# A 652.5 g object left on the scale, reading settled.
STABLE_652_5 = bytes.fromhex("1012004c01020501b9197d7e1f02580201c0")
# 1595 g: above 1 kg the scale switches to 1 g steps (byte 16 = 0, flag bit 4 clear).
STABLE_1595 = bytes.fromhex("1012004c01020501a9063b3e1f025802001a")
# Tare pressed with 1595 g on, then the object removed: display −1599 g, settled.
STABLE_MINUS_1599 = bytes.fromhex("1012004c01020501aa063f3e1f025802001f")
# −1591 g, still moving.
MOVING_MINUS_1591 = bytes.fromhex("1012004c01020501a206373e1f025802000f")
# Sent once when tare is pressed; not a weight frame.
TARE_EVENT = bytes.fromhex("1504011a")


def _frame(weight_g: float, stable_flag: bool) -> bytes:
    """Build a frame the way the scale does: sign in the flags, 0.1 g steps below 1 kg."""
    magnitude = abs(weight_g)
    decimals = 1 if magnitude < 1000 else 0
    flags = 0xA0 | (0x10 if decimals else 0) | (0x08 if stable_flag else 0)
    flags |= 0x01 if weight_g >= 0 else 0x02
    raw = round(magnitude * 10**decimals)
    body = (
        bytes.fromhex("1012004c01020501")
        + bytes([flags])
        + raw.to_bytes(2, "big")
        + (bytes.fromhex("7e1f025802") if decimals else bytes.fromhex("3e1f025802"))
        + bytes([decimals])
    )
    return body + bytes([sum(body) & 0xFF])


def stable(weight_g: float) -> bytes:
    """Build a stable frame for any weight, with a valid checksum."""
    return _frame(weight_g, True)


def moving(weight_g: float) -> bytes:
    """Build a moving (unstable) frame for any weight."""
    return _frame(weight_g, False)
