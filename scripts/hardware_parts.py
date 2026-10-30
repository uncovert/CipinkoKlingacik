"""Reviewable C4 component selections (not purchasing approval)."""

from dataclasses import dataclass


# Exact supplier identities, not fuzzy model-name matches. Blank means hand-fit,
# PCB feature or an unmapped DNP option, never permission to auto-substitute.
JLCPCB_CODES = {
    "0805W8F1002T5E": "C17414", "0805W8F1003T5E": "C149504",
    "0805W8F1001T5E": "C17513", "0805W8F1000T5E": "C17408",
    "0805W8F3300T5E": "C17630", "0805W8F220KT5E": "C17521",
    "1206W4F0000T5E": "C17888", "CC0805KRX7R9BB104": "C49678",
    "GRM21BR71C105KA01L": "C77079", "GRM31CR71C106KA12L": "C97954",
    "EEE-FK1C101P": "C128532", "LTST-C170KGKT": "C98221",
    "1206L025YR": "C99561", "UCC27517DBVR": "C99395",
    "2N7002,215": "C65189", "AO3400A": "C20917", "BAT54WS-7-F": "C124205",
    "TPS7A2036PDBVR": "C2873626", "AP2112K-3.3TRG1": "C51118",
    "AP2112K-1.8TRG1": "C176944", "RC2512FK-7W15RL": "C6639259",
    "NX3L1T3157GMZ": "C1870392", "Si2377EDS-T1-GE3": "C143698",
    "SN74LVC1G17DBVR": "C7836",
}


@dataclass(frozen=True)
class Part:
    mpn: str
    manufacturer: str
    footprint: str
    datasheet: str
    requirement: str
    assembly: str = "SMT"

    @property
    def lcsc(self):
        return JLCPCB_CODES.get(self.mpn, "")


def part(mpn, manufacturer, footprint, datasheet, requirement, assembly="SMT"):
    return Part(mpn, manufacturer, "CipinkoKlingacik:" + footprint, datasheet, requirement, assembly)


RESISTORS = {
    "10k": "0805W8F1002T5E", "100k": "0805W8F1003T5E",
    "1k": "0805W8F1001T5E", "100": "0805W8F1000T5E",
    "330": "0805W8F3300T5E", "2.2": "0805W8F220KT5E",
}
CAPACITORS = {
    "100nF": ("CC0805KRX7R9BB104", "C_0805_2012Metric", "100 nF, 50 V, X7R, 10%"),
    "1uF": ("GRM21BR71C105KA01L", "C_0805_2012Metric", "1 uF, 16 V, X7R, 10%; verify >=0.47 uF at bias"),
    "10uF": ("GRM31CR71C106KA12L", "C_1206_3216Metric", "10 uF, 16 V, X7R, 10%; check DC bias"),
}
HEADER = "Connector_PinHeader_2.54mm"
DS = {
    "resistor": "https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L.pdf",
    "uniroyal": "https://www.lcsc.com/datasheet/lcsc_datasheet_2411221126_UNI-ROYAL-Uniroyal-Elec-0805W8F1002T5E_C17414.pdf",
    "yageo_cap": "https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_YAGEO-CC0805KRX7R9BB104_C49678.pdf",
    "murata": "https://www.murata.com/en-us/products/capacitor/mlcc",
    "pico": "https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf",
}
SPECIAL = {
    "U1": part("SC1631", "Raspberry Pi", "RaspberryPi_Pico_Common_THT", DS["pico"],
               "Pico 2 without headers; hand-fit 2x 1x20 sockets and module headers", "Module/hand-fit"),
    "U2": part("UCC27517DBVR", "Texas Instruments", "SOT-23-5", "https://www.ti.com/lit/ds/symlink/ucc27517.pdf", "4.90-5.25 V measured at VDD before arm"),
    "U3": part("NX3L1T3157GMZ", "NXP", "SOT-886", "https://www.nxp.com/docs/en/data-sheet/NX3L1T3157.pdf", "XSON6/SOT886; GMZ ordering code, not obsolete ,115/,132"),
    "U4": part("AP2112K-3.3TRG1", "Diodes Incorporated", "SOT-23-5", "https://www.diodes.com/assets/Datasheets/AP2112.pdf", "3.3 V; verify reservoir startup and stability"),
    "U5": part("AP2112K-1.8TRG1", "Diodes Incorporated", "SOT-23-5", "https://www.diodes.com/assets/Datasheets/AP2112.pdf", "1.8 V; source-only, reservoir/bleeder absorb dip charge"),
    "U6": part("TPS7A2036PDBVR", "Texas Instruments", "SOT-23-5", "https://www.ti.com/lit/ds/symlink/tps7a20.pdf", "3.6 V; IN1 GND2 EN3 NC4 OUT5; EN tied to HOLD_IN, not Pico/AUX5; >=0.47 uF effective output; qualify retention/shutdown"),
    "U7": part("SN74LVC1G17DBVR", "Texas Instruments", "SOT-23-5", "https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf", "3.3 V trigger input only"),
    "U8": part("SN74AXC4T774PWR", "Texas Instruments", "TSSOP-16_4.4x5mm_P0.65mm", "https://www.ti.com/lit/ds/symlink/sn74axc4t774.pdf", "Optional UART; independent DIR pins; OE high disables"),
    "Q1": part("AO3400A", "Alpha & Omega Semiconductor", "SOT-23", "https://aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf", "G1 S2 D3; pulse/thermal qualification required"),
    "D1": part("BAT54WS-7-F", "Diodes Incorporated", "D_SOD-323", "https://www.diodes.com/assets/Datasheets/BAT54WS.pdf", "K1 A2; low-current hold-up charging diode"),
    "D2": part("LTST-C170KGKT", "Lite-On", "LED_0805_2012Metric", "https://optoelectronics.liteon.com/upload/download/DS22-2000-223/LTST-C170KGKT.pdf", "Green LED; K1 A2; software status only"),
    "F1": part("1206L025YR", "Littelfuse", "Fuse_1206_3216Metric", "https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Littelfuse-1206L025YR_C99561.pdf", "250 mA hold, 500 mA trip, 16 V PTC; 100 A fault rating; R1max 2.3 ohm; 80 ms max trip at 8 A, NOT precision limiting; qualify inrush/drop"),
    "R20": part("WSK2512R1000FEA", "Vishay", "R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm", "https://www.vishay.com/docs/30108/wsk2512.pdf", "DNP 0.1 ohm 1% 1 W four-terminal shunt; force1/4, sense2/3; REMOVE R39 when fitted"),
    "R39": part("1206W4F0000T5E", "UNI-ROYAL", "R_1206_3216Metric", "https://www.lcsc.com/datasheet/lcsc_datasheet_2206010200_UNI-ROYAL-Uniroyal-Elec-1206W4F0000T5E_C17888.pdf", "Fitted zero-ohm bypass; REMOVE when R20 fitted; not a removable ARM link"),
    "R40": part("RC0805FR-074K7L", "Yageo", "R_0805_2012Metric", DS["resistor"], "DNP UART option: 4.7k 1% UVCCB bleeder sized for 12uA off-supply source-current budget; change all target links together, power off"),
    "R41": part("RC0805FR-07100KL", "Yageo", "R_0805_2012Metric", DS["resistor"], "DNP UART option: 100k B2 input pull-down; include in target load budget"),
}


def select_part(ref, symbol, value):
    if ref.startswith("#"):
        return None
    if ref in SPECIAL:
        return SPECIAL[ref]
    if ref in ("Q2", "Q3"):
        return part("Si2377EDS-T1-GE3", "Vishay", "SOT-23", "https://www.vishay.com/docs/65905/si2377eds.pdf", "G1 S2 D3; common-source slow disconnect; -1.5 V drive specified")
    if ref in ("Q4", "Q5", "Q6"):
        return part("2N7002,215", "Nexperia", "SOT-23", "https://assets.nexperia.com/documents/data-sheet/2N7002.pdf", "G1 S2 D3")
    if symbol == "R":
        if ref in ("R15", "R16"):
            return part("RC2512FK-7W15RL", "Yageo", "R_2512_6332Metric", "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2312191106_YAGEO-RC2512FK-7W15RL_C6639259.pdf", "15 ohm 1%, 2 W (7W power code); <=0.756 W bounded peak, no pulse-overload credit; qualify >=1 W on actual PCB and derating")
        return part(RESISTORS[value], "UNI-ROYAL", "R_0805_2012Metric", DS["uniroyal"], "1%, 0.125 W; gate pulse rating requires check")
    if symbol == "CP":
        return part("EEE-FK1C101P", "Panasonic", "CP_Elec_6.3x5.8", "https://industrial.panasonic.com/cdbs/www-data/pdf/RDE0000/ABA0000C1181.pdf", "100 uF 16 V +/-20%, positive pad1; leakage max16 uA; reservoir/hold-up qualification")
    if symbol == "C":
        mpn, fp, spec = CAPACITORS[value]
        return part(mpn, "Yageo" if value == "100nF" else "Murata", fp,
                    DS["yageo_cap"] if value == "100nF" else DS["murata"], spec)
    if symbol in ("CONN2", "CONN3", "JP2"):
        n = 3 if symbol == "CONN3" else 2
        return part(f"TSW-10{n}-07-G-S", "Samtec", f"PinHeader_1x0{n}_P2.54mm_Vertical", "https://suddendocs.samtec.com/catalog_english/tsw.pdf", "2.54 mm header; pin1 marked; hand-fit; removable shunts separate", "THT/hand-fit")
    if symbol == "TP":
        return part("PCB_PAD", "PCB", "TestPoint_Pad_D1.5mm", "", "Bare copper probe pad; no purchased component", "PCB feature")
    raise ValueError(f"No component selection for {ref}: {symbol}/{value}")


# Standard KiCad footprints are snapshotted locally for repeatable pad matching.
FOOTPRINT_SOURCES = {
    "SOT-23": "Package_TO_SOT_SMD", "SOT-23-5": "Package_TO_SOT_SMD",
    "SOT-886": "Package_TO_SOT_SMD", "D_SOD-323": "Diode_SMD",
    "TSSOP-16_4.4x5mm_P0.65mm": "Package_SO", "RaspberryPi_Pico_Common_THT": "Module",
    "R_0805_2012Metric": "Resistor_SMD", "R_2512_6332Metric": "Resistor_SMD",
    "C_0805_2012Metric": "Capacitor_SMD", "C_1206_3216Metric": "Capacitor_SMD",
    "CP_Elec_6.3x5.8": "Capacitor_SMD", "LED_0805_2012Metric": "LED_SMD",
    "Fuse_1206_3216Metric": "Fuse", "TestPoint_Pad_D1.5mm": "TestPoint",
    "PinHeader_1x02_P2.54mm_Vertical": HEADER,
    "PinHeader_1x03_P2.54mm_Vertical": HEADER,
    "R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm": "Resistor_SMD",
    "R_1206_3216Metric": "Resistor_SMD",
    "MountingHole_2.7mm_M2.5": "MountingHole",
}
