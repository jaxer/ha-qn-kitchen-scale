"""Measurement detection over the frame stream."""

from datetime import UTC, datetime, timedelta

from custom_components.qn_kitchen_scale.protocol import parse_frame
from custom_components.qn_kitchen_scale.session import Measurement, MeasurementLog

from .frames import moving, stable

T0 = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)


def feed(log: MeasurementLog, frames: list[bytes], start: datetime = T0) -> list[Measurement]:
    """Feed frames 200 ms apart and collect the measurements they produce."""
    out = []
    for i, raw in enumerate(frames):
        frame = parse_frame(raw)
        assert frame is not None
        if (m := log.feed(frame, start + timedelta(milliseconds=200 * i))) is not None:
            out.append(m)
    return out


def test_an_object_left_on_the_scale_is_one_measurement() -> None:
    log = MeasurementLog()
    log.start_session()
    frames = [stable(0)] * 5 + [moving(300), moving(640)] + [stable(652.5)] * 20
    assert feed(log, frames) == [
        Measurement(
            at=T0 + timedelta(milliseconds=200 * 9), weight_g=652.5, delta_g=None, session=1
        )
    ]


def test_short_blips_do_not_count() -> None:
    log = MeasurementLog(stable_frames=3)
    log.start_session()
    assert feed(log, [stable(100)] * 2 + [moving(100)] + [stable(100)] * 2) == []


def test_adding_ingredients_records_each_step_with_its_delta() -> None:
    log = MeasurementLog()
    log.start_session()
    frames = (
        [stable(210)] * 3 + [moving(300)] + [stable(330)] * 3 + [moving(400)] + [stable(412.5)] * 3
    )
    weights = [(m.weight_g, m.delta_g) for m in feed(log, frames)]
    assert weights == [(210.0, None), (330.0, 120.0), (412.5, 82.5)]


def test_removing_and_replacing_the_same_item_records_it_again() -> None:
    log = MeasurementLog()
    log.start_session()
    frames = [stable(500)] * 3 + [moving(20)] + [stable(0)] * 3 + [moving(400)] + [stable(500)] * 3
    assert [m.weight_g for m in feed(log, frames)] == [500.0, 500.0]


def test_tiny_changes_are_noise() -> None:
    log = MeasurementLog(min_delta_g=0.5)
    log.start_session()
    frames = (
        [stable(100.0)] * 3
        + [moving(100.2)]
        + [stable(100.3)] * 3
        + [moving(101)]
        + [stable(101.0)] * 3
    )
    assert [m.weight_g for m in feed(log, frames)] == [100.0, 101.0]


def test_history_is_newest_first_and_bounded() -> None:
    log = MeasurementLog(history_size=3)
    log.start_session()
    frames: list[bytes] = []
    for w in (10, 20, 30, 40):
        frames += [stable(w)] * 3 + [moving(w + 5)]
    feed(log, frames)
    assert [m.weight_g for m in log.measurements] == [40.0, 30.0, 20.0]


def test_new_session_restarts_deltas() -> None:
    log = MeasurementLog()
    log.start_session()
    feed(log, [stable(100)] * 3)
    log.start_session()
    (m,) = feed(log, [stable(250)] * 3)
    assert m == Measurement(
        at=T0 + timedelta(milliseconds=400), weight_g=250.0, delta_g=None, session=2
    )


def test_measurement_survives_a_round_trip_through_dict() -> None:
    m = Measurement(at=T0, weight_g=12.5, delta_g=-3.0, session=4)
    assert Measurement.from_dict(m.as_dict()) == m


def test_clear_forgets_everything() -> None:
    log = MeasurementLog()
    log.start_session()
    feed(log, [stable(100)] * 3)
    log.clear()
    assert log.measurements == []
    assert [m.weight_g for m in feed(log, [stable(100)] * 3)] == [100.0]
