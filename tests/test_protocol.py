"""The frame parser against captured frames."""

from custom_components.qn_kitchen_scale.protocol import Frame, parse_frame

from .frames import (
    MOVING_444,
    MOVING_MINUS_1591,
    MOVING_ZERO,
    STABLE_1_5,
    STABLE_652_5,
    STABLE_1595,
    STABLE_MINUS_1599,
    STABLE_ZERO,
    TARE_EVENT,
    moving,
    stable,
)


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


def test_above_one_kilogram_the_scale_counts_whole_grams() -> None:
    assert parse_frame(STABLE_1595) == Frame(weight_g=1595.0, stable=True, flags=0xA9)


def test_negative_readings_after_tare() -> None:
    assert parse_frame(STABLE_MINUS_1599) == Frame(weight_g=-1599.0, stable=True, flags=0xAA)
    assert parse_frame(MOVING_MINUS_1591) == Frame(weight_g=-1591.0, stable=False, flags=0xA2)


def test_tare_event_is_not_a_weight_frame() -> None:
    assert parse_frame(TARE_EVENT) is None


def test_builders_round_trip_the_captured_frames() -> None:
    assert stable(652.5) == STABLE_652_5
    assert stable(1595) == STABLE_1595
    assert parse_frame(stable(-1599)) == parse_frame(STABLE_MINUS_1599)
    assert parse_frame(moving(-1591)) == parse_frame(MOVING_MINUS_1591)
