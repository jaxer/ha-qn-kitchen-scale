"""The frame parser against captured frames."""

from custom_components.qn_kitchen_scale.protocol import Frame, parse_frame

from .frames import MOVING_444, MOVING_ZERO, STABLE_1_5, STABLE_652_5, STABLE_ZERO, stable


def test_stable_zero() -> None:
    assert parse_frame(STABLE_ZERO) == Frame(weight_g=0.0, stable=True, flags=0xB9)


def test_stable_object_matches_display() -> None:
    assert parse_frame(STABLE_652_5) == Frame(weight_g=652.5, stable=True, flags=0xB9)


def test_moving_frames_are_flagged_unstable() -> None:
    assert parse_frame(MOVING_ZERO) == Frame(weight_g=1.5, stable=False, flags=0xB1)
    assert parse_frame(MOVING_444) == Frame(weight_g=444.0, stable=False, flags=0xB3)


def test_resolution_is_a_tenth_of_a_gram() -> None:
    assert parse_frame(STABLE_1_5) == Frame(weight_g=1.5, stable=True, flags=0xB9)


def test_bad_checksum_is_rejected() -> None:
    corrupted = STABLE_652_5[:-1] + bytes([STABLE_652_5[-1] ^ 0x01])
    assert parse_frame(corrupted) is None


def test_wrong_length_or_header_is_rejected() -> None:
    assert parse_frame(STABLE_652_5[:-1]) is None
    assert parse_frame(b"\x11" + STABLE_652_5[1:]) is None
    assert parse_frame(b"") is None


def test_builder_round_trips_the_captured_frame() -> None:
    assert stable(652.5) == STABLE_652_5
