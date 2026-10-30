# Manufacturer and upstream sources

The project uses manufacturer specifications and pinned KiCad assets, not an
imported PicoGlitcher board. Links can change; verify the sourced device revision,
ordering suffix, package and operating conditions before procurement. Datasheet
PDFs/text extracts are **not redistributed** in this repository.

| Block | Manufacturer source |
| --- | --- |
| Pico 2 / RP2350 | [Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf), [RP2350](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf) |
| UCC27517 driver | [TI](https://www.ti.com/lit/ds/symlink/ucc27517.pdf) — UVLO/input/pinout/layout conditions |
| NX3L1T3157GMZ mux | [NXP](https://www.nxp.com/docs/en/data-sheet/NX3L1T3157.pdf), [SOT886](https://www.nxp.com/docs/en/package-information/SOT886.pdf) — current/drop/BBM/timing/analog limits |
| AP2112 target regulators | [Diodes](https://www.diodes.com/assets/Datasheets/AP2112.pdf) — pinout/startup/EN-low discharge/current limit; not an active dip-charge sink |
| TPS7A2036P retention regulator | [TI](https://www.ti.com/lit/ds/symlink/tps7a20.pdf) — revised pinout, EN on retained input, capacitor/accuracy conditions, active discharge and reverse-current limits |
| SN74LVC1G17 trigger | [TI](https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf) |
| SN74AXC4T774 optional UART | [TI](https://www.ti.com/lit/ds/symlink/sn74axc4t774.pdf) — directions/OE/isolation, ICCB off-supply source current and integrated data pulls |
| AO3400A crowbar | [AOS](https://aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf) |
| Si2377EDS disconnect | [Vishay](https://www.vishay.com/docs/65905/si2377eds.pdf) — low-VGS/hot resistance and slow gate behavior |
| 2N7002 controls | [Nexperia](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf) |
| BAT54WS diode | [Diodes](https://www.diodes.com/assets/Datasheets/BAT54WS.pdf) — DS30098, not DS30421 |
| LTST-C170KGKT LED | [Lite-On](https://optoelectronics.liteon.com/upload/download/DS22-2000-223/LTST-C170KGKT.pdf) |
| Yageo 15 Ω / 2 W input resistors | [RC_L series](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2312191106_YAGEO-RC2512FK-7W15RL_C6639259.pdf) — 7W power code, TCR/copper/derating; no pulse-overload credit |
| WSK2512 four-terminal shunt | [Vishay](https://www.vishay.com/docs/30108/wsk2512.pdf) — 0.005–0.2 Ω T=1.19 mm variant |
| EEE-FK reservoirs | [Panasonic](https://industrial.panasonic.com/cdbs/www-data/pdf/RDE0000/ABA0000C1181.pdf) |
| 1206L025YR PTC | [Littelfuse 1206L](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Littelfuse-1206L025YR_C99561.pdf) — hold/trip/resistance, 8 A trip-time test, fault current and dimensions |

All part-level links/requirements also appear in the generated
[all-parts BOM](../hardware/cipinkoklingacik-parts-all.csv). No live stock or price
is asserted. Some source servers block automated downloads; linked evidence is
not a blanket claim of archived documents or final sourced-package approval.

KiCad **10.0.7** footprints/primitives are pinned with hashes, source names and
licences in [hardware/vendor/](../hardware/vendor/README.md). 3D model hashes and
proxy limitations are in [visuals/](../hardware/visuals/README.md). Local assisted
routing provenance and review conclusions are in [REVIEW.md](../docs/REVIEW.md).
