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


def stable(weight_g: float) -> bytes:
    """Build a stable frame for any weight, with a valid checksum."""
    raw = round(weight_g * 10)
    body = (
        bytes.fromhex("1012004c01020501b9") + raw.to_bytes(2, "big") + bytes.fromhex("7e1f02580201")
    )
    return body + bytes([sum(body) & 0xFF])


def moving(weight_g: float) -> bytes:
    """Build a moving (unstable) frame for any weight."""
    raw = round(weight_g * 10)
    body = (
        bytes.fromhex("1012004c01020501b3") + raw.to_bytes(2, "big") + bytes.fromhex("7e1f02580201")
    )
    return body + bytes([sum(body) & 0xFF])
