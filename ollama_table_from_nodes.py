#!/usr/bin/env python3
"""
Ollama Table Generator: Extract nodes + support documents → Ollama → full table (CSV).

Loads:
  1. Extracted semantic nodes (from CSV or from datamap extraction)
  2. Support documents (from support_files/ or Data/support_files/)

Sends each node together with support document text to Ollama and asks for:
  Name, Conceptual definition, Usage of data, Value, Value type, Unit, Source description.

Writes a single CSV table with all columns filled from Ollama (or kept from extraction).
"""

import argparse
import csv
import os
import re
import sys

# Optional: use datamap for extraction if nodes CSV not provided
try:
    import datamap
except ImportError:
    datamap = None

# Ollama API
try:
    import requests
except ImportError:
    requests = None

# Default column set for output table
TABLE_COLUMNS = [
    "Name",
    "Conceptual definition",
    "Usage of data",
    "Value",
    "Value type",
    "Unit",
    "Source description",
]

# Max support-doc chars to send per node (to stay within context)
MAX_SUPPORT_CHARS = 12000

# Response block separator and field pattern for parsing Ollama output
BLOCK_SEP = "---"
FIELD_PATTERN = re.compile(
    r"^(Name|Conceptual definition|Usage of data|Value|Value type|Unit|Source description)\s*:\s*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)


def load_support_documents(support_folder: str) -> str:
    """Load all text from support folder and return one string. Tries common paths."""
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        support_folder,
        os.path.join(base, support_folder),
        os.path.join(base, "Data", support_folder),
        os.path.join(base, "data", support_folder),
    ]
    chosen = None
    for path in candidates:
        if os.path.isdir(path):
            chosen = path
            break
    if not chosen:
        return ""

    parts = []
    total = 0
    for name in sorted(os.listdir(chosen)):
        path = os.path.join(chosen, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in (".txt", ".text", ".md", ".markdown"):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            elif ext in (".html", ".htm"):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                text = re.sub(r"<[^>]+>", " ", raw)
                text = re.sub(r"\s+", " ", text).strip()
            else:
                continue
        except Exception:
            continue
        if text:
            parts.append(f"[Document: {name}]\n{text}")
            total += len(text)
            if total >= MAX_SUPPORT_CHARS * 2:
                break
    out = "\n\n".join(parts)
    if len(out) > MAX_SUPPORT_CHARS:
        out = out[:MAX_SUPPORT_CHARS] + "\n... [truncated]"
    return out


def load_nodes_from_csv(csv_path: str) -> list[dict]:
    """Load semantic nodes from a CSV with standard columns."""
    rows = []
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = {}
            for k, v in row.items():
                key = k.strip()
                val = v.strip() if isinstance(v, str) else v
                r[key] = val
            # Normalize column names
            if "Usage of data (Affordance)" in r and "Usage of data" not in r:
                r["Usage of data"] = r.get("Usage of data (Affordance)", "")
            rows.append(r)
    return rows


def load_nodes_from_extraction(data_folder: str) -> list[dict]:
    """Run datamap extractor and return list of node dicts (with TABLE_COLUMNS keys)."""
    if not datamap:
        raise RuntimeError("datamap not available; install or run from project root")
    extractor = datamap.SemanticNodeExtractor(data_folder=data_folder)
    extractor.process_all_files()
    out = []
    for n in extractor.semantic_nodes:
        row = {col: (n.get(col) or "") for col in TABLE_COLUMNS}
        out.append(row)
    return out


def build_prompt(node: dict, support_text: str) -> str:
    """Build the prompt for Ollama: node info + support docs + instruction for table row."""
    name = node.get("Name", "")
    value = node.get("Value", "")
    value_type = node.get("Value type", "")
    unit = node.get("Unit", "")
    conceptual = (node.get("Conceptual definition") or "").strip()
    usage = (node.get("Usage of data") or "").strip()
    source_desc = (node.get("Source description") or "").strip()

    prompt_parts = [
        "You are filling a single row of a semantic node table. Use the CURRENT NODE below and the SUPPORT DOCUMENTS to produce one complete row.",
        "",
        "CURRENT NODE:",
        f"  Name: {name}",
        f"  Value: {value or '(none)'}",
        f"  Value type: {value_type or '(unknown)'}",
        f"  Unit: {unit or '(none)'}",
        f"  Conceptual definition (if any): {conceptual or '(none)'}",
        f"  Usage of data (if any): {usage or '(none)'}",
        f"  Source description (if any): {source_desc or '(none)'}",
        "",
    ]
    if support_text:
        prompt_parts.append("SUPPORT DOCUMENTS (use these to improve definitions and usage):")
        prompt_parts.append(support_text[:MAX_SUPPORT_CHARS])
        prompt_parts.append("")
    prompt_parts.extend([
        "Output exactly one block with these 7 fields. Use the exact labels. Keep values on one line each.",
        "Format:",
        BLOCK_SEP,
        "Name: <same or clarified name>",
        "Conceptual definition: <1-3 sentences>",
        "Usage of data: <1-2 sentences>",
        "Value: <from node or N/A>",
        "Value type: <e.g. String, Number, Boolean, time, enum>",
        "Unit: <e.g. %, time, mm, NONE>",
        "Source description: <short context or source>",
        BLOCK_SEP,
        "",
        "Your response (only the block between the two ---):",
    ])
    return "\n".join(prompt_parts)


def parse_ollama_block(text: str) -> dict | None:
    """Parse a single --- ... --- block into a row dict with TABLE_COLUMNS keys."""
    text = (text or "").strip()
    if not text:
        return None
    row = {col: "" for col in TABLE_COLUMNS}
    for m in FIELD_PATTERN.finditer(text):
        key = m.group(1)
        val = (m.group(2) or "").strip()
        for col in TABLE_COLUMNS:
            if col.lower() == key.lower():
                row[col] = val
                break
    return row if any(row.values()) else None


def call_ollama(prompt: str, model: str, url: str, timeout: int = 90) -> str:
    """Send prompt to Ollama and return the response text."""
    if not requests:
        raise RuntimeError("requests is required; pip install requests")
    resp = requests.post(
        f"{url.rstrip('/')}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9, "num_predict": 800},
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama returned {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    return (data.get("response") or data.get("text") or "").strip()


def extract_block_from_response(response: str) -> str:
    """Get the first --- ... --- block from the model response."""
    if BLOCK_SEP not in response:
        return response.strip()
    parts = response.split(BLOCK_SEP)
    if len(parts) >= 2:
        return parts[1].strip()
    return response.strip()


def collection_to_node_dicts(collection) -> list[dict]:
    """Convert a SemanticNodeCollection to list of node dicts with TABLE_COLUMNS keys."""
    try:
        nodes = list(collection.nodes)
    except AttributeError:
        nodes = list(collection)
    out = []
    for node in nodes:
        d = getattr(node, "to_dict", None)
        if d:
            row = d()
            r = {}
            for col in TABLE_COLUMNS:
                val = row.get(col)
                if col == "Usage of data" and not val:
                    val = row.get("Usage of data (Affordance)")
                r[col] = val or ""
            out.append(r)
        else:
            out.append({col: (node.get(col) or "") for col in TABLE_COLUMNS})
    return out


def run_ollama_table(
    nodes: list[dict],
    support_folder: str,
    model: str = None,
    ollama_url: str = None,
    limit: int = 0,
) -> list[dict]:
    """
    Run Ollama table generation on a list of node dicts. Usable from the integrated pipeline.
    
    Args:
        nodes: List of dicts with at least Name (and optionally Value, Value type, Unit, etc.)
        support_folder: Path to support documents folder
        model: Ollama model name (default: env or llama3.2)
        ollama_url: Ollama base URL (default: env or http://localhost:11434)
        limit: Max nodes to process (0 = all)
    
    Returns:
        List of dicts with keys TABLE_COLUMNS (Name, Conceptual definition, Usage of data, Value, Value type, Unit, Source description)
    """
    model = model or os.getenv("LLAMA_MODEL_NAME", "llama3.2")
    ollama_url = (ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
    support_text = load_support_documents(support_folder)
    if limit > 0:
        nodes = nodes[:limit]
    out_rows = []
    for i, node in enumerate(nodes):
        name = node.get("Name", "")
        prompt = build_prompt(node, support_text)
        try:
            raw = call_ollama(prompt, model, ollama_url)
            block = extract_block_from_response(raw)
            row = parse_ollama_block(block)
            if row:
                for col in TABLE_COLUMNS:
                    if not (row.get(col) or "").strip() and (node.get(col) or "").strip():
                        row[col] = node.get(col, "")
                row["Name"] = row.get("Name") or name
                out_rows.append(row)
            else:
                out_rows.append({col: node.get(col, "") for col in TABLE_COLUMNS})
        except Exception:
            out_rows.append({col: node.get(col, "") for col in TABLE_COLUMNS})
    return out_rows


def main():
    parser = argparse.ArgumentParser(
        description="Get extracted nodes + support documents → Ollama → full table (CSV)."
    )
    parser.add_argument(
        "--nodes-csv",
        default="",
        help="Input CSV of semantic nodes (optional; else use --data-folder to extract)",
    )
    parser.add_argument(
        "--data-folder",
        default="Data",
        help="Data folder for extraction when --nodes-csv is not set (default: Data)",
    )
    parser.add_argument(
        "--support",
        default="support_files",
        help="Support documents folder (default: support_files)",
    )
    parser.add_argument(
        "--output",
        default="ollama_semantic_table.csv",
        help="Output CSV path (default: ollama_semantic_table.csv)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LLAMA_MODEL_NAME", "llama3.2"),
        help="Ollama model name (default: LLAMA_MODEL_NAME or llama3.2)",
    )
    parser.add_argument(
        "--ollama-url",
        default=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        help="Ollama base URL (default: OLLAMA_URL or http://localhost:11434)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only first N nodes (0 = all)",
    )
    args = parser.parse_args()

    # Load nodes
    if args.nodes_csv and os.path.isfile(args.nodes_csv):
        nodes = load_nodes_from_csv(args.nodes_csv)
        print(f"Loaded {len(nodes)} nodes from {args.nodes_csv}")
    else:
        if not os.path.isdir(args.data_folder):
            print(f"Data folder not found: {args.data_folder}. Use --nodes-csv or set --data-folder.")
            sys.exit(1)
        nodes = load_nodes_from_extraction(args.data_folder)
        print(f"Extracted {len(nodes)} nodes from {args.data_folder}")

    if not nodes:
        print("No nodes to process.")
        sys.exit(0)

    # Load support documents
    support_text = load_support_documents(args.support)
    if support_text:
        print(f"Loaded support documents ({len(support_text)} chars)")
    else:
        print("No support documents found; Ollama will use only node data.")

    # Optional limit
    if args.limit > 0:
        nodes = nodes[: args.limit]
        print(f"Processing first {args.limit} nodes")

    # Output rows: one per node, filled by Ollama or fallback to original
    out_rows = []
    for i, node in enumerate(nodes):
        name = node.get("Name", "")
        print(f"  [{i+1}/{len(nodes)}] {name or '(unnamed)'}...", end=" ", flush=True)
        prompt = build_prompt(node, support_text)
        try:
            raw = call_ollama(prompt, args.model, args.ollama_url)
            block = extract_block_from_response(raw)
            row = parse_ollama_block(block)
            if row:
                # Prefer Ollama row; fill missing from node
                for col in TABLE_COLUMNS:
                    if not (row.get(col) or "").strip() and (node.get(col) or "").strip():
                        row[col] = node.get(col, "")
                row["Name"] = row.get("Name") or name
                out_rows.append(row)
                print("OK")
            else:
                # Fallback: use node as-is
                out_rows.append({col: node.get(col, "") for col in TABLE_COLUMNS})
                print("fallback")
        except Exception as e:
            print(f"Error: {e}")
            out_rows.append({col: node.get(col, "") for col in TABLE_COLUMNS})

    # Write table
    out_path = args.output
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TABLE_COLUMNS)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
