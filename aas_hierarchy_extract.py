#!/usr/bin/env python3
"""
AAS (Asset Administration Shell) Hierarchy Extractor

Extracts the complete hierarchical tree of all Submodels, SubmodelElementCollections (SMC),
and SubmodelElementLists (SML). For lists, expands the first instance fully.

Output per element:
  - Parent Path: full breadcrumb (e.g. Submodel > SMC > List)
  - idShort: short identifier
  - ModelType: e.g. Property, SMC, SML, MLP, Submodel
  - SemanticID: IRI reference
  - Value / ValueType: for Properties/MLP (e.g. xs:string)

Output: CSV table + nested JSON (no summarization; first list instance expanded fully).

Usage:
  python aas_hierarchy_extract.py "Data/AAS Data/IDTA 02031-1_Template_ProcessParameters_Type_forAASMetamodelV3.1.json"
  python aas_hierarchy_extract.py <path> --output-dir output
"""

import argparse
import json
import os
import csv
from typing import Dict, List, Tuple


def get_semantic_id(obj: Dict) -> str:
    """Extract SemanticID IRI from semanticId (AAS 3.0) or semanticID (AAS 2.0)."""
    sid = obj.get("semanticId") or obj.get("semanticID")
    if not sid:
        return ""
    keys = sid.get("keys") or sid.get("key") or []
    if isinstance(keys, list) and keys:
        first = keys[0]
        return (first.get("value") or first.get("name") or "").strip()
    return ""


def get_model_type(obj: Dict) -> str:
    """Get modelType (AAS 3.0)."""
    return (obj.get("modelType") or "").strip()


def get_english_description(description_list: List[Dict]) -> str:
    """Extract English description from AAS description array ([{\"language\": \"en\", \"text\": \"...\"}, ...])."""
    if not description_list or not isinstance(description_list, list):
        return ""
    for d in description_list:
        if isinstance(d, dict) and (d.get("language") or "").strip().lower() in ("en", "en-us", "en_us"):
            t = (d.get("text") or "").strip()
            if t:
                return t
    if description_list and isinstance(description_list[0], dict):
        return (description_list[0].get("text") or "").strip()
    return ""


def get_value_and_type(obj: Dict) -> Tuple[str, str]:
    """Get value and valueType for Property/MLP only. SMC/SML have value=child elements; do not use as Value."""
    mt = get_model_type(obj)
    if mt in ("SubmodelElementCollection", "SubmodelElementList", "Submodel"):
        return "", ""
    value_type = (obj.get("valueType") or "").strip()
    val = obj.get("value")
    if val is None:
        return "", value_type
    if isinstance(val, list):
        for item in val:
            if isinstance(item, dict) and item.get("language") == "en":
                return (item.get("text") or "").strip(), value_type or "langString"
        if val and isinstance(val[0], dict) and "language" in (val[0] or {}):
            return (val[0].get("text") or "").strip(), value_type or "langString"
        return "", value_type
    return str(val).strip()[:500], value_type


def is_smc_or_sml(obj: Dict) -> bool:
    mt = get_model_type(obj)
    return mt in ("SubmodelElementCollection", "SubmodelElementList")


def get_children(obj: Dict, expand_first_only: bool) -> List[Dict]:
    """
    Get child elements for SMC/SML. For SML, if expand_first_only=True return only first item.
    """
    val = obj.get("value")
    if not isinstance(val, list):
        return []
    # Filter to actual submodel elements (have idShort or modelType)
    children = [x for x in val if isinstance(x, dict) and (x.get("idShort") is not None or x.get("modelType"))]
    if not children:
        return []
    if expand_first_only and get_model_type(obj) == "SubmodelElementList":
        return children[:1]
    return children


def walk(
    parent_path: str,
    obj: Dict,
    rows: List[Dict],
    expand_first_only: bool = True,
) -> Dict:
    """
    Recursively walk AAS structure. Append flat row to rows; return nested node for JSON.
    """
    id_short = (obj.get("idShort") or "").strip()
    model_type = get_model_type(obj)
    semantic_id = get_semantic_id(obj)
    value_str, value_type = get_value_and_type(obj)
    description = get_english_description(obj.get("description") or [])

    row = {
        "Parent Path": parent_path,
        "idShort": id_short,
        "ModelType": model_type,
        "SemanticID": semantic_id,
        "Value": value_str,
        "ValueType": value_type,
        "Description": description,
    }
    rows.append(row)

    node: Dict = {
        "Parent Path": parent_path,
        "idShort": id_short,
        "ModelType": model_type,
        "SemanticID": semantic_id,
    }
    if model_type not in ("SubmodelElementCollection", "SubmodelElementList", "Submodel") and (value_type or value_str):
        node["Value"] = value_str
        node["ValueType"] = value_type

    if is_smc_or_sml(obj):
        children = get_children(obj, expand_first_only=expand_first_only)
        path = f"{parent_path} > {model_type}" if parent_path else model_type
        if id_short:
            path = f"{parent_path} > {id_short}" if parent_path else id_short
        child_nodes = []
        for ch in children:
            child_nodes.append(walk(path, ch, rows, expand_first_only))
        if child_nodes:
            node["children"] = child_nodes

    return node


def extract_from_submodel(submodel: Dict, expand_first_only: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """Extract from one submodel. Returns (flat_rows, nested_nodes)."""
    rows: List[Dict] = []
    id_short = (submodel.get("idShort") or "").strip()
    model_type = get_model_type(submodel) or "Submodel"
    semantic_id = get_semantic_id(submodel)
    rows.append({
        "Parent Path": "",
        "idShort": id_short,
        "ModelType": model_type,
        "SemanticID": semantic_id,
        "Value": "",
        "ValueType": "",
        "Description": get_english_description(submodel.get("description") or []),
    })
    root_node: Dict = {
        "Parent Path": "",
        "idShort": id_short,
        "ModelType": model_type,
        "SemanticID": semantic_id,
        "children": [],
    }
    path = f"Submodel > {id_short}" if id_short else "Submodel"
    for elem in submodel.get("submodelElements") or []:
        if not isinstance(elem, dict):
            continue
        root_node["children"].append(walk(path, elem, rows, expand_first_only))
    return rows, [root_node]


def extract_from_json(data: Dict, expand_first_only: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """Extract hierarchy from AAS JSON. Returns (flat_rows, nested_structure)."""
    all_rows: List[Dict] = []
    all_nested: List[Dict] = []
    submodels = data.get("submodels") or []
    for sm in submodels:
        if not isinstance(sm, dict):
            continue
        rows, nested = extract_from_submodel(sm, expand_first_only=expand_first_only)
        all_rows.extend(rows)
        all_nested.extend(nested)
    return all_rows, all_nested


def load_hierarchy_csv_to_collection(csv_path: str):
    """
    Load an AAS hierarchy CSV (as produced by this script) into a SemanticNodeCollection.
    Every row becomes a matchable node so that mapping can match source nodes to either
    container elements (e.g. PlannedSkillDemand, SubmodelElementList) or leaf parameters
    (e.g. ProcessTime, Property). Do not skip any row.
    """
    try:
        from semantic_node_enhanced import SemanticNode, SemanticNodeCollection
    except ImportError:
        raise ImportError("semantic_node_enhanced is required for load_hierarchy_csv_to_collection")
    collection = SemanticNodeCollection()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parent = (row.get("Parent Path") or "").strip()
            id_short = (row.get("idShort") or "").strip()
            model_type = (row.get("ModelType") or "").strip()
            semantic_id = (row.get("SemanticID") or "").strip()
            value = (row.get("Value") or "").strip()
            value_type = (row.get("ValueType") or "").strip()
            if not parent and not id_short and not model_type:
                continue  # skip fully empty rows
            name = id_short if id_short else (parent.split(" > ")[-1] if parent else "Unnamed")
            if not name:
                name = "Unnamed"
            # Use description from file (CSV column) when present
            conceptual = (row.get("Description") or "").strip()
            if not conceptual:
                conceptual = f"{parent} | {model_type}" if parent else model_type
                if semantic_id:
                    conceptual = f"{conceptual} | {semantic_id}"
            node = SemanticNode(
                name=name,
                conceptual_definition=conceptual,
                value=value,
                value_type=value_type or "String",
                unit="",
                source_description=parent,
                source_file=os.path.basename(csv_path),
                metadata={"parent_path": parent, "model_type": model_type, "semantic_id": semantic_id},
            )
            collection.add_node(node)
    return collection


def main():
    parser = argparse.ArgumentParser(description="Extract AAS hierarchy (Submodels, SMC, SML) to table and JSON.")
    parser.add_argument("input_json", help="Path to AAS JSON file")
    parser.add_argument("--output-dir", default=".", help="Output directory for CSV and JSON")
    parser.add_argument("--expand-all-items", action="store_true", help="Expand all list items (default: first only)")
    args = parser.parse_args()

    path = args.input_json
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}")
        return 1

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    expand_first_only = not args.expand_all_items
    rows, nested = extract_from_json(data, expand_first_only=expand_first_only)

    base = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(args.output_dir, exist_ok=True)
    csv_path = os.path.join(args.output_dir, f"{base}_aas_hierarchy.csv")
    json_path = os.path.join(args.output_dir, f"{base}_aas_hierarchy.json")

    fieldnames = ["Parent Path", "idShort", "ModelType", "SemanticID", "Value", "ValueType", "Description"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"submodels": nested, "flatRowCount": len(rows)}, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(rows)} elements")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    return 0


if __name__ == "__main__":
    exit(main())
