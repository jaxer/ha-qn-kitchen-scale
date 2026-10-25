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
| 2–7 | constant `00 4c 01 02 05 01` in every frame seen |
| 8 | flags: bit 3 set when the reading is stable. Seen: `B9` stable, `B1` moving at zero, `B3` moving under load |
| 9–10 | weight, unsigned big-endian, unit 0.1 g (`0x197D` = 6525 → 652.5 g) |
| 11–16 | constant `7e 1f 02 58 02 01` in every frame seen |
| 17 | checksum: sum of bytes 0–16 modulo 256 |

Only grams were observed; the display unit button was not exercised, so other units may change
bytes 11–16 or the scale factor. Reports welcome.

## Differences from QN body scales

Body scales from the same vendor (`QN-Scale`, used by Renpho, FITINDEX and others) share the
`FFF0`/`FFF1` pair but use a different frame: weight in bytes 3–4 in kg/100 with byte 5 equal to 1.
Libraries written for them reject the kitchen-scale frame (byte 5 equals 2), which is why this
integration has its own parser.
