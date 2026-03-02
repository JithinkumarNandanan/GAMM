# Enhanced Enrichment Features

## Overview

The enrichment module now supports multiple enrichment sources and automatically generates descriptions using Gemini API for comparison purposes.

## New Features

### 1. Document-Based Enrichment (`support_files` folder)

Users can add support documents to a `support_files` folder. The system will:
- Read documents from the folder (supports: TXT, JSON, MD, PDF, DOCX)
- Search for relevant information about semantic nodes
- Extract context around matches
- Use found information to enrich nodes

**Supported File Formats:**
- `.txt` - Plain text files
- `.html`, `.htm` - HTML files (text content extracted, tags stripped)
- `.json` - JSON files
- `.md` - Markdown files
- `.pdf` - PDF files (requires `PyPDF2`)
- `.docx`, `.doc` - Word documents (requires `python-docx`)

**Supported URLs:**
- HTML URLs (http:// or https://) - Automatically fetched and parsed for text content
- Useful for online help documentation, software manuals, or web-based technical documentation

### 2. Gemini API Description Generation

Even when enrichment is found from libraries or documents, the system:
- **Always generates a Gemini description** for comparison
- Stores Gemini description in node metadata
- Uses Gemini as fallback when no enrichment is found

**Benefits:**
- Compare library/document descriptions with AI-generated ones
- Ensure all nodes have descriptions for better matching
- Improve semantic understanding

## Enrichment Priority Order

The system tries enrichment sources in this order:

1. **eCl@ss Library** - International product classification standard
2. **IEC CDD Library** - IEC 61360 Common Data Dictionary
3. **Support Documents** - User-provided documents in `support_files` folder
4. **Gemini API** - AI-generated descriptions (always used for comparison)

## Usage

### Basic Usage
```bash
python integrated_pipeline.py --source Data/source --target Data/target
```

### With Support Documents
```bash
# Add documents to support_files/ folder, then run:
python integrated_pipeline.py --source Data/source --target Data/target --support support_files
```

### Disable Gemini (if needed)
```bash
python integrated_pipeline.py --source Data/source --target Data/target --no-gemini
```

## Setup

### 1. Create Support Files Folder
```bash
mkdir support_files
```

### 2. Add Documents
Place your support documents (PDF, TXT, MD, JSON, DOCX) in the `support_files/` folder.

### 3. Set Gemini API Key (Optional but Recommended)
```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your-api-key-here"

# Linux/Mac
export GOOGLE_API_KEY="your-api-key-here"
```

### 4. Install Optional Dependencies (for PDF/DOCX support)
```bash
pip install PyPDF2 python-docx
```

## Enrichment Statistics

The pipeline now tracks:
- `enriched_from_eclass` - Nodes enriched from eCl@ss
- `enriched_from_ieccdd` - Nodes enriched from IEC CDD
- `enriched_from_documents` - Nodes enriched from support documents
- `enriched_from_gemini` - Nodes enriched from Gemini API
- `not_found` - Nodes that couldn't be enriched

## Node Metadata

Enriched nodes now include:
- `enrichment_source` - Source of enrichment (eclass, ieccdd, documents, gemini)
- `gemini_definition` - Gemini-generated definition (for comparison)
- `gemini_usage` - Gemini-generated usage description (for comparison)
- Additional metadata based on source (eclass_id, irdi, source_file)

## Example

When a node is enriched:
- Primary description comes from the best matching source
- Gemini description is stored in metadata for comparison
- Both descriptions are available in output files

This allows you to:
- Compare library definitions with AI-generated ones
- Validate enrichment quality
- Improve matching accuracy


