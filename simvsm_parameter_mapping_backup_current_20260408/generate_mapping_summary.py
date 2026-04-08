"""
generate_mapping_summary.py
-----------------------------
Generates mapping_summary.csv from the latest semantic_mapping_*.json in a given
output folder.  Can be run standalone or imported and called programmatically by
the pipeline.

Standalone usage:
    python generate_mapping_summary.py                          # uses Pipeline_Results/
    python generate_mapping_summary.py --output "some/folder"

Columns written:
  Source Node, Normalized Name, Target Node, Target Parent Path,
  Confidence, Overall Score, Unit Compat, Type Compat, Lexical Sim,
  Semantic Sim, Match Type
"""

import argparse
import csv
import glob
import json
import os

FIELDNAMES = [
    'Source Node', 'Normalized Name', 'Target Node', 'Target Parent Path',
    'Confidence', 'Overall Score',
    'Unit Compat', 'Type Compat', 'Lexical Sim', 'Semantic Sim',
    'Match Type',
]


def _build_target_parent_lookup(target_csv: str) -> dict:
    """Return {node_name: parent_path_string} from target_nodes.csv."""
    lookup = {}
    if not os.path.isfile(target_csv):
        return lookup
    with open(target_csv, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            name = row.get('Name', '').strip()
            if name in lookup:
                continue  # keep first occurrence
            pp = row.get('Parent Path', '').strip()
            if not pp:
                concept = row.get('Conceptual definition', '')
                if ' > ' in concept:
                    pp = concept.split(' | ')[0].strip()
                else:
                    pp = row.get('Source description', '').strip() or ''
            lookup[name] = pp
    return lookup


def _build_source_name_lookup(source_csv: str) -> dict:
    """Return {raw_name: normalised_name} from source_nodes.csv."""
    lookup = {}
    if not os.path.isfile(source_csv):
        return lookup
    with open(source_csv, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            n = row.get('Name', '').strip()
            normalized = (row.get('Normalized Name') or '').strip()
            lookup[n] = normalized or n
    return lookup


def generate(output_folder: str, verbose: bool = True) -> str:
    """
    Generate mapping_summary.csv inside *output_folder*.

    Picks the latest semantic_mapping_*.json found in that folder
    (falls back to semantic_mapping_resumed_*.json for legacy runs).

    Returns the path of the written CSV.
    """
    # ── find latest mapping JSON ─────────────────────────────────────────────
    patterns = [
        os.path.join(output_folder, 'semantic_mapping_*.json'),
        os.path.join(output_folder, 'semantic_mapping_resumed_*.json'),
    ]
    json_files = []
    for pat in patterns:
        json_files.extend(glob.glob(pat))
    # de-duplicate and sort newest-last (by name — timestamp embedded)
    json_files = sorted(set(json_files))
    if not json_files:
        raise FileNotFoundError(
            f'No semantic_mapping_*.json found in: {output_folder}'
        )
    latest_json = json_files[-1]
    if verbose:
        print(f'  [mapping_summary] Using: {os.path.basename(latest_json)}')

    with open(latest_json, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)

    # ── side-car CSVs ────────────────────────────────────────────────────────
    source_csv = os.path.join(output_folder, 'source_nodes.csv')
    target_csv = os.path.join(output_folder, 'target_nodes.csv')
    normalised   = _build_source_name_lookup(source_csv)
    target_parents = _build_target_parent_lookup(target_csv)

    # ── build rows ───────────────────────────────────────────────────────────
    rows = []
    for m in mapping_data.get('matches', []):
        src  = m.get('source_name', '')
        tgt  = m.get('target_name', '')
        comp = m.get('details', {}).get('component_scores', {})
        rows.append({
            'Source Node':        src,
            'Normalized Name':    normalised.get(src, src),
            'Target Node':        tgt,
            'Target Parent Path': target_parents.get(tgt, ''),
            'Confidence':         m.get('confidence', ''),
            'Overall Score':      round(float(m.get('score', 0)), 4),
            'Unit Compat':        round(float(comp.get('unit_compatibility', 0)), 4),
            'Type Compat':        round(float(comp.get('type_compatibility', 0)), 4),
            'Lexical Sim':        round(float(comp.get('lexical_similarity', 0)), 4),
            'Semantic Sim':       round(float(comp.get('semantic_similarity', 0)), 4),
            'Match Type':         m.get('match_type', ''),
        })

    # ── append explicit no_match rows for unmatched sources ───────────────────
    # This ensures mapping_summary.csv has one row per source node (matched + no_match),
    # which is useful for thesis evaluation and downstream CSV-based analyses.
    for u in mapping_data.get('unmatched_source', []) or []:
        # Current semantic_mapping JSON stores objects like {"name": "...", ...}
        if isinstance(u, dict):
            src = (u.get('name') or '').strip()
        else:
            src = str(u).strip()
        if not src:
            continue
        rows.append({
            'Source Node':        src,
            'Normalized Name':    normalised.get(src, src),
            'Target Node':        '',
            'Target Parent Path': '',
            'Confidence':         'no_match',
            'Overall Score':      0.0,
            'Unit Compat':        0.0,
            'Type Compat':        0.0,
            'Lexical Sim':        0.0,
            'Semantic Sim':       0.0,
            'Match Type':         'no_match',
        })

    # ── write CSV ────────────────────────────────────────────────────────────
    out_path = os.path.join(output_folder, 'mapping_summary.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    if verbose:
        # Windows cp1252 terminals may not support the unicode arrow.
        print(f'  [mapping_summary] Written {len(rows)} rows -> {out_path}')
    return out_path


# ── CLI entry-point ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate mapping_summary.csv from the latest semantic mapping JSON.'
    )
    parser.add_argument(
        '--output', default='Pipeline_Results',
        help='Output folder that contains semantic_mapping_*.json and *_nodes.csv'
    )
    args = parser.parse_args()
    generate(args.output)
