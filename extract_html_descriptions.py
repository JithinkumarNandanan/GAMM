#!/usr/bin/env python3
"""
Extract SimVSM class/parameter descriptions from local HTML docs.

Output format:
[
  {
    "class_name": "...",
    "source_file": "...html",
    "brief_description": "...",
    "parameters": [
      {
        "parameter_name": "...",
        "required": "...",
        "description": "...",
        "section": "Process Parameter"
      }
    ]
  }
]
"""

import argparse
import html
import json
import os
import re
from typing import Dict, List


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_class_name(title_text: str, file_name: str) -> str:
    title = _clean_text(title_text)
    if not title:
        return os.path.splitext(file_name)[0]
    # Keep only the first breadcrumb part as class title.
    for sep in ("|", "-", ">", "»", "•"):
        if sep in title:
            left = title.split(sep)[0].strip()
            if left:
                return left
    return title


def _parse_with_bs4(filepath: str) -> Dict:
    from bs4 import BeautifulSoup  # type: ignore

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    soup = BeautifulSoup(raw, "html.parser")

    title_text = soup.title.get_text(" ", strip=True) if soup.title else ""
    class_name = _extract_class_name(title_text, os.path.basename(filepath))

    # Use first substantial paragraph/div as short brief description.
    brief = ""
    for tag in soup.find_all(["p", "div"], limit=40):
        t = _clean_text(tag.get_text(" ", strip=True))
        if len(t) >= 40:
            brief = t
            break

    parameters: List[Dict[str, str]] = []
    seen = set()
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        header = [_clean_text(c.get_text(" ", strip=True)).lower() for c in header_cells]
        if len(header) < 3:
            continue
        # Only process proper parameter tables: "<something> Parameter | Required | Description"
        if "required" not in header or "description" not in header:
            continue
        if "parameter" not in header[0]:
            continue
        section = _clean_text(header_cells[0].get_text(" ", strip=True))

        for r in rows[1:]:
            cells = r.find_all(["th", "td"])
            if len(cells) < 3:
                continue
            p_name = _clean_text(cells[0].get_text(" ", strip=True))
            required = _clean_text(cells[1].get_text(" ", strip=True))
            desc = _clean_text(cells[2].get_text(" ", strip=True))
            if not p_name or p_name.lower() == "parameter":
                continue
            key = (p_name.lower(), section.lower())
            if key in seen:
                continue
            seen.add(key)
            parameters.append(
                {
                    "parameter_name": p_name,
                    "required": required,
                    "description": desc,
                    "section": section,
                }
            )

    return {
        "class_name": class_name,
        "source_file": os.path.basename(filepath),
        "brief_description": brief,
        "parameters": parameters,
    }


def extract_docs(input_dir: str) -> List[Dict]:
    entries: List[Dict] = []
    for root, _, files in os.walk(input_dir):
        for file_name in sorted(files):
            if not file_name.lower().endswith((".html", ".htm")):
                continue
            path = os.path.join(root, file_name)
            try:
                entries.append(_parse_with_bs4(path))
            except Exception as e:
                entries.append(
                    {
                        "class_name": os.path.splitext(file_name)[0],
                        "source_file": file_name,
                        "brief_description": f"Parse error: {e}",
                        "parameters": [],
                    }
                )
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract SimVSM HTML parameter descriptions")
    parser.add_argument("--input", required=True, help="Folder containing SimVSM HTML docs")
    parser.add_argument(
        "--output",
        default="simvsm_extracted_parameters.json",
        help="Output JSON path (default: simvsm_extracted_parameters.json)",
    )
    args = parser.parse_args()

    entries = extract_docs(args.input)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"[OK] Wrote {len(entries)} HTML class entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
