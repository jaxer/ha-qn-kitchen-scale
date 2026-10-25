# QN-KS Bluetooth protocol

Captured from a Yolanda CK10A (firmware `V02.0`, manufacturer string `Qing Niu Technology`) with
`bleak` on macOS, 2026-10-25. The same hardware ships as Arboleaf CK10A and under other names;
the Bluetooth name is always `QN-KS`.

## Advertisement

* Local name `QN-KS`, service UUID `0000ffe0-0000-1000-8000-00805f9b34fb` in the advertisement.
* No weight in the advertisement: a connection is required.
* The scale only advertises while switched on; it sleeps after a few minutes idle and stops
  advertising, which drops the connection.

## GATT

| Service | Characteristic | Properties | Role |
|---|---|---|---|
| `180F` Battery | `2A19` | read | battery level, percent |
| `180A` Device Information | `2A29`, `2A26`, `2A23`, `2A25` | read | manufacturer, firmware, system ID, serial |
| `FFF0` | `FFF1` | notify | **weight stream** |
| `FFF0` | `FFF2` | write, write-without-response | unused: the stream starts on subscription |
| `AE00` | `AE01` write, `AE02` notify | | chip vendor channel, silent |

Subscribing to `FFF1` is enough; the scale streams at about 5 Hz with no command.

## Frame

18 bytes, for example `10 12 00 4c 01 02 05 01 b9 19 7d 7e 1f 02 58 02 01 c0` (652.5 g, stable):

| Offset | Meaning |
|---|---|
| 0–1 | header `10 12` (`0x12` = 18, the length) |
| 2–6 | constant `00 4c 01 02 05` in every frame seen |
| 7 | unit shown on the display, one bit each: `01` g, `02` ml, `04` ml (milk), `08` oz, `10` lb:oz. The weight in the frame stays in grams |
| 8 | flags, see below |
| 9–10 | magnitude of the weight, unsigned big-endian, in 0.1 g when flag bit 4 is set, else in 1 g (`0x197D` = 6525 → 652.5 g; `0x0641` = 1601 → 1601 g) |
| 11 | `7e` in 0.1 g steps, `3e` in 1 g steps (bit 6 mirrors flag bit 4) |
| 12–15 | constant `1f 02 58 02` in every frame seen |
| 16 | decimals the display shows in the current unit: `01` for g below 1 kg, oz and lb:oz; `00` for g from 1 kg up and for ml. Not needed to decode the weight |
| 17 | checksum: sum of bytes 0–16 modulo 256 |

### Flags (byte 8)

| Bit | Meaning |
|---|---|
| 0–1 | tare state: `00` no tare, positive weight; `01` tare set, net weight zero or positive; `11` tare set, positive; `10` tare set, **negative** |
| 2 | always 0 |
| 3 | reading is stable |
| 4 | 0.1 g steps (below 1 kg) |
| 5, 7 | always 1 |
| 6 | always 0 |

Values seen: `B9` stable, `B1` moving at zero, `B3` moving under load (0.1 g steps, tare set);
`A8` stable 1600 g right after power-on (no tare); `AB` stable +1601 g after tare; `AA` stable −1599 g after
tare and lifting the object; `A2` the same while moving.

Pressing tare sends one short frame `15 04 01 1a` before the weight frames resume at zero. Pressing tare
with nothing on the scale clears the tare state (bits 0–1 return to `00`). Switching the scale off and on
clears it as well.

## Differences from QN body scales

Body scales from the same vendor (`QN-Scale`, used by Renpho, FITINDEX and others) share the
`FFF0`/`FFF1` pair but use a different frame: weight in bytes 3–4 in kg/100 with byte 5 equal to 1.
Libraries written for them reject the kitchen-scale frame (byte 5 equals 2), which is why this
integration has its own parser.
