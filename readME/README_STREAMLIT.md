# Streamlit Interface for Semantic Node Mapping

## Overview

This Streamlit application provides a user-friendly web interface for the semantic node mapping pipeline. Users can upload files, review extracted nodes, and run the complete mapping process through an intuitive web UI.

## Features

- 📁 **Multi-file Upload**: Upload source, target, and support files through drag-and-drop interface
- 🔍 **Automatic Extraction**: Extract semantic nodes from uploaded files automatically
- ✏️ **Editable Tables**: Review and edit extracted nodes before mapping
- 🚀 **One-Click Mapping**: Run the complete pipeline with a single button
- 📈 **Results Visualization**: View mapping results, statistics, and download CSV reports

## Installation

1. Ensure all dependencies are installed:
```bash
pip install streamlit pandas
```

2. Make sure all pipeline dependencies are installed (see main README.md)

## Running the Application

Start the Streamlit app:

```bash
streamlit run streamlit_app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage Guide

### Step 1: Upload Files

1. **Source Files**: Upload your source files (XML, JSON, AML, EXM, SIMVSM) in the sidebar
2. **Target Files**: Upload your target files (XML, JSON, AML, EXM, SIMVSM) in the sidebar
3. **Support Files** (Optional): Upload support documents (TXT, HTML, PDF, DOCX, JSON, MD, YAML, CSV) for enrichment
4. **Support URLs** (Optional): Enter HTML URLs (one per line) to fetch help/documentation pages online

### Step 2: Extract Nodes

1. Click the **"🔍 Extract Nodes"** button in the sidebar
2. The system will extract semantic nodes from all uploaded files
3. You'll see success messages showing how many nodes were extracted

### Step 3: Review and Edit Nodes

1. Navigate to the **"📊 Source Nodes"** tab to review source nodes
2. Navigate to the **"📊 Target Nodes"** tab to review target nodes
3. Edit any node details directly in the tables:
   - Name
   - Conceptual definition
   - Usage of data
   - Value
   - Value type
   - Unit
   - Source description

### Step 4: Run Mapping

1. Click the **"🚀 Start Mapping Process"** button
2. The system will:
   - Enrich nodes using eClass, IEC CDD, and support files
   - Use context-aware LLM for intelligent matching
   - Perform semantic mapping between source and target nodes
3. Wait for the process to complete (may take a few minutes)

### Step 5: View Results

1. View mapping statistics (total matches, confidence levels)
2. Review enrichment statistics for source and target nodes
3. Browse the mapping matches table
4. Download results as CSV if needed

## File Format Support

### Source/Target Files
- **XML**: AAS XML format
- **JSON**: AAS JSON format
- **AML**: AutomationML format
- **EXM**: Extended XML format
- **SIMVSM**: SIMVSM format (treated as XML)

### Support Files
- **TXT**: Plain text files
- **HTML/HTM**: HTML files (text content extracted, tags stripped)
- **PDF**: PDF documents (requires PyPDF2)
- **DOCX**: Word documents (requires python-docx)
- **JSON**: JSON files
- **MD**: Markdown files
- **YAML**: YAML configuration files
- **CSV**: CSV data files

### Support URLs
- **HTML URLs**: Enter web URLs (http:// or https://) to fetch HTML help/documentation pages
- URLs are fetched automatically and their text content is extracted for enrichment
- Each URL should be on a separate line in the text area
- Example: `https://example.com/software-help.html`

## Troubleshooting

### Application won't start
- Ensure Streamlit is installed: `pip install streamlit`
- Check that all pipeline dependencies are installed

### Extraction fails
- Verify file formats are supported
- Check that files are not corrupted
- Ensure files follow the expected AAS/AML structure

### Mapping takes too long
- Large files may take several minutes
- Check that Ollama/Llama is running if using LLM enrichment
- Consider reducing the number of files

### No matches found
- Verify that source and target nodes have similar properties
- Check that nodes have been properly enriched
- Review node names and definitions for compatibility

## Advanced Features

### Context-Aware Enrichment
The system uses LLM intelligence to understand semantic meaning in context. For example:
- "capacity" → volume (mechanical context)
- "capacity" → charge (electrical context)
- "capacity" → occupancy (hall context)

### Multi-Format Support
The pipeline automatically detects and processes multiple file formats without manual configuration.

## Support

For issues or questions, refer to the main project documentation or create an issue in the repository.
