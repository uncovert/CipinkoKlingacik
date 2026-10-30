#!/usr/bin/env python3
"""Generate the C4 KiCad schematic, local symbols and candidate BOMs.

Requires the pinned hardware requirements and vendored primitive symbols.
This is a generator-owned, net-labelled schematic, not a round-trip GUI editor.
It is not a fabrication release or measured electrical qualification.

Run from the project root:
    python3 scripts/generate_kicad_schematic.py

Outputs:
    hardware/cipinkoklingacik.kicad_sch
    hardware/cipinkoklingacik.kicad_sym
    hardware/sym-lib-table
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import uuid
import copy
import csv
import json

from hardware_parts import select_part

from kiutils.schematic import Schematic, SchematicSymbol, LocalLabel, Connection, NoConnect
from kiutils.items.schitems import (
    SymbolProjectInstance, SymbolProjectPath, Text,
)
from kiutils.items.common import Position, Justify, Effects, Font, Stroke, Fill, TitleBlock
from kiutils.items.syitems import SyRect, SyPolyLine, SyCircle
from kiutils.symbol import Symbol, SymbolPin, Property, SymbolLib

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "hardware"
PROJECT = "cipinkoklingacik"
FONT = Effects(Font(height=1.27, width=1.27))
HIDE = Effects(Font(height=1.27, width=1.27), hide=True)


def u(key: str) -> str:
    """Keep the legacy UUID seed unchanged: rebranding must not detach PCB pads."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"glitchpico/concept-c/{key}"))


def g(n: float) -> float:
    """Grid coordinate: 1 unit = 1.27 mm."""
    return round(n * 1.27, 2)


@dataclass
class PinDef:
    name: str
    number: str
    x: float
    y: float
    angle: int
    etype: str = "passive"
    length: float = 2.54
    hide_name: bool = False
    hide_number: bool = False


@dataclass
class SymDef:
    name: str
    ref_prefix: str
    body_w: float
    body_h: float
    pins: list[PinDef]
    graphics: list = field(default_factory=list)
    show_pin_names: bool = True
    show_pin_numbers: bool = True
    pin_length: float = 2.54


def body_rect(w: float, h: float, fill: str = "none") -> SyRect:
    return SyRect(
        start=Position(-w / 2, -h / 2), end=Position(w / 2, h / 2),
        stroke=Stroke(0.254, "default"), fill=Fill(fill),
    )


def line(points, width=0.254):
    return SyPolyLine(
        points=[Position(x, y) for x, y in points],
        stroke=Stroke(width, "default"), fill=Fill("none"),
    )


def build_symbol(d: SymDef) -> Symbol:
    graphics = [body_rect(d.body_w, d.body_h)] + list(d.graphics)
    pins = []
    for p in d.pins:
        ne = HIDE if p.hide_name else FONT
        nu = HIDE if p.hide_number else FONT
        pins.append(SymbolPin(
            electricalType=p.etype, graphicalStyle="line",
            position=Position(p.x, p.y, p.angle), length=p.length,
            name=p.name, number=p.number,
            nameEffects=ne, numberEffects=nu,
        ))
    unit = Symbol(
        entryName=d.name, unitId=1, styleId=1,
        graphicItems=graphics, pins=pins,
    )
    lib = Symbol(
        libraryNickname="CipinkoKlingacik", entryName=d.name,
        inBom=True, onBoard=True,
        pinNames=d.show_pin_names, pinNamesOffset=0.508,
        pinNamesHide=not d.show_pin_names,
        hidePinNumbers=not d.show_pin_numbers,
        properties=[
            Property("Reference", d.ref_prefix, 0, Position(0, d.body_h / 2 + 2.54, 0), FONT),
            Property("Value", d.name, 1, Position(0, -d.body_h / 2 - 2.54, 0), FONT),
            Property("Footprint", "", 2, Position(0, 0, 0), HIDE),
            Property("Datasheet", "", 3, Position(0, 0, 0), HIDE),
        ],
        units=[unit],
    )
    lib.libId = f"CipinkoKlingacik:{d.name}"
    return lib


def make_symbols() -> dict[str, SymDef]:
    syms: dict[str, SymDef] = {}

    syms["R"] = SymDef("R", "R", 2.032, 5.08, [
        PinDef("~", "1", 0, 3.81, 270, length=1.27, hide_name=True, hide_number=True),
        PinDef("~", "2", 0, -3.81, 90, length=1.27, hide_name=True, hide_number=True),
    ], show_pin_names=False, show_pin_numbers=False)

    syms["C"] = SymDef("C", "C", 3.048, 5.08, [
        PinDef("~", "1", 0, 3.81, 270, length=2.54, hide_name=True, hide_number=True),
        PinDef("~", "2", 0, -3.81, 90, length=2.54, hide_name=True, hide_number=True),
    ], graphics=[line([(-1.524, 0.5), (1.524, 0.5)]), line([(-1.524, -0.5), (1.524, -0.5)])],
        show_pin_names=False, show_pin_numbers=False)

    syms["D"] = SymDef("D", "D", 3.048, 5.08, [
        PinDef("A", "1", 0, 3.81, 270, length=2.54, hide_name=True, hide_number=True),
        PinDef("K", "2", 0, -3.81, 90, length=2.54, hide_name=True, hide_number=True),
    ], graphics=[line([(-1.524, 1.0), (1.524, 1.0), (0, -1.0), (-1.524, 1.0)]),
                 line([(-1.524, -1.0), (1.524, -1.0)])],
        show_pin_names=False, show_pin_numbers=False)

    syms["PTC"] = SymDef("PTC", "F", 2.032, 5.08, [
        PinDef("~", "1", 0, 3.81, 270, length=1.27, hide_name=True, hide_number=True),
        PinDef("~", "2", 0, -3.81, 90, length=1.27, hide_name=True, hide_number=True),
    ], show_pin_names=False, show_pin_numbers=False)

    # Simple generic MOSFET symbols: G left, S bottom, D top.
    for kind in ("NMOS", "PMOS"):
        extra = []
        if kind == "PMOS":
            extra.append(line([(-0.6, 0), (0.6, 0)]))
        syms[kind] = SymDef(kind, "Q", 6.35, 10.16, [
            PinDef("G", "1", -5.08, 0, 0, "input", 2.54),
            PinDef("S", "2", 0, -6.35, 90, "passive", 2.54),
            PinDef("D", "3", 0, 6.35, 270, "passive", 2.54),
        ], graphics=[
            line([(-2.54, 0), (-1.27, 0)]),
            line([(-1.27, -2.54), (-1.27, 2.54)]),
            line([(0, -3.81), (0, 3.81)]),
            line([(0, -3.81), (1.27, -3.81)]),
            line([(0, 3.81), (1.27, 3.81)]),
        ] + extra, show_pin_names=True, show_pin_numbers=True)

    def ic2(name, ref, w, h, left, right, extra_graphics=None):
        pins = []
        for pname, pnum, y in left:
            pins.append(PinDef(pname, str(pnum), -w / 2 - 2.54, y, 0, "passive", 2.54))
        for pname, pnum, y in right:
            pins.append(PinDef(pname, str(pnum), w / 2 + 2.54, y, 180, "passive", 2.54))
        return SymDef(name, ref, w, h, pins, graphics=extra_graphics or [],
                      show_pin_names=True, show_pin_numbers=True)

    syms["U2"] = ic2("U2", "U", 20.32, 22.86,
        [("VDD", 1, 7.62), ("GND", 2, 2.54), ("IN+", 3, -2.54), ("IN-", 4, -7.62)],
        [("OUT", 5, 0)])
    syms["U3"] = ic2("U3", "U", 20.32, 27.94,
        [("Y1", 1, 10.16), ("GND", 2, 0), ("Y0", 3, -10.16)],
        [("Z", 4, 10.16), ("VCC", 5, 0), ("S", 6, -10.16)])
    syms["U4"] = ic2("U4", "U", 20.32, 22.86,
        [("VIN", 1, 7.62), ("GND", 2, 0), ("EN", 3, -7.62)],
        [("NC", 4, 7.62), ("VOUT", 5, -7.62)])
    syms["U5"] = ic2("U5", "U", 20.32, 22.86,
        [("VIN", 1, 7.62), ("GND", 2, 0), ("EN", 3, -7.62)],
        [("NC", 4, 7.62), ("VOUT", 5, -7.62)])
    syms["U6"] = ic2("U6", "U", 20.32, 17.78,
        [("IN", 1, 5.08), ("GND", 2, 0), ("EN", 3, -5.08)],
        [("OUT", 5, 5.08), ("NC", 4, -5.08)])
    syms["U7"] = ic2("U7", "U", 20.32, 22.86,
        [("NC", 1, 7.62), ("A", 2, 0), ("GND", 3, -7.62)],
        [("Y", 4, 5.08), ("VCC", 5, -5.08)])

    u8_left = [
        ("DIR1", 1, 17.78), ("DIR2", 2, 12.7), ("A1", 3, 7.62), ("A2", 4, 2.54),
        ("A3", 5, -2.54), ("A4", 6, -7.62), ("DIR3", 7, -12.7), ("DIR4", 8, -17.78),
    ]
    u8_right = [
        ("VCCA", 16, 17.78), ("VCCB", 15, 12.7), ("B1", 14, 7.62), ("B2", 13, 2.54),
        ("B3", 12, -2.54), ("B4", 11, -7.62), ("GND", 10, -12.7), ("OE", 9, -17.78),
    ]
    syms["U8"] = ic2("U8", "U", 25.4, 45.72, u8_left, u8_right)
    syms["SHUNT4"] = ic2("SHUNT4", "R", 12.7, 12.7,
        [("FORCE+", 1, 2.54), ("SENSE+", 2, -2.54)],
        [("SENSE-", 3, -2.54), ("FORCE-", 4, 2.54)])

    # Used pins on the right; every remaining socket pin explicit on the left.
    pico_pins = [
        ("GP0", 1), ("GP1", 2), ("GP2", 4), ("GP3", 5), ("GP4", 6), ("GP5", 7),
        ("GP6", 9), ("GP7", 10), ("GP8", 11), ("GP9", 12), ("GP10", 14),
        ("3V3", 36), ("VBUS", 40), ("GND", 3), ("GND", 8), ("GND", 13),
        ("GND", 38), ("AGND", 33),
    ]
    pins = []
    top = 35.56
    for i, (name, num) in enumerate(pico_pins):
        etype = "power_out" if name == "3V3" else "power_in" if name in ("VBUS", "GND", "AGND") else "bidirectional"
        pins.append(PinDef(name, str(num), 20.32, top - i * 5.08, 180, etype, 5.08))
    unused = [("GP11", 15), ("GP12", 16), ("GP13", 17), ("GND", 18),
              ("GP14", 19), ("GP15", 20), ("GP16", 21), ("GP17", 22),
              ("GND", 23), ("GP18", 24), ("GP19", 25), ("GP20", 26),
              ("GP21", 27), ("GND", 28), ("GP22", 29), ("RUN", 30),
              ("GP26_ADC0", 31), ("GP27_ADC1", 32), ("GP28_ADC2", 34),
              ("ADC_VREF", 35), ("3V3_EN", 37), ("VSYS", 39)]
    for i, (name, num) in enumerate(unused):
        etype = "power_in" if name in ("GND", "VSYS") else "input" if name in ("RUN", "3V3_EN") else "bidirectional"
        pins.append(PinDef(name, str(num), -20.32, 53.34 - i * 5.08, 0, etype, 5.08))
    syms["PICO"] = SymDef("PICO", "U", 30.48, 116.84, pins,
                          show_pin_names=True, show_pin_numbers=True, pin_length=5.08)

    # Connectors and jumpers.
    syms["CONN2"] = SymDef("CONN2", "J", 5.08, 10.16, [
        PinDef("1", "1", 5.08, 2.54, 180, "passive", 2.54),
        PinDef("2", "2", 5.08, -2.54, 180, "passive", 2.54),
    ], show_pin_names=False, show_pin_numbers=True)
    syms["CONN3"] = SymDef("CONN3", "J", 5.08, 12.7, [
        PinDef("1", "1", 5.08, 5.08, 180, "passive", 2.54),
        PinDef("2", "2", 5.08, 0, 180, "passive", 2.54),
        PinDef("3", "3", 5.08, -5.08, 180, "passive", 2.54),
    ], show_pin_names=False, show_pin_numbers=True)
    syms["JP2"] = SymDef("JP2", "JP", 3.048, 5.08, [
        PinDef("1", "1", 0, 3.81, 270, "passive", 1.27),
        PinDef("2", "2", 0, -3.81, 90, "passive", 1.27),
    ], show_pin_names=False, show_pin_numbers=True)
    syms["TP"] = SymDef("TP", "TP", 2.0, 2.0, [
        PinDef("1", "1", 0, 0, 180, "passive", 2.54),
    ], graphics=[SyCircle(center=Position(0, 0), radius=0.8,
                          stroke=Stroke(0.254, "default"), fill=Fill("none"))],
        show_pin_names=False, show_pin_numbers=False)
    syms["PWR_FLAG"] = SymDef("PWR_FLAG", "#FLG", 2.54, 2.54, [
        PinDef("PWR_FLAG", "1", 0, 0, 180, "power_out", 2.54),
    ], graphics=[line([(0, 0), (0, 1.27)]), line([(-1.27, 1.27), (1.27, 1.27), (0, 2.54), (-1.27, 1.27)])],
        show_pin_names=True, show_pin_numbers=False)
    return syms



# Placement overrides; values are 1.27 mm grid units.
LAYOUT = {
    "U1": (40, 92),
    "R1": (100, 30), "R2": (100, 50), "R3": (100, 70), "R4": (100, 90),
    "R5": (100, 110), "R6": (100, 130), "R7": (125, 30), "D2": (125, 50),
    "R8": (125, 70), "R35": (125, 90), "R9": (125, 110), "R10": (125, 130),
    "U4": (185, 40), "C3": (155, 40), "C4": (220, 40), "C5": (240, 40), "R11": (265, 40),
    "U5": (185, 80), "C6": (155, 80), "C7": (220, 80), "C8": (240, 80), "R12": (265, 80),
    "D1": (160, 135), "R13": (180, 135), "C9": (200, 135), "C10": (220, 135),
    "U6": (255, 135), "C11": (280, 120), "R14": (280, 145),
    "R15": (315, 35), "R16": (315, 75), "U3": (350, 55), "C12": (375, 55),
    "R36": (335, 105), "R37": (355, 105), "Q2": (400, 30), "Q3": (400, 65),
    "R17": (430, 25), "Q4": (400, 105), "R38": (380, 105),
    "R18": (420, 105), "R19": (440, 80), "R39": (395, 145), "R20": (420, 145),
    "J2": (440, 130), "R21": (440, 155),
    "F1": (165, 195), "C1": (185, 195), "C2": (205, 195),
    "U2": (300, 210), "R22": (270, 195), "R23": (270, 220),
    "C13": (285, 245), "C14": (305, 245), "R24": (335, 190),
    "Q1": (370, 215), "R27": (345, 215), "R28": (365, 245), "J1": (420, 215),
    "Q6": (230, 240), "R25": (190, 240), "R26": (210, 240), "JP2": (250, 240),
    "Q5": (50, 200), "R29": (20, 200), "R30": (35, 235), "R31": (60, 235), "J3": (80, 200),
    "U7": (110, 230), "R32": (80, 230), "R33": (80, 255), "C16": (130, 255), "J4": (110, 190),
    "U8": (205, 290), "C17": (170, 280), "C18": (170, 305), "R34": (245, 275),
    "JP3": (265, 280), "JP4": (265, 305), "JP5": (290, 280), "J5": (290, 305),
    "R40": (315, 280), "R41": (315, 305),
    "TP1": (330, 275), "TP2": (330, 290), "TP3": (330, 305),
    "TP4": (365, 275), "TP5": (365, 290), "TP6": (365, 305),
    "TP7": (410, 165), "TP8": (435, 165),
    "#FLG01": (400, 275), "#FLG02": (400, 285), "#FLG03": (400, 295),
    "#FLG04": (430, 275), "#FLG05": (430, 285), "#FLG06": (430, 295),
}

SYMS = make_symbols()

def _set_types(name: str, mapping: dict[str, str]) -> None:
    for p in SYMS[name].pins:
        if p.name in mapping:
            p.etype = mapping[p.name]


_set_types("U2", {"VDD": "power_in", "GND": "power_in", "IN+": "input",
                   "IN-": "input", "OUT": "output"})
_set_types("U3", {"VCC": "power_in", "GND": "power_in", "S": "input"})
for _u in ("U4", "U5"):
    _set_types(_u, {"VIN": "power_in", "GND": "power_in", "EN": "input",
                    "NC": "no_connect", "VOUT": "power_out"})
_set_types("U6", {"GND": "power_in", "IN": "power_in", "OUT": "power_out",
                  "EN": "input", "NC": "no_connect"})
_set_types("U7", {"NC": "no_connect", "A": "input", "GND": "power_in",
                  "Y": "output", "VCC": "power_in"})
_set_types("U8", {"VCCA": "power_in", "VCCB": "power_in", "GND": "power_in",
                  "DIR1": "input", "DIR2": "input", "DIR3": "input", "DIR4": "input",
                   "OE": "input", "A1": "input", "A2": "tri_state",
                   "A3": "tri_state", "A4": "tri_state",
                   "B1": "tri_state", "B2": "input",
                   "B3": "input", "B4": "input"})

LIB_SYMBOLS = {name: build_symbol(d) for name, d in SYMS.items()}

# Conventional graphics/polarity from vendored KiCad primitives. Coordinates
# come from the actual symbol, not an assumption about its drawing.
PRIMITIVES = SymbolLib.from_file(str(OUT / "vendor" / "primitives.kicad_sym"))
for local, upstream in {"R": "R", "C": "C", "CP": "C_Polarized",
                        "D": "D_Schottky", "LED": "LED",
                        "NMOS": "Q_NMOS_GSD", "PMOS": "Q_PMOS_GSD"}.items():
    lib = copy.deepcopy(next(s for s in PRIMITIVES.symbols if s.entryName == upstream))
    lib.libId = f"CipinkoKlingacik:{local}"
    for unit in lib.units:
        unit.entryName = local
    LIB_SYMBOLS[local] = lib
    pins = [p for unit in lib.units for p in unit.pins]
    SYMS[local] = SymDef(local, "Q" if local.endswith("MOS") else local[0], 6.35, 10.16,
                        [PinDef(p.name, p.number, p.position.X, p.position.Y,
                                p.position.angle, p.electricalType, p.length) for p in pins])



NET_ALIAS = {
    "CROWBAR_PULSE": "CB_PULSE", "TARGET_ON": "TGT_ON", "TARGET_ON_G": "TGT_G",
    "MUX_LOW": "MUX_CMD", "RESET_ASSERT": "RST_ASSERT", "DRIVER_ARM": "ARM_EN",
    "UART_DISABLE": "UART_OE", "TRIGGER_RAW": "TRIG_IN", "TRIGGER_IN": "TRIG_F",
    "TRIGGER_OUT": "TRIG_OUT", "TARGET_VDD": "TVDD", "TARGET_PRE": "T_PRE",
    "MUX_VCC": "MVCC", "MUX_Y0": "MY0", "MUX_Y1": "MY1", "MUX_Z": "MZ",
    "RESET_TARGET": "RST_T", "RESET_G": "RST_G", "UART_TGT_RX": "URX_T",
    "UART_TGT_TX": "UTX_T", "UART_CONN_RX": "URX_C", "UART_CONN_TX": "UTX_C",
    "UART_VCCB": "UVCCB", "PICO_3V3": "3V3", "AUX_5V": "AUX5", "USB_VBUS": "VBUS",
    "HOLD_IN": "HOLD", "RET_CHG": "RET", "Q23_G": "Q23G", "Q23_S": "Q23S",
    "U2_INP": "U2P", "U2_INN": "U2N", "U2_OUT": "U2O", "Q1_G": "Q1G",
    "ARM_GATE": "AG", "ARM_LINK": "AL", "EN_DRIVE": "EN", "RAILS_EN": "REN",
    "LED_ARM": "LED", "LED_A": "LEDA", "UART_TX": "UTX", "UART_RX": "URX",
    "GLITCH": "GL", "VHIGH": "VH", "VLOW": "VL", "GND": "GND",
    "MUX_SELECT": "MUX_S", "DISCONNECT_DRAIN": "Q4D",
    "EN_HIGH": "EN_H", "EN_LOW": "EN_L",
}

@dataclass
class Placed:
    d: SymDef
    ref: str
    x: float
    y: float
    instance: SchematicSymbol

    def pin(self, number: str) -> PinDef:
        for p in self.d.pins:
            if p.number == number:
                return p
        raise KeyError(f"{self.d.name} has no pin {number}")

    def abs_pin(self, number: str) -> tuple[float, float]:
        p = self.pin(number)
        return self.x + p.x, self.y - p.y


class Builder:
    def __init__(self) -> None:
        self.root_uuid = u("root")
        self.s = Schematic.create_new()
        self.s.uuid = self.root_uuid
        self.s.paper.paperSize = "A2"
        self.s.paper.portrait = False
        self.s.titleBlock = TitleBlock(
            title="ČipinkoKlingáčik C4 - engineering prototype", date="2026-10-30", revision="C4",
            company="ČipinkoKlingáčik contributors",
            comments={1: "Engineering prototype - sourcing/assembly approval and hardware qualification pending"},
        )
        self.s.libSymbols = list(LIB_SYMBOLS.values())
        self.s.schematicSymbols = []
        self.s.labels = []
        self.s.junctions = []
        self.s.noConnects = []
        self.s.texts = []
        self.placed: dict[str, Placed] = {}
        self.bom = []
        self.contract = {}

    def _pos(self, x: float, y: float) -> tuple[float, float]:
        return g(x), g(y)

    def place(self, sym: str, ref: str, value: str, x: float, y: float,
              footprint: str = "", note: str = "", in_bom: bool = True,
              on_board: bool = True, hide_value: bool = False) -> Placed:
        d = SYMS[sym]
        selected = select_part(ref, sym, value)
        if selected:
            footprint = selected.footprint
        if ref in LAYOUT:
            x, y = g(LAYOUT[ref][0]), g(LAYOUT[ref][1])
        else:
            x, y = self._pos(x, y)
        hid = HIDE
        ref_y = y - d.body_h / 2 - 2.54
        val_y = y + d.body_h / 2 + 2.54
        props = [
            Property("Reference", ref, 0, Position(x, ref_y, 0), FONT),
            Property("Value", value, 1, Position(x, val_y, 0), hid if hide_value else FONT),
            Property("Footprint", footprint, 2, Position(x, y, 0), hid),
            Property("Datasheet", selected.datasheet if selected else "", 3, Position(x, y, 0), hid),
        ]
        if sym in ("R", "C", "CP", "PTC", "JP2"):
            # Keep reference/value away from the vertical net labels.
            for prop, dy in zip(props[:2], (-1.27, 1.27)):
                prop.position = Position(x + 3.81, y + dy, 0)
                prop.effects = Effects(Font(height=1.27, width=1.27), Justify(horizontally="left"))
        elif sym in ("NMOS", "PMOS"):
            for prop, dy in zip(props[:2], (-2.54, 0)):
                prop.position = Position(x + 7.62, y + dy, 0)
                prop.effects = Effects(Font(height=1.27, width=1.27), Justify(horizontally="left"))
        elif sym == "PWR_FLAG":
            props[0].effects = HIDE
        elif sym == "TP":
            props[1].effects = HIDE
        if selected:
            metadata = {"MPN": selected.mpn, "Manufacturer": selected.manufacturer,
                        "Requirement": selected.requirement, "Assembly": selected.assembly,
                        "LCSC": selected.lcsc}
            for key, content in metadata.items():
                props.append(Property(key, content, len(props), Position(x, y, 0), hid))
            self.bom.append({"Reference": ref, "Value": value, "MPN": selected.mpn,
                             "Manufacturer": selected.manufacturer, "Footprint": footprint,
                             "DNP": "yes" if not in_bom else "no", "Assembly": selected.assembly,
                             "Requirement": selected.requirement, "Datasheet": selected.datasheet,
                             "LCSC": selected.lcsc})
        if note:
            props.append(Property("Note", note, len(props), Position(x, val_y + 2.54, 0), HIDE))
        inst = SchematicSymbol(
            libraryNickname="CipinkoKlingacik", entryName=sym,
            libName=f"CipinkoKlingacik:{sym}", position=Position(x, y, 0),
            unit=1, inBom=bool(selected and sym != "TP"), onBoard=on_board,
            dnp=bool(selected and not in_bom),
            uuid=u(f"symbol/{ref}"),
            properties=props,
            pins={p.number: u(f"pin/{ref}/{p.number}") for p in d.pins},
            instances=[SymbolProjectInstance(PROJECT, [
                SymbolProjectPath(f"/{self.root_uuid}", ref, 1)
            ])],
        )
        self.s.schematicSymbols.append(inst)
        placed = Placed(d, ref, x, y, inst)
        self.placed[ref] = placed
        return placed

    def label(self, placed: Placed, pin_number: str, net: str) -> None:
        px, py = placed.abs_pin(pin_number)
        p = placed.pin(pin_number)
        if p.angle == 0:       # left-side pin, outward left
            lx, ly, ang, just = px - 2.54, py, 0, "right"
        elif p.angle == 180:   # right-side pin, outward right
            lx, ly, ang, just = px + 2.54, py, 0, "left"
        elif p.angle == 270:   # top pin, outward up
            lx, ly, ang, just = px, py - 2.54, 90, "left"
        elif p.angle == 90:    # bottom pin, outward down
            lx, ly, ang, just = px, py + 2.54, 90, "right"
        else:
            raise ValueError(p.angle)
        self.s.graphicalItems.append(Connection(
            type="wire", points=[Position(px, py), Position(lx, ly)],
            stroke=Stroke(0.0, "default"), uuid=u(f"wire/{placed.ref}/{pin_number}"),
        ))
        self.s.labels.append(LocalLabel(
            text=NET_ALIAS.get(net, net), position=Position(lx, ly, ang),
            effects=Effects(Font(height=1.27, width=1.27),
                            Justify(horizontally=just)),
            uuid=u(f"label/{placed.ref}/{pin_number}"),
        ))

    def label_all(self, placed: Placed, mapping: dict[str, str | None]) -> None:
        expected = {p.number for p in placed.d.pins}
        if set(mapping) != expected:
            raise ValueError(f"{placed.ref}: missing/extra pin mapping {set(mapping) ^ expected}")
        self.contract[placed.ref] = {p: NET_ALIAS.get(net, net) for p, net in mapping.items()}
        for p in placed.d.pins:
            net = mapping.get(p.number)
            if net is None:
                self.s.noConnects.append(NoConnect(position=Position(*placed.abs_pin(p.number)), uuid=u(f"nc/{placed.ref}/{p.number}")))
            elif net:
                self.label(placed, p.number, net)
            else:
                raise ValueError(f"missing mapping for {placed.ref} pin {p.number}")

    def text(self, x: float, y: float, text: str, size: float = 2.0) -> None:
        xm, ym = self._pos(x, y)
        self.s.texts.append(Text(
            text=text, position=Position(xm, ym, 0),
            effects=Effects(Font(height=size, width=size), Justify(horizontally="left")), uuid=u(f"text/{x}/{y}"),
        ))

    def write(self) -> None:
        OUT.mkdir(exist_ok=True)
        self.s.to_file(str(OUT / "cipinkoklingacik.kicad_sch"))
        lib_file_symbols = []
        for name, lib in LIB_SYMBOLS.items():
            item = copy.deepcopy(lib)
            item.libId = name
            lib_file_symbols.append(item)
        SymbolLib(version="20211014", generator="kiutils",
                  symbols=lib_file_symbols).to_file(str(OUT / "cipinkoklingacik.kicad_sym"))
        (OUT / "sym-lib-table").write_text(
            '(sym_lib_table\n'
            '  (version 7)\n'
            '  (lib (name "CipinkoKlingacik")(type "KiCad")'
            '(uri "${KIPRJMOD}/cipinkoklingacik.kicad_sym")(options "")'
            '(descr "ČipinkoKlingáčik project symbols"))\n'
            ')\n'
        )
        (OUT / "fp-lib-table").write_text(
            '(fp_lib_table\n  (version 7)\n'
            '  (lib (name "CipinkoKlingacik")(type "KiCad")'
            '(uri "${KIPRJMOD}/CipinkoKlingacik.pretty")(options "")(descr "Pinned KiCad footprints"))\n)\n'
        )
        (OUT / "cipinkoklingacik-connectivity.json").write_text(json.dumps(self.contract, indent=2) + "\n")
        for filename, rows in (("cipinkoklingacik-parts-all.csv", self.bom),
                               ("cipinkoklingacik-bom.csv", [r for r in self.bom if r["DNP"] == "no" and r["Assembly"] != "PCB feature"])):
            with (OUT / filename).open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(self.bom[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)


def main() -> int:
    b = Builder()

    # ---- Pico and control defaults -------------------------------------------------
    pico = b.place("PICO", "U1", "Raspberry Pi Pico 2", 40, 165,
                   note="Full 40-pin socket; module/headers/sockets hand fitted")
    pico_mapping = {p.number: None for p in pico.d.pins}
    pico_mapping.update({
        "1": "UART_TX", "2": "UART_RX", "4": "CROWBAR_PULSE", "5": "TRIGGER_OUT",
        "6": "TARGET_ON", "7": "MUX_LOW", "9": "RESET_ASSERT", "10": "LED_ARM",
        "11": "DRIVER_ARM", "12": "UART_DISABLE", "14": "RAILS_EN",
        "36": "PICO_3V3", "40": "USB_VBUS",
        "3": "GND", "8": "GND", "13": "GND", "18": "GND", "23": "GND",
        "28": "GND", "38": "GND", "33": "GND",
    })
    b.label_all(pico, pico_mapping)

    def two(sym, ref, value, x, y, a, bb, note="", in_bom=True, footprint=""):
        p = b.place(sym, ref, value, x, y, note=note, in_bom=in_bom, footprint=footprint)
        b.label_all(p, {"1": a, "2": bb})
        return p

    two("R", "R1", "10k", 120, 250, "CROWBAR_PULSE", "GND")
    two("R", "R2", "10k", 120, 235, "TARGET_ON", "GND")
    two("R", "R3", "10k", 120, 220, "MUX_LOW", "GND")
    two("R", "R4", "10k", 120, 205, "RESET_ASSERT", "GND")
    two("R", "R5", "10k", 120, 190, "DRIVER_ARM", "GND")
    two("R", "R6", "10k", 120, 175, "UART_DISABLE", "PICO_3V3")
    two("R", "R7", "1k", 120, 150, "LED_ARM", "LED_A")
    two("LED", "D2", "Green LED", 135, 150, "GND", "LED_A")
    two("R", "R8", "1k", 120, 125, "RAILS_EN", "EN_HIGH")
    two("R", "R9", "10k", 145, 150, "EN_HIGH", "GND")
    two("R", "R10", "10k", 145, 135, "EN_LOW", "GND")
    two("R", "R35", "1k", 120, 105, "RAILS_EN", "EN_LOW")

    # ---- Auxiliary input and crowbar ------------------------------------------------
    two("PTC", "F1", "250 mA hold", 125, 260, "USB_VBUS", "AUX_5V")
    two("C", "C1", "10uF", 145, 260, "AUX_5V", "GND")
    two("C", "C2", "100nF", 160, 260, "AUX_5V", "GND")

    u2 = b.place("U2", "U2", "UCC27517DBVR", 250, 260)
    b.label_all(u2, {"1": "AUX_5V", "2": "GND", "3": "U2_INP", "4": "U2_INN", "5": "U2_OUT"})
    two("C", "C13", "100nF", 230, 275, "AUX_5V", "GND")
    two("C", "C14", "1uF", 245, 275, "AUX_5V", "GND")
    two("R", "R22", "100", 210, 260, "CROWBAR_PULSE", "U2_INP")
    two("R", "R23", "10k", 210, 245, "U2_INP", "GND")
    two("R", "R24", "10k", 290, 240, "AUX_5V", "U2_INN")

    q6 = b.place("NMOS", "Q6", "2N7002", 215, 220)
    b.label_all(q6, {"1": "ARM_GATE", "2": "GND", "3": "ARM_LINK"})
    two("R", "R25", "100", 190, 220, "DRIVER_ARM", "ARM_GATE")
    two("R", "R26", "10k", 190, 205, "ARM_GATE", "GND")
    two("JP2", "JP2", "ARM link", 235, 220, "ARM_LINK", "U2_INN")

    q1 = b.place("NMOS", "Q1", "AO3400A", 310, 260)
    b.label_all(q1, {"1": "Q1_G", "2": "GND", "3": "GLITCH"})
    two("R", "R27", "2.2", 285, 250, "U2_OUT", "Q1_G")
    two("R", "R28", "10k", 300, 245, "Q1_G", "GND")
    jg = b.place("CONN2", "J1", "GLITCH/GND", 355, 260)
    b.label_all(jg, {"1": "GLITCH", "2": "GND"})

    # ---- Retained mux supply --------------------------------------------------------
    d1 = b.place("D", "D1", "Schottky", 150, 200)
    b.label_all(d1, {"1": "RET_CHG", "2": "AUX_5V"})
    two("R", "R13", "1k", 170, 200, "RET_CHG", "HOLD_IN")
    two("CP", "C9", "100uF", 190, 200, "HOLD_IN", "GND")
    two("C", "C10", "1uF", 205, 200, "HOLD_IN", "GND")
    u6 = b.place("U6", "U6", "TPS7A2036PDBVR", 250, 200)
    b.label_all(u6, {"1": "HOLD_IN", "2": "GND", "3": "HOLD_IN", "4": None, "5": "MUX_VCC"})
    two("C", "C11", "1uF", 280, 200, "MUX_VCC", "GND")
    two("R", "R14", "100k", 295, 200, "MUX_VCC", "GND")

    # ---- Target regulators ----------------------------------------------------------
    u4 = b.place("U4", "U4", "AP2112K-3.3", 170, 150)
    b.label_all(u4, {"1": "AUX_5V", "2": "GND", "3": "EN_HIGH", "4": None, "5": "VHIGH"})
    two("C", "C3", "1uF", 140, 150, "AUX_5V", "GND")
    two("CP", "C4", "100uF", 200, 150, "VHIGH", "GND")
    two("C", "C5", "1uF", 215, 150, "VHIGH", "GND")
    two("R", "R11", "330", 230, 150, "VHIGH", "GND")

    u5 = b.place("U5", "U5", "AP2112K-1.8", 170, 115)
    b.label_all(u5, {"1": "AUX_5V", "2": "GND", "3": "EN_LOW", "4": None, "5": "VLOW"})
    two("C", "C6", "1uF", 140, 115, "AUX_5V", "GND")
    two("CP", "C7", "100uF", 200, 115, "VLOW", "GND")
    two("C", "C8", "1uF", 215, 115, "VLOW", "GND")
    two("R", "R12", "330", 230, 115, "VLOW", "GND")

    # ---- Selector, disconnect and target ------------------------------------------
    two("R", "R15", "15 1% 2W", 260, 170, "VHIGH", "MUX_Y0")
    two("R", "R16", "15 1% 2W", 260, 135, "VLOW", "MUX_Y1")
    u3 = b.place("U3", "U3", "NX3L1T3157GMZ", 300, 150)
    b.label_all(u3, {"1": "MUX_Y1", "2": "GND", "3": "MUX_Y0", "4": "MUX_Z",
                     "5": "MUX_VCC", "6": "MUX_SELECT"})
    two("R", "R36", "100", 280, 115, "MUX_LOW", "MUX_SELECT")
    two("R", "R37", "10k", 300, 115, "MUX_SELECT", "GND")
    two("C", "C12", "100nF", 320, 150, "MUX_VCC", "GND")

    q2 = b.place("PMOS", "Q2", "Si2377EDS", 350, 165)
    b.label_all(q2, {"1": "Q23_G", "2": "Q23_S", "3": "MUX_Z"})
    q3 = b.place("PMOS", "Q3", "Si2377EDS", 350, 135)
    b.label_all(q3, {"1": "Q23_G", "2": "Q23_S", "3": "TARGET_PRE"})
    two("R", "R17", "10k", 370, 150, "Q23_S", "Q23_G")
    q4 = b.place("NMOS", "Q4", "2N7002", 370, 110)
    b.label_all(q4, {"1": "TARGET_ON_G", "2": "GND", "3": "DISCONNECT_DRAIN"})
    two("R", "R38", "100", 350, 110, "DISCONNECT_DRAIN", "Q23_G")
    two("R", "R18", "100", 390, 110, "TARGET_ON", "TARGET_ON_G")
    two("R", "R19", "10k", 405, 110, "TARGET_ON_G", "GND")
    two("R", "R39", "0", 395, 145, "TARGET_PRE", "TARGET_VDD",
        note="Baseline bypass; remove before fitting R20")
    shunt = b.place("SHUNT4", "R20", "0.1 ohm Kelvin", 420, 145,
                    note="DNP measurement option; REMOVE R39; differential probing ONLY", in_bom=False)
    b.label_all(shunt, {"1": "TARGET_PRE", "2": "ISENSE_P", "3": "ISENSE_N", "4": "TARGET_VDD"})
    jt = b.place("CONN2", "J2", "TARGET/GND", 440, 150)
    b.label_all(jt, {"1": "TARGET_VDD", "2": "GND"})
    two("R", "R21", "10k", 455, 135, "TARGET_VDD", "GND")

    # ---- Target-side signals --------------------------------------------------------
    q5 = b.place("NMOS", "Q5", "2N7002", 150, 70)
    b.label_all(q5, {"1": "RESET_G", "2": "GND", "3": "RESET_TARGET"})
    two("R", "R29", "100", 125, 70, "RESET_ASSERT", "RESET_G")
    two("R", "R30", "10k", 140, 55, "RESET_G", "GND")
    two("R", "R31", "10k", 165, 55, "RESET_TARGET", "TARGET_VDD",
        note="DNP for external target supply", in_bom=False)
    jr = b.place("CONN2", "J3", "RESET/GND", 180, 70)
    b.label_all(jr, {"1": "RESET_TARGET", "2": "GND"})

    u7 = b.place("U7", "U7", "SN74LVC1G17", 250, 70)
    b.label_all(u7, {"1": None, "2": "TRIGGER_IN", "3": "GND", "4": "TRIGGER_OUT", "5": "PICO_3V3"})
    two("C", "C16", "100nF", 265, 85, "PICO_3V3", "GND")
    two("R", "R32", "1k", 220, 70, "TRIGGER_RAW", "TRIGGER_IN")
    two("R", "R33", "100k", 235, 55, "TRIGGER_IN", "GND")
    jtr = b.place("CONN2", "J4", "TRIGGER/GND", 200, 45)
    b.label_all(jtr, {"1": "TRIGGER_RAW", "2": "GND"})

    u8 = b.place("U8", "U8", "SN74AXC4T774PWR", 350, 70,
                 note="DNP; symbol pin types reflect hardwired DIR1=1, DIR2/3/4=0, not a general-purpose translator", in_bom=False)
    b.label_all(u8, {
        "1": "PICO_3V3", "2": "GND", "3": "UART_TX", "4": "UART_RX",
        "5": None, "6": None, "7": "GND", "8": "GND",
        "9": "UART_DISABLE", "10": "GND", "11": "GND", "12": "GND",
        "13": "UART_TGT_TX", "14": "UART_TGT_RX", "15": "UART_VCCB",
        "16": "PICO_3V3",
    })
    two("C", "C17", "100nF", 325, 90, "PICO_3V3", "GND")
    two("C", "C18", "100nF", 325, 50, "UART_VCCB", "GND",
        note="DNP optional UART bypass", in_bom=False)
    two("R", "R34", "10k", 370, 90, "UART_DISABLE", "PICO_3V3")
    two("R", "R40", "4.7k", 415, 95, "UART_VCCB", "GND",
        note="DNP UART supply bleeder; does not permit partial-link operation", in_bom=False)
    two("R", "R41", "100k", 415, 45, "UART_TGT_TX", "GND",
        note="DNP UART B2 input default when RX link/cable absent", in_bom=False)
    two("JP2", "JP3", "VCCB link", 390, 90, "TARGET_VDD", "UART_VCCB",
        note="DNP optional", in_bom=False)
    two("JP2", "JP4", "TX link", 390, 70, "UART_TGT_RX", "UART_CONN_RX",
        note="DNP optional", in_bom=False)
    two("JP2", "JP5", "RX link", 390, 50, "UART_TGT_TX", "UART_CONN_TX",
        note="DNP optional", in_bom=False)
    ju = b.place("CONN3", "J5", "UART", 440, 70)
    b.label_all(ju, {"1": "GND", "2": "UART_CONN_RX", "3": "UART_CONN_TX"})

    # ---- Test points and power flags ------------------------------------------------
    for i, (ref, net, y) in enumerate([
        ("TP1", "AUX_5V", 300), ("TP2", "MUX_VCC", 285),
        ("TP3", "VHIGH", 270), ("TP4", "VLOW", 255),
        ("TP5", "TARGET_VDD", 240), ("TP6", "GND", 225),
        ("TP7", "ISENSE_P", 165), ("TP8", "ISENSE_N", 165),
    ], start=1):
        tp = b.place("TP", ref, net, 440, y, in_bom=True)
        b.label_all(tp, {"1": net})

    for i, (net, y) in enumerate([
        ("USB_VBUS", 300), ("AUX_5V", 285), ("HOLD_IN", 270),
        ("TARGET_VDD", 255), ("UART_VCCB", 240), ("GND", 225),
    ], start=1):
        pf = b.place("PWR_FLAG", f"#FLG{i:02d}", "PWR_FLAG", 460, y,
                     in_bom=False, on_board=False, hide_value=True)
        b.label_all(pf, {"1": net})

    # ---- Documentation on the sheet ------------------------------------------------
    b.text(15, 12, "1. Pico 2 / boot defaults", 2.2)
    b.text(150, 12, "2. Target reservoirs (upstream of current limits)", 2.2)
    b.text(300, 12, "3. Voltage selector / slow disconnect", 2.2)
    b.text(150, 108, "4. Retained 3.6 V mux supply", 2.2)
    b.text(15, 177, "5. Reset / 3.3 V trigger", 2.2)
    b.text(150, 177, "6. USB auxiliary branch / separate crowbar", 2.2)
    b.text(150, 263, "7. Optional UART (native DNP)", 2.2)
    b.text(325, 263, "8. Probe pads / ERC flags", 2.2)
    for y, text in [
        (280, "C4 ENGINEERING PROTOTYPE - HARDWARE UNQUALIFIED"),
        (286, "15 ohm in each mux input; <=10 mA total target load."),
        (291, "100 nF: about 5.8 us settling; no settled 100 ns plateau."),
        (296, "GL is separate from TVDD. External supply: unplug TVDD."),
        (301, "No stuck-on timeout. Supervised expendable targets only."),
        (306, "U8/JP3-JP5/C18/R20/R31/R40/R41: DNP. ARM ships OPEN."),
        (311, "VH/VL=3.3/1.8 V reservoirs; MVCC=mux VCC; TVDD=target."),
        (316, "RST_ASSERT=1 asserts reset. Full alias list: hardware/README.md."),
    ]:
        b.text(15, y, text, 1.5)
    b.write()
    print(f"Wrote {OUT / 'cipinkoklingacik.kicad_sch'}")
    print(f"Wrote {OUT / 'cipinkoklingacik.kicad_sym'}")
    print(f"Wrote {OUT / 'sym-lib-table'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
