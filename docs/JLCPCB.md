# JLCPCB upload and sourcing — C4 baseline

**Quote/review package, not production approval.** This update **changes U6's
pinout and local routing**, repositions its bypass capacitors and replaces the
unavailable fuse/limiters with reviewed, stocked parts from established makers.
Use the regenerated ZIP/BOM/CPL together, not the previous TLV704 files.
Population is still 68 SMT placements. Firmware and physical qualification remain
open. Stock was rechecked on **2026-10-30**, not reserved; no order was placed.

## Upload these three files

| JLCPCB step | File |
| --- | --- |
| PCB / Gerber upload | [cipinkoklingacik-C4-bare-pcb.zip](../hardware/manufacturing/cipinkoklingacik-C4-bare-pcb.zip) |
| BOM | [jlcpcb-bom.csv](../hardware/manufacturing/assembly/jlcpcb-bom.csv) |
| CPL / placement | [jlcpcb-cpl.csv](../hardware/manufacturing/assembly/jlcpcb-cpl.csv) |

1. Quote **100 × 85 mm, 2 layers, 1.6 mm FR4, 1 oz, top-side assembly**.
   Start with Economic PCBA, single boards (no V-cut panel). Supplier review of
   U3's 0.5 mm-pitch XSON6/SOT886 and finish/process remains necessary. Compare
   2 versus 5 assembled boards; JLCPCB normally fabricates at least 5 bare boards.
2. Upload the **bare-board ZIP only** at the Gerber step, not the repository or
   release ZIP. Upload the supplier CSVs separately. **24 grouped SKUs expand to
   68 placements**, matching the CPL. Match `LCSC Part #`; do not accept automatic
   alternate/clone matches. Recheck stock including attrition at checkout.
3. Select **Confirm Parts Placement** and review JLCPCB's production file before
   assembly. Check U2–U7 pin 1, Q1–Q6 pin order, D1/D2 cathode and C4/C7/C9 positive
   pads. No supplier feeder rotations have been independently approved.
4. Match Gerber/CPL alignment. Coordinates are millimetres, X right, Y up, with
   the same upper-left origin as the exported Gerbers: **negative Mid Y is
   intentional**. Rotation is counterclockwise, normalized to 0–360 degrees.
   Do not flip Y, mirror or apply guessed ±90° rotations globally. If JLCPCB
   shifts the Gerber origin, the placement overlay needs the same translation.
   Resolve any mismatch before approving production.
5. JLCPCB normally derives paste from the selected BOM. If requested, provide
   the [baseline-only stencil](../hardware/manufacturing/stencil/cipinkoklingacik-F_Paste.gtp).
   **DNP pads must have no baseline paste**; check this in supplier review.

**C4 DFM correction:** C4/C7/C9/C11 ground vias are outside their SMT pad/mask/
paste openings, with ≥0.10 mm annulus clearance. Ordinary tented vias are used;
no filled/capped via-in-pad process is assumed. The baseline export check rejects
via annuli too close to fitted SMT solder openings. Use only the C4 ZIP together
with this BOM/CPL; earlier C3/TLV704 files are incompatible.

### Stocked replacements, not lower-quality clones

| Ref | Previous selection | New exact selection / LCSC | Snapshot stock |
| --- | --- | --- | ---: |
| U6 | TLV70436DBVR (12 stocked), then DBVT (50) | **Texas Instruments TPS7A2036PDBVR / C2873626** | **3,663** |
| F1 | Bourns MF-NSMF025X-2 (0) | **Littelfuse 1206L025YR / C99561** | **1,577** |
| R15, R16 | Vishay CRCW251215R0FKEGHP (0) | **Yageo RC2512FK-7W15RL / C6639259**, 15 Ω, 1%, **2 W** | **17,202** |

All **24 selected SKUs are stocked** in the revised snapshot, with no shortages
for 2/5/10 baseline boards even under the quantity allowance below. The catalog
field `minPurchaseNum=1` is **not** the assembly minimum charge: separate
`leastNumber`, `lossNumber` and `leastNumberPrice` fields are retained in the
snapshot/audit. Minimum charges do **not** prohibit a two-board assembly build.
All 68 references, including F1/R15/R16, remain in the upload BOM. Checkout still
determines actual availability, assembly eligibility, attrition and lead time.
**Never power an incomplete board, bridge F1 or bypass R15/R16.**

#### Engineering review of the substitutions

- **U6:** same manufacturer, fixed 3.6 V, SOT-23-5, but **IN1/GND2/EN3/NC4/OUT5**,
  not the TLV704 pinout. EN is wired directly to **HOLD_IN**, not AUX5, Pico or a
  GPIO, so USB removal does not prematurely disable the retention regulator.
  C10/C11 moved for direct input/output bypass routes (~2.26/~3.35 mm) and each
  has a nearby ground return. No other functional block was rerouted.
  The TPS7A20 requires ≥0.47 µF effective output C; C11 remains the specified
  Murata 1 µF/16 V X7R part. Its 6 V recommended input maximum covers this board's
  ≤5.25 V supply, but does not grant external/high-voltage input support.
  The P version actively discharges when disabled/UVLO and is **not reverse
  blocking**. Capture USB-loss/brownout/startup traces before use. Datasheet
  ±1.5% accuracy is specified at stated load/headroom conditions; it is not a
  measured guarantee at this board's tens-of-µA load. Accept 3.50–3.70 V on the
  actual board. Updated retention sizing uses 4.2→3.9 V input headroom and
  ≤100 µA total demand: **141 ms estimate**, not the old 235 ms figure.
- **F1:** a Littelfuse protection component, not a generic fuse clone. Both old
  and new parts specify 250 mA hold, 500 mA trip, 16 V, R1max=2.3 Ω and **80 ms
  maximum trip at 8 A** (the old Bourns value was not 8 seconds). Littelfuse's
  fault-current rating is 100 A versus 20 A; initial Rmin is 0.55 Ω versus 0.45 Ω.
  The 1206 envelope fits the existing land pattern. Still measure inrush, ambient
  derating and driver VDD: **4.90 V minimum at the driver remains mandatory**.
- **R15/R16:** choose the exact **2 W / 1%** Yageo code, not a 1 W or 5% lookalike.
  These are general-purpose resistors; no equivalence to Vishay's high-pulse
  overload capability is claimed or needed. The bounded 25°C peak is 0.756 W,
  below continuous rating. Including ±200 ppm/°C TCR over −40..125°C component
  temperature gives ~230 mA / **0.771 W**, still under the required ≥1 W actual-PCB
  capability. The 2 W nameplate is at the datasheet's reference mounting/ambient;
  qualify actual copper/temperature/fault duration. TCR is ±200 rather than the
  original ±100 ppm/°C: the arithmetic explicitly includes it. This is an
  application-specific replacement, not a claim every datasheet parameter improved.

Sources: [TI TPS7A20](https://www.ti.com/lit/ds/symlink/tps7a20.pdf) (SBVS338H,
pinout, operating conditions and active discharge),
[Littelfuse 1206L](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Littelfuse-1206L025YR_C99561.pdf)
(electrical table and dimensions),
[Yageo RC_L](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2312191106_YAGEO-RC2512FK-7W15RL_C6639259.pdf)
(7W power code, characteristics/derating, not pulse-overload credit).

### Not included in SMT assembly

Hand-fit **U1 Pico 2, J1–J5 and JP2**, two 1×20 carrier sockets and module headers.
Use [hand-fit](../hardware/manufacturing/assembly/baseline-hand-fit.csv) and
[accessory](../hardware/manufacturing/assembly/accessories-candidates.csv) lists.
Socket height and USB mating remain mechanically unapproved.
**JP2 ARM ships open; supply its shorting cap loose.**

U8, C18, JP3–JP5, R20, R31, R40 and R41 stay DNP. R39=0 Ω stays fitted. The eight
probe pads are PCB copper, not purchased parts. No UART/Kelvin option is enabled.

## Applied optimizations

The earlier Basic passive optimization is retained, with the additional stocked
replacement selections and the deliberate U6/C10/C11 layout change above:

| Value / package | Previous MPN | Selected MPN | LCSC | Baseline qty |
| --- | --- | --- | --- | ---: |
| 10 kΩ / 0805 | RC0805FR-0710KL | 0805W8F1002T5E | C17414 | 18 |
| 1 kΩ / 0805 | RC0805FR-071KL | 0805W8F1001T5E | C17513 | 5 |
| 100 Ω / 0805 | RC0805FR-07100RL | 0805W8F1000T5E | C17408 | 6 |
| 100 kΩ / 0805 | RC0805FR-07100KL | 0805W8F1003T5E | C149504 | 2 |
| 330 Ω / 0805 | RC0805FR-07330RL | 0805W8F3300T5E | C17630 | 2 |
| 2.2 Ω / 0805 | RC0805FR-072R2L | 0805W8F220KT5E | C17521 | 1 |
| 0 Ω / 1206 | RC1206JR-070RL | 1206W4F0000T5E | C17888 | 1 |
| 100 nF / 0805 | GRM21BR71H104KA01L | CC0805KRX7R9BB104 | C49678 | 5 |
| 3.6 V / SOT-23-5 | TLV70436DBVR / DBVT | TPS7A2036PDBVR | C2873626 | 1 |
| 250 mA hold / 1206 | MF-NSMF025X-2 | 1206L025YR | C99561 | 1 |
| 15 Ω / 2512 | CRCW251215R0FKEGHP | RC2512FK-7W15RL (2 W) | C6639259 | 2 |

The first eight lines are **Basic** parts, replacing eight paid Extended SKUs.
The existing AO3400A is also Basic: **9 Basic + 15 paid Extended SKUs** in total.
Nothing selected relies on temporary Promotional Extended status.

Uniroyal's [series datasheet](https://www.lcsc.com/datasheet/lcsc_datasheet_2411221126_UNI-ROYAL-Uniroyal-Elec-0805W8F1002T5E_C17414.pdf)
(Feb 2019 V3, pp. 2/4/5) confirms W8=1/8 W, F=1%, 0805 dimensions and resistance
range. `220K` encodes 220 × 10^-2 = **2.2 Ω**, not 220 Ω. R39 remains a 1206 jumper
(W4=1/4 W family); qualify current/contact resistance in the existing 17 Ω path
budget. R27 still needs gate-pulse validation. Yageo's [X7R datasheet](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_YAGEO-CC0805KRX7R9BB104_C49678.pdf)
confirms 0805, K=10%, 9=50 V and 104=100 nF: no reduced voltage/dielectric rating.
The old TLV704 pinout is obsolete for this layout; verify the **TPS7A20** pinout.

Nexperia 2N7002, Diodes BAT54WS, Lite-On LED, Murata 1 µF/10 µF, Panasonic
electrolytics and the other active devices are retained. Cross-brand
same-name transistors, unknown-brand diodes, higher-Vf LEDs and different-bias/
leakage capacitors are not automatic equivalents. The old TLV704 is **not
pin-compatible** with the revised U6; do not use it on the new routing.

## Budget, not a checkout quote

The [revised dated snapshot](../hardware/sourcing/jlcpcb-stock-2026-10-30-r2.json),
[per-SKU audit](../hardware/manufacturing/assembly/jlcpcb-sourcing.csv) and
[calculated estimates](../hardware/manufacturing/assembly/jlcpcb-cost-estimate.json)
make assumptions inspectable. Builds are offline and never refresh stock/prices
silently. The snapshot contains tiers needed for the quantities below.

At **$3.07/Extended SKU/order**, the 15 paid SKUs incur **$46.05** feeder charges.
Eight formerly paid Extended selections now use Basic parts. Historical total
component-cost savings are not quoted: a matching pre-optimization price snapshot
was not retained. The first snapshot is self-labelled historical and is not the
stock source for this upload package.

| Assembled boards | Parts, exact quantity only | Setup + stencil + confirmation + feeders | SMT placement | Subtotal | Assembly-only per board |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | $8.87 | $56.21 | $0.52 | **$65.59** | **$32.80** |
| 5 | $22.17 | $56.21 | $1.29 | **$79.67** | **$15.93** |
| 10 | $43.26 | $56.21 | $2.58 | **$102.05** | **$10.20** |

Formula: quantity-tier parts + $8.18 setup + $1.53 stencil + $0.45 placement
confirmation + 15 × $3.07 feeders + **N × 161 × $0.0016** solder-joint assembly.

The table above deliberately retains the **exact-quantity** basis, not a checkout
price. The report also supplies a separate **quantity-based planning allowance**:
for each SKU, price `max(build requirement + lossNumber, leastNumber,
minPurchaseNum)` at its captured quantity tier. This adds attrition **before**
taking the minimum, never `max(build, minimum) + loss`.

| Assembled boards | Parts quantity allowance | Assembly subtotal with allowance | Assembly-only per board |
| ---: | ---: | ---: | ---: |
| 2 | $18.43 | **$75.16** | $37.58 |
| 5 | $28.53 | **$86.03** | $17.21 |
| 10 | $48.87 | **$107.65** | $10.77 |

This allowance is **not JLCPCB's billing algorithm or a guaranteed upper bound**.
Supplier templates describe minimum fixed charges versus build-plus-attrition
charges; the raw API `leastNumberPrice` values are retained verbatim, but their
application/current billing must be confirmed at checkout. No unverified minimum
fee discount is used in this planning allowance. Assembly terms were separately
checked at **2026-10-30 12:41:56 UTC**; stock/prices retain their original timestamp.

**Excludes:** bare PCBs, attrition, procurement minimums/buy-in fees, X-ray (expect
leadless U3 to need it), special/nitrogen/pre-reflow processes, shipping/taxes,
Pico/sockets/headers and hand-fit labor. If the separate $0.016/joint pre-reflow
process applies, add **N × 161 × $0.016**: $5.15 / $12.88 / $25.76 respectively.
The old fuse/resistor procurement terms are not reused for their replacement SKUs;
checkout determines actual minimum charges, attrition and current unit prices.

These subtotals are **not the final price of complete working instruments**.
The earlier conversational ~$76 estimate used swaps not adopted here and
undercounted quantity-dependent charges. Use this explicit model and then
JLCPCB's quote instead. No shipping estimate or PCB promotion is assumed.

Sources: [fee schedule](https://jlcpcb.com/help/article/pcb-assembly-price),
[Basic/Promotional Extended rules](https://jlcpcb.com/parts/basic_parts),
[BOM format](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly),
[CPL format](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly),
[quantity/feeder explanations](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype).
Minimum/attrition evidence: [supplier placement template](https://cart.jlcpcb.com/client/template/placeOrder/component/smtOrders.html)
and [supplier component-detail template](https://cart.jlcpcb.com/client/template/placeOrder/component/componentDetails.html).

## Regeneration

`hardware_parts.py` owns selections and LCSC mapping; the schematic generator
emits those fields. `export_prototype.py` invokes offline `export_jlcpcb.py` and
binds the snapshot hash in the manufacturing manifest. Follow [BUILD.md](BUILD.md)
after changes; do not edit only upload CSVs. Format/parity tests do not approve
supplier rotations, procurement or physical qualification.
