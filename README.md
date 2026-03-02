# Semantic Node DataMapper

This project provides tools to extract and analyze semantic node information from Asset Administration Shell (AAS) files in multiple formats: JSON, XML, AML (AutomationML), EXM, and SIMVSM.

## Files

- `datamap.py` - Main script to extract semantic nodes from JSON, XML, AML, EXM, and SIMVSM files
- `dataframe.py` - Converts CSV output to pandas DataFrame for analysis
- `example_analysis.py` - Demonstrates various analysis techniques
- `semantic_nodes.csv` - Generated CSV file with extracted semantic nodes
- `data/` - Folder containing input files (JSON, XML, AML, EXM, SIMVSM)

## Usage

### 1. Extract Semantic Nodes from All Supported Files

```bash
python3 datamap.py
```

This will:
- Process all supported files (JSON, XML, AML, EXM, SIMVSM) in the `data/` folder
- Extract semantic node information according to the specified mapping
- Generate `semantic_nodes.csv` with the results
- Display a summary of extracted data

**Supported File Formats:**
- **JSON**: AAS JSON format files
- **XML**: AAS XML format files  
- **AML**: AutomationML format files
- **EXM**: EXM format files (treated as XML)
- **SIMVSM**: SIMVSM format files (treated as XML)
- **SIMVSM**: SIMVSM format files (treated as XML)

### 2. Convert to DataFrame for Analysis

```bash
python3 dataframe.py
```

This will:
- Load the CSV data into a pandas DataFrame
- Display comprehensive analysis and statistics
- Show filtering and search examples
- Provide export options

### 3. Run Example Analysis

```bash
python3 example_analysis.py
```

This demonstrates:
- Basic DataFrame operations
- Filtering and searching
- Statistical analysis
- Export capabilities

## Semantic Node Mapping

The extraction follows this mapping across all supported file formats:

| Field | Source | Description |
|-------|--------|-------------|
| Name | `idShort`/`Name` | Short identifier from source files |
| Conceptual definition | `description` (en) or (optional) conceptDescriptions | From element description; if source has none, left for enrichment (support files / Llama) unless `USE_CONCEPT_DESCRIPTIONS_FROM_SOURCE=1` |
| Usage of data | (blank) | Not available in source files |
| Value | `value`/`Value`/`DefaultValue` | Actual value from source files (if present) |
| Value type | `valueType`/`AttributeDataType` | Data type from source files (if present) |
| Unit | `unit` | Measurement unit from source files (if present) |
| Source description | (blank) | Not specified |

**Format-Specific Details:**
- **JSON**: Uses `idShort`, `description`, `value`, `valueType`, `unit`
- **XML**: Uses AAS XML namespace elements with same field names
- **AML**: Uses `Name`, `Description`, `Value`/`DefaultValue`, `AttributeDataType`
- **EXM**: Treated as XML format
- **SIMVSM**: Treated as XML format

## Data Analysis Features

The DataFrame provides various analysis capabilities:

- **Filtering**: By value type, presence of values, descriptions
- **Searching**: By name or description content
- **Statistics**: Completeness, distribution analysis
- **Export**: To Excel, JSON, or other formats
- **Custom Analysis**: Pattern matching, data quality assessment

## Requirements

- Python 3.6+
- pandas
- json (built-in)
- csv (built-in)
- os (built-in)
- sys (built-in)
- xml.etree.ElementTree (built-in)

For Excel export (optional):
- openpyxl

## Example Output

The scripts process all supported file formats and extract information like:

**From JSON/XML files:**
```
Name: URIOfTheProduct
Conceptual definition: unique global identification of the product instance using an universal resource identifier (URI)
Value: https://www.domain-abc.com/Model-Nr-1234/Serial-Nr-5678
Value type: xs:anyURI
```

**From AML files:**
```
Name: AutomationMLBaseInterface
Conceptual definition: Standard Automation Markup Language Interface Class Library
Value type: xs:string
```

**From EXM files:**
```
Name: ExampleMotor
Conceptual definition: (extracted from XML structure)
Value: (if present)
Value type: (if present)
```

## Multi-Format Support

The system now supports extracting semantic nodes from multiple file formats:

### JSON Files (AAS JSON Format)
- Processes submodels and concept descriptions
- Extracts `idShort`, `description`, `value`, `valueType`, `unit`
- Handles nested submodel elements recursively

### XML Files (AAS XML Format)  
- Parses AAS XML namespace elements
- Extracts same fields as JSON but from XML structure
- Handles multilingual descriptions (prefers English)

### AML Files (AutomationML Format)
- Processes interface class libraries
- Extracts `Name`, `Description`, `Value`/`DefaultValue`, `AttributeDataType`
- Handles nested interface classes and attributes

### EXM Files
- Treated as XML format for processing
- Same extraction logic as XML files

### SIMVSM Files
- Treated as XML format for processing
- Same extraction logic as XML files

## Caching

- **eClass library only:** The **EClass** folder (local eClass XML dictionary) is loaded and cached in `.cache/eclass_library_*.pkl` to speed up later runs. This cache stores only the eClass term dictionary (name → definition), not per-node or per-file conceptual definitions.
- **No cache of extraction or enrichment:** Source extraction and enrichment (support files, Llama, eClass lookup) are run fresh each time. Conceptual definitions are not read from any previous run.

## Optional: Conceptual definition from source file

Descriptions **in the file** are read by default: we use each element’s inline `description` and the same file’s **conceptDescriptions** (e.g. IDTA templates) so definitions like “Indentification of the classification system where the qualification is classified” appear as conceptual definition.

- **Default:** `USE_CONCEPT_DESCRIPTIONS_FROM_SOURCE=1`. We use inline description and conceptDescriptions from the AAS file when present. Missing descriptions are left for enrichment (support files / Llama).
- **To leave conceptual definition only for support files/Llama:** set `USE_CONCEPT_DESCRIPTIONS_FROM_SOURCE=0` (e.g. in PowerShell: `$env:USE_CONCEPT_DESCRIPTIONS_FROM_SOURCE = "0"`).

## Generated Files

- `semantic_nodes.csv` - Main output with all extracted semantic nodes
- `semantic_nodes_analysis.xlsx` - Excel export (if openpyxl available)
- `semantic_nodes_analysis.json` - JSON export for programmatic use
