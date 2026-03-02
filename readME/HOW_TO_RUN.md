# How to Run the Complete System

## Main Entry Point
**Run: `integrated_pipeline.py`** - This is the main file that runs the entire 9-layer pipeline.

## Quick Start

### Step 1: Organize Your Files

You need to separate your files into **source** and **target** folders:

```
Data/
├── source/          (source AAS files)
│   ├── IDTA 02006-3-0_Template_Digital Nameplate.json
│   └── ...
└── target/          (target AAS files)
    ├── Example_AAS_ServoDCMotor - Simplified V2.0.xml
    └── ...
```

### Step 2: Run the Pipeline

**Basic Command:**
```bash
python integrated_pipeline.py --source Data/source --target Data/target
```

**With Custom Output Folder:**
```bash
python integrated_pipeline.py --source Data/source --target Data/target --output results/
```

**With Custom Libraries:**
```bash
python integrated_pipeline.py --source Data/source --target Data/target --eclass eclass_library.json --ieccdd ieccdd_library.json
```

## What the Pipeline Does

1. **Extracts** semantic nodes from source files
2. **Extracts** semantic nodes from target files  
3. **Enriches** source nodes with eCl@ss/IEC CDD
4. **Enriches** target nodes with eCl@ss/IEC CDD
5. **Maps** source nodes to target nodes (semantic matching)
6. **Generates** comprehensive reports

## Output Files

All results are saved to the `output/` folder (or your custom folder):
- `source_nodes.csv` - Extracted source semantic nodes
- `target_nodes.csv` - Extracted target semantic nodes
- `source_nodes_enriched.csv` - Enriched source nodes
- `target_nodes_enriched.csv` - Enriched target nodes
- `mapping_results.json` - Complete mapping results
- `mapping_summary.csv` - Summary of matches
- `pipeline_report.json` - Full pipeline report

## Alternative: Run Individual Modules

If you only need specific functionality:

### Extract Only (No Enrichment/Mapping)
```bash
python datamap.py
```
- Processes files in `data/` folder
- Outputs: `semantic_nodes.csv`

### Extract with Gemini (LLM-assisted)
```bash
python datamap_gpt.py
```
- Requires: `GOOGLE_API_KEY` environment variable
- Processes files in `Data/` folder
- Outputs: `semantic_nodes.csv`

## Requirements

All Python files must be in the same directory:
- ✅ `integrated_pipeline.py` (main)
- ✅ `semantic_node_enhanced.py` (required)
- ✅ `datamap.py` (required)
- ✅ `enrichment_module.py` (required)
- ✅ `mapping_module.py` (required)

Optional:
- `datamap_gpt.py` (for LLM-assisted extraction, standalone)

