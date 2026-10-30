#!/usr/bin/env python3
"""Offline JLCPCB quote exports; no upload, order, auto-match or substitution.

Called by export_prototype.py before the manufacturing manifest is sealed.
Coordinates retain the Gerbers' origin (negative Y is intentional); no unverified
feeder rotation offsets are applied. Production placement review is mandatory.
"""
import csv
import json
from pathlib import Path
import re

from kicad_sexpr import loads, children

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "hardware/sourcing/jlcpcb-stock-2026-10-30-r2.json"

# Exact reviewed aliases only; no fuzzy manufacturer or package matching.
MANUFACTURER_ALIASES = {
    "UNI-ROYAL": {"UNI-ROYAL(Uniroyal Elec)"}, "Yageo": {"YAGEO"},
    "Murata": {"Murata Electronics"}, "Panasonic": {"PANASONIC"},
    "Lite-On": {"Lite-On"}, "Littelfuse": {"Littelfuse"},
    "Texas Instruments": {"Texas Instruments"}, "Nexperia": {"Nexperia"},
    "Alpha & Omega Semiconductor": {"Alpha & Omega Semicon"},
    "Diodes Incorporated": {"Diodes Incorporated"}, "NXP": {"NXP Semicon"},
    "Vishay": {"Vishay Intertech"},
}
PACKAGE_ALIASES = {
    "R_0805_2012Metric": {"0805"}, "R_1206_3216Metric": {"1206"},
    "R_2512_6332Metric": {"2512"}, "C_0805_2012Metric": {"0805"},
    "C_1206_3216Metric": {"1206"}, "CP_Elec_6.3x5.8": {"SMD,D6.3xL5.8mm"},
    "LED_0805_2012Metric": {"0805"}, "Fuse_1206_3216Metric": {"1206"},
    "D_SOD-323": {"SOD-323"}, "SOT-23": {"SOT-23"},
    "SOT-23-5": {"SOT-23-5", "SOT-25-5", "SOT-25"}, "SOT-886": {"SOT-886"},
}


def ref_key(ref):
    match = re.fullmatch(r"([A-Z]+)([0-9]+)", ref)
    if not match:
        raise ValueError(f"Invalid designator: {ref}")
    return match[1], int(match[2])


def bom_rows(parts):
    groups = {}
    refs = set()
    for row in parts:
        ref = row["Reference"]
        ref_key(ref)
        if ref in refs:
            raise ValueError(f"Duplicate BOM reference: {ref}")
        refs.add(ref)
        if row["Assembly"] != "SMT" or row["DNP"] != "no":
            raise ValueError(f"Not a fitted SMT part: {ref}")
        if not re.fullmatch(r"C[0-9]+", row.get("LCSC", "")):
            raise ValueError(f"Missing exact LCSC identity: {ref}")
        key = (row["MPN"], row["Manufacturer"], row["Footprint"], row["Value"], row["LCSC"])
        groups.setdefault(key, []).append(ref)
    result = []
    for (mpn, manufacturer, footprint, value, code), designators in groups.items():
        result.append({"Comment": f"{value}; {mpn}",
                       "Designator": ",".join(sorted(designators, key=ref_key)),
                       "Footprint": footprint.split(":", 1)[1],
                       "LCSC Part #": code, "Manufacturer Part Number": mpn,
                       "Manufacturer": manufacturer})
    return sorted(result, key=lambda row: ref_key(row["Designator"].split(",")[0]))


def cpl_rows(parts, positions):
    expected = {row["Reference"] for row in parts}
    if len(expected) != len(parts):
        raise ValueError("Duplicate BOM references")
    if len({row["Ref"] for row in positions}) != len(positions):
        raise ValueError("Duplicate placement references")
    if {row["Ref"] for row in positions} != expected:
        raise ValueError("JLCPCB BOM/CPL population mismatch")
    result = []
    for row in sorted(positions, key=lambda row: ref_key(row["Ref"])):
        if row["Side"] != "top":
            raise ValueError("Only the reviewed top-side baseline is supported")
        result.append({"Designator": row["Ref"], "Mid X": row["PosX"],
                       "Mid Y": row["PosY"], "Layer": "Top",
                       "Rotation": f'{float(row["Rot"]) % 360:.6f}'})
    return result


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def unit_price(item, quantity):
    for tier in item["prices"]:
        if quantity >= tier["startNumber"] and (tier["endNumber"] == -1 or quantity <= tier["endNumber"]):
            return float(tier["productPrice"])
    raise ValueError(f"No price tier for {item['lcsc']} / {quantity}")


def validate_supplier_identity(row, item):
    model = row["Manufacturer Part Number"]
    if item["mpn"].upper() != model.upper() and (model, item["mpn"]) != ("EEE-FK1C101P", "EEEFK1C101P"):
        raise ValueError(f"Snapshot SKU/model mismatch: {model} / {item['lcsc']}")
    if item["manufacturer"] not in MANUFACTURER_ALIASES.get(row["Manufacturer"], set()):
        raise ValueError(f"Snapshot manufacturer mismatch: {model}")
    if item["package"] not in PACKAGE_ALIASES.get(row["Footprint"], set()):
        raise ValueError(f"Snapshot package/footprint mismatch: {model}")


def planning_quantity(build_quantity, terms, catalog_minimum=1):
    """Quantity-only allowance, NOT JLC's minimum-fee/checkout pricing engine.

    Loss is added to the build requirement before taking the minimum, not after.
    Raw leastNumberPrice is disclosed separately; no unverified discount is used.
    """
    if build_quantity <= 0 or min(terms["leastNumber"], terms["lossNumber"], catalog_minimum) < 0:
        raise ValueError("Invalid procurement quantity")
    return max(build_quantity + terms["lossNumber"], terms["leastNumber"], catalog_minimum)


def export(parts, positions, directory):
    bom = bom_rows(parts)
    cpl = cpl_rows(parts, positions)
    snapshot = json.loads(SNAPSHOT.read_text())
    if snapshot["status"] != "active":
        raise ValueError("Cannot export from a historical sourcing snapshot")
    stock = {item["lcsc"]: item for item in snapshot["parts"]}
    terms = snapshot["assembly_terms"]["parts"]
    audit = []
    extended = 0
    for row in bom:
        item = stock[row["LCSC Part #"]]
        model = row["Manufacturer Part Number"]
        validate_supplier_identity(row, item)
        procurement = terms[item["lcsc"]]
        free = item["library_type"] == "base" or item["preferred"]
        extended += not free
        audit.append({"Designator": row["Designator"], "MPN": model,
                       "Manufacturer": row["Manufacturer"], "Supplier_manufacturer": item["manufacturer"],
                       "Footprint": row["Footprint"], "Supplier_package": item["package"],
                      "LCSC": item["lcsc"], "Quantity_per_board": len(row["Designator"].split(",")),
                      "Library_type": "Basic" if item["library_type"] == "base" else "Extended",
                      "Promotional_extended": item["preferred"],
                      "Economic_feeder_fee_USD": "0.00" if free else "3.07",
                      "Stock_at_snapshot": item["stock"],
                       "Catalog_minPurchaseNum": item["min_purchase"],
                       "Assembly_leastNumber": procurement["leastNumber"],
                       "Assembly_lossNumber": procurement["lossNumber"],
                       "API_leastNumberPrice_USD_unverified": procurement["leastNumberPrice"],
                       "Assembly_terms_checked_UTC": snapshot["assembly_terms"]["checked_utc"],
                      "Unit_price_1_USD": unit_price(item, 1),
                      "Checked_UTC": snapshot["checked_utc"],
                      "Warning": "OUT OF STOCK - source exact part or hand-fit before power" if not item["stock"] else
                                 "LOW STOCK - allow for attrition" if item["stock"] < 100 else "Recheck at checkout"})
    board = loads((ROOT / "hardware/cipinkoklingacik.kicad_pcb").read_text())
    selected = {row["Reference"] for row in parts}
    joints = 0
    for fp in children(board, "footprint"):
        props = {p[1]: p[2] for p in children(fp, "property")}
        if props["Reference"] in selected:
            joints += len([p for p in children(fp, "pad") if p[1]])
    estimates = []
    for quantity in (2, 5, 10):
        components = sum(unit_price(stock[row["LCSC"]], quantity * row["Quantity_per_board"])
                         * quantity * row["Quantity_per_board"] for row in audit)
        allowances = {row["LCSC"]: planning_quantity(quantity * row["Quantity_per_board"],
                      terms[row["LCSC"]], stock[row["LCSC"]]["min_purchase"]) for row in audit}
        allowance_cost = sum(q * unit_price(stock[code], q) for code, q in allowances.items())
        fixed = 8.18 + 1.53 + 0.45 + extended * 3.07
        placement = quantity * joints * 0.0016
        estimates.append({"assembled_boards": quantity,
                          "components_USD_excluding_attrition": round(components, 4),
                          "setup_stencil_confirmation_feeders_USD": round(fixed, 4),
                          "smt_joint_charge_USD": round(placement, 4),
                          "subtotal_USD": round(components + fixed + placement, 4),
                           "per_board_USD": round((components + fixed + placement) / quantity, 4),
                           "quantity_allowance_components_USD": round(allowance_cost, 4),
                           "quantity_allowance_subtotal_USD": round(allowance_cost + fixed + placement, 4),
                           "quantity_allowance_per_board_USD": round((allowance_cost + fixed + placement) / quantity, 4),
                           "snapshot_stock_shortfalls_with_quantity_allowance": [code for code, q in allowances.items()
                               if stock[code]["stock"] < q],
                          "additional_pre_reflow_USD_if_applied": round(quantity * joints * 0.016, 4),
                          "snapshot_stock_shortfalls_before_attrition": [row["LCSC"] for row in audit
                              if stock[row["LCSC"]]["stock"] < quantity * row["Quantity_per_board"]]})
    write_csv(directory / "jlcpcb-bom.csv", bom)
    write_csv(directory / "jlcpcb-cpl.csv", cpl)
    write_csv(directory / "jlcpcb-sourcing.csv", audit)
    report = {"purpose": "Budget model, NOT a supplier quote or order approval",
              "snapshot": str(SNAPSHOT.relative_to(ROOT)),
              "baseline_smt_placements": len(parts), "unique_skus": len(bom),
              "smt_solder_joints_per_board": joints, "paid_extended_skus": extended,
              "economic_feeder_total_USD": round(extended * 3.07, 2),
              "excludes": ["PCB fabrication", "shipping, duties, VAT", "component attrition/MOQ/global sourcing",
                           "X-ray for leadless U3", "special process/nitrogen/pre-reflow fees",
                           "Pico, sockets, headers, loose shunt and all hand-fit labor"],
               "assumptions": ["Economic PCBA eligibility is subject to JLCPCB review",
                               "No coupons or unverified feeder rotation offsets",
                               "Exact-quantity subtotals exclude procurement minimum/attrition charges",
                               "Quantity allowance prices max(build + lossNumber, leastNumber, minPurchaseNum) at snapshot tiers; NOT checkout pricing",
                               "leastNumberPrice is retained verbatim; its billing semantics/discounts are not assumed without checkout confirmation",
                               "Minimum charges do not prohibit a two-board assembly order",
                              "Out-of-stock catalog prices are NOT procurement quotes"],
              "estimates": estimates}
    (directory / "jlcpcb-cost-estimate.json").write_text(json.dumps(report, indent=2) + "\n")
