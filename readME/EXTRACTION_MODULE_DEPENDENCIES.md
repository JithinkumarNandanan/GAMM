# Python Files Required for Extraction Modules

## Overview
This document outlines which Python files are needed to run each extraction module in this project.

---

## 1. Basic Extraction Module (`datamap.py`)

**Standalone module** - No dependencies on other custom Python files.

### Required Files:
- ✅ `datamap.py` (only file needed)

### Standard Library Dependencies:
- `json`
- `csv`
- `os`
- `sys`
- `xml.etree.ElementTree`
- `typing`

### Usage:
```bash
python datamap.py
```

---

## 2. Enhanced Extraction Module with Gemini (`datamap_gpt.py`)

**Standalone module** - No dependencies on other custom Python files.

### Required Files:
- ✅ `datamap_gpt.py` (only file needed)

### Standard Library Dependencies:
- `json`
- `csv`
- `os`
- `sys`
- `xml.etree.ElementTree`
- `typing`
- `importlib`

### External Dependencies:
- `google-generativeai` (optional - runs in fallback mode if not available)
- Environment variable: `GOOGLE_API_KEY` (required for Gemini features)

### Usage:
```bash
python datamap_gpt.py
```

---

## 3. Integrated Pipeline (`integrated_pipeline.py`)

**Full pipeline** - Requires multiple custom modules.

### Required Files:
1. ✅ `integrated_pipeline.py` (main entry point)
2. ✅ `semantic_node_enhanced.py` (base data structures)
3. ✅ `datamap.py` (extraction functionality)
4. ✅ `enrichment_module.py` (eCl@ss and IEC CDD enrichment)
5. ✅ `mapping_module.py` (semantic matching)

### Dependency Chain:
```
integrated_pipeline.py
├── semantic_node_enhanced.py (no dependencies)
├── datamap.py (no dependencies)
├── enrichment_module.py
│   └── semantic_node_enhanced.py
└── mapping_module.py
    └── semantic_node_enhanced.py
```

### Standard Library Dependencies:
- `argparse`
- `os`
- `sys`
- `json`
- `csv`
- `datetime`
- `typing`

### Usage:
```bash
python integrated_pipeline.py --source data/source/ --target data/target/
```

---

## Summary Table

| Module | Files Required | Standalone? |
|--------|---------------|-------------|
| **Basic Extraction** | `datamap.py` | ✅ Yes |
| **Gemini Extraction** | `datamap_gpt.py` | ✅ Yes |
| **Integrated Pipeline** | `integrated_pipeline.py`<br>`semantic_node_enhanced.py`<br>`datamap.py`<br>`enrichment_module.py`<br>`mapping_module.py` | ❌ No (5 files) |

---

## Quick Reference

### For simple extraction only:
- Use: `datamap.py` or `datamap_gpt.py`
- Files needed: Just the one file you choose

### For full pipeline (extraction + enrichment + mapping):
- Use: `integrated_pipeline.py`
- Files needed: All 5 files listed above

---

## Notes

- `semantic_node_enhanced.py` is the base module that defines the `SemanticNode` and `SemanticNodeCollection` classes
- `datamap.py` is imported by `integrated_pipeline.py` for extraction
- Both `enrichment_module.py` and `mapping_module.py` depend on `semantic_node_enhanced.py`
- The other Python files (`view_dataframe.py`, `dataframe.py`, `example_analysis.py`) are utility/analysis scripts and not required for extraction


