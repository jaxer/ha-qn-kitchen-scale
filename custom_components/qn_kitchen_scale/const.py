"""Constants for the QN Kitchen Scale integration."""

from __future__ import annotations

DOMAIN = "qn_kitchen_scale"

MANUFACTURER = "Qing Niu Technology"
MODEL = "QN-KS kitchen scale"

# Number of consecutive stable frames (5 Hz) before a reading counts as a measurement.
DEFAULT_STABLE_FRAMES = 3
# Readings below this are treated as an empty scale.
DEFAULT_MIN_WEIGHT_G = 1.0
# A new stable reading must differ from the previous measurement by at least this much...
DEFAULT_MIN_DELTA_G = 1.0
# ...or by this fraction of the previous measurement, whichever is larger.
DEFAULT_TOLERANCE = 0.01
# How many measurements are kept and exposed on the entity.
DEFAULT_HISTORY_SIZE = 50

STORAGE_VERSION = 1
