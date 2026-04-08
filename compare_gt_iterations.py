"""Compare Pipeline_Results/*/mapping_summary.csv (or semantic_mapping JSON) to ground-truth pairs."""
import csv
import difflib
import glob
import json
import os
import sys

BASE = os.path.join(os.path.dirname(__file__), "Pipeline_Results")

GROUND_TRUTH = {
    "mfr_name": "ManufacturerName",
    "prod_des": "ManufacturerProductDesignation",
    "serial_no": "SerialNumber",
    "yr_built": "YearOfConstruction",
    "origin_ctry": "CountryOfOrigin",
    "cnt_name": "Name",
    "cnt_role": "RoleOfContactPerson",
    "cnt_phone": "Phone",
    "cnt_mail": "EmailAddress",
    "cnt_city": "CityTown",
    "dim_len": "VehicleLength",
    "dim_wid": "VehicleWidth",
    "pld_max": "PayloadCapacity",
    "ip_class": "IngressProtection",
    "doc_id": "DocumentId",
    "doc_rev": "DocumentVersion",
    "doc_lang": "Language",
    "mime_typ": "MimeType",
    "doc_url": "DocumentURL",
    "ts_id": "TimeSeriesId",
    "tm_stmp": "TimeStamp",
    "smp_rate": "SamplingRate",
    "tz_off": "TimeZone",
    "pcf_val": "ProductCarbonFootprint",
    "pcf_mth": "PcfCalculationMethod",
    "ref_qty": "ReferenceUnit",
    "gwp100": "GlobalWarmingPotential",
    "ghg_scp": "GHGScope",
    "srv_typ": "ServiceType",
    "err_cd": "ErrorCode",
    "req_dt": "RequestDate",
    "urg_lvl": "Urgency",
    "cnt_eml": "ContactEmail",
    "assy_id": "AssemblyIdentifier",
    "part_id": "PartIdentifier",
    "qty_req": "Quantity",
    "child_id": "ChildIdentifier",
    "assy_lvl": "AssemblyLevel",
    "cad_fil": "File",
    "bbx_x": "BoundingBoxX",
    "bbx_y": "BoundingBoxY",
    "bbx_z": "BoundingBoxZ",
    "fmt_3d": "Format",
    "ep_url": "EndpointURL",
    "if_name": "InterfaceName",
    "aut_typ": "AuthenticationType",
    "mth_typ": "MethodType",
    "ctrl_typ": "ControllerType",
    "ctrl_mfr": "Manufacturer",
    "ctrl_id": "Identifier",
    "inst_loc": "Location",
    "sw_name": "SoftwareName",
    "sw_ver": "SoftwareVersion",
    "os_req": "OperatingSystem",
    "lic_mod": "LicenseModel",
    "sim_id": "SimulationModelId",
    "sim_typ": "SimulationType",
    "sim_fmt": "Format",
    "sim_url": "ModelURL",
    "sim_rev": "Revision",
    "sil_lvl": "SIL",
    "pl_lvl": "PL",
    "proof_iv": "ProofTestInterval",
    "mtbf_val": "MTBF",
    "mttr_val": "MTTR",
    "fail_rt": "FailureRate",
    "lte_bnd": "FrequencyBand",
    "mac_adr": "MACAddress",
    "pam_id": "PAMIdentifier",
    "life_ph": "LifeCyclePhase",
    "ax_cnt": "AxisCount",
    "spnd_mx": "SpindleSpeed",
    "tl_cap": "ToolCapacity",
    "cnc_typ": "MachineType",
    "wk_day": "WorkingDays",
    "cal_ref": "CalendarReference",
    "hol_exc": "HolidayException",
}


def load_mapping_summary(folder: str) -> dict | None:
    path = os.path.join(folder, "mapping_summary.csv")
    if not os.path.isfile(path):
        return None
    pred = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            s = (row.get("Source Node") or "").strip()
            t = (row.get("Target Node") or "").strip()
            if s:
                pred[s] = t
    return pred


def load_semantic_json(folder: str) -> dict | None:
    pats = glob.glob(os.path.join(folder, "semantic_mapping_*.json"))
    if not pats:
        return None
    latest = max(pats, key=os.path.getmtime)
    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)
    pred = {}
    for m in data.get("matches", []):
        s = (m.get("source_name") or "").strip()
        t = (m.get("target_name") or "").strip()
        if s:
            pred[s] = t
    return pred


def _norm(s: str) -> str:
    return (s or "").strip().casefold()


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def approximately_matches(expected: str, predicted: str, min_ratio: float = 0.82) -> bool:
    """
    True if predicted is 'close enough' to expected (not only exact string).
    Rules: exact; case-insensitive; high string similarity; plural/singular;
    one contains the other when the shorter is at least 4 chars (handles DocumentId vs DocumentIds).
    """
    e = (expected or "").strip()
    g = (predicted or "").strip()
    if not e or not g:
        return False
    if e == g:
        return True
    if _norm(e) == _norm(g):
        return True
    # Plural / singular (simple trailing s)
    if _norm(e + "s") == _norm(g) or _norm(e) == _norm(g + "s"):
        return True
    if _norm(e).endswith("s") and _norm(e[:-1]) == _norm(g):
        return True
    if _norm(g).endswith("s") and _norm(g[:-1]) == _norm(e):
        return True
    r = _ratio(_norm(e), _norm(g))
    if r >= min_ratio:
        return True
    # Substring (e.g. Endpoint vs EndpointURL, Name vs InterfaceName)
    ne, ng = _norm(e), _norm(g)
    shorter, longer = (ne, ng) if len(ne) <= len(ng) else (ng, ne)
    if len(shorter) >= 4 and shorter in longer:
        return True
    return False


def evaluate(pred: dict) -> dict:
    correct = 0
    wrong = []
    missing = []
    for src, exp in GROUND_TRUTH.items():
        got = pred.get(src)
        if got is None:
            missing.append(src)
        elif got == exp:
            correct += 1
        else:
            wrong.append((src, exp, got))
    n = len(GROUND_TRUTH)
    return {
        "accuracy": correct / n if n else 0.0,
        "correct": correct,
        "total_gt": n,
        "wrong": wrong,
        "missing": missing,
    }


def evaluate_approx(pred: dict, min_ratio: float = 0.82) -> dict:
    """Same as evaluate but counts approximate matches (see approximately_matches)."""
    ok = 0
    wrong = []
    missing = []
    for src, exp in GROUND_TRUTH.items():
        got = pred.get(src)
        if got is None:
            missing.append(src)
        elif approximately_matches(exp, got, min_ratio=min_ratio):
            ok += 1
        else:
            wrong.append((src, exp, got))
    n = len(GROUND_TRUTH)
    return {
        "accuracy": ok / n if n else 0.0,
        "correct": ok,
        "total_gt": n,
        "wrong": wrong,
        "missing": missing,
    }


def main() -> None:
    base = BASE
    if len(sys.argv) > 1:
        base = sys.argv[1]

    rows = []
    for name in sorted(os.listdir(base), key=lambda x: (not str(x).isdigit(), int(x) if str(x).isdigit() else 0)):
        folder = os.path.join(base, name)
        if not os.path.isdir(folder):
            continue
        pred = load_mapping_summary(folder)
        src = "mapping_summary.csv"
        if pred is None:
            pred = load_semantic_json(folder)
            src = "semantic_mapping_*.json"
        if pred is None:
            rows.append((name, None, None, 0, 0, "—", src))
            continue
        r_ex = evaluate(pred)
        r_ap = evaluate_approx(pred)
        rows.append(
            (
                name,
                r_ex["accuracy"],
                r_ap["accuracy"],
                r_ex["correct"],
                r_ap["correct"],
                r_ex["total_gt"],
                f"{r_ex['correct']}/{r_ex['total_gt']}",
                f"{r_ap['correct']}/{r_ap['total_gt']}",
                src,
            )
        )

    valid = [x for x in rows if x[1] is not None]
    valid_by_exact = sorted(valid, key=lambda x: (-x[1], -x[3], str(x[0])))
    valid_by_approx = sorted(valid, key=lambda x: (-x[2], -x[4], str(x[0])))

    print(f"Ground-truth pairs: {len(GROUND_TRUTH)}")
    print(f"Base folder: {os.path.abspath(base)}\n")
    print(
        "Approximate = case-insensitive, fuzzy ratio >= 0.82, plural/s, or substring (>=4 chars).\n"
    )
    print(f"{'Iter':<8} {'Exact%':>9} {'Approx%':>9} {'Exact':>10} {'Approx':>10}  Source")
    print("-" * 68)
    for row in sorted(valid, key=lambda x: (-x[2], str(x[0]))):
        name, ex_acc, ap_acc, _, _, tot, ex_lbl, ap_lbl, src = row
        print(
            f"{str(name):<8} {ex_acc*100:8.2f}% {ap_acc*100:8.2f}% "
            f"{ex_lbl:>10} {ap_lbl:>10}  {src}"
        )

    skipped = [x for x in rows if x[1] is None]
    if skipped:
        print("\nNo mapping_summary / semantic_mapping:")
        for x in skipped:
            print(f"  {x[0]}")

    if valid_by_exact:
        b1, ex1, ap1, _, _, _, _, _, _ = valid_by_exact[0]
        b2, ex2, ap2, _, _, _, _, _, _ = valid_by_approx[0]
        print(f"\nBest by EXACT match: folder **{b1}**  ({ex1*100:.2f}%)")
        print(f"Best by APPROX match: folder **{b2}**  ({ap2*100:.2f}%)")
        if b1 != b2:
            print("(Ranking can differ between exact and approximate.)")

        folder = os.path.join(base, valid_by_approx[0][0])
        pred = load_mapping_summary(folder) or load_semantic_json(folder)
        r = evaluate_approx(pred)
        print(f"\nStill not approx-match after fuzzy rules: {len(r['wrong'])}  |  Missing: {len(r['missing'])}")
        if r["wrong"][:20]:
            print("  Examples (source -> expected, got):")
            for w in r["wrong"][:20]:
                print(f"    {w[0]} -> expected {w[1]}, got {w[2]!r}")


if __name__ == "__main__":
    main()
