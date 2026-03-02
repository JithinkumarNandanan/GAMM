# Quick Start Guide

## Step-by-Step Setup

### Step 1: Install Required Packages

```bash
# Install official Gemini API package (recommended)
pip install google-genai

# OR install legacy package (also supported)
pip install google-generativeai

# Optional: For PDF/DOCX support in support documents
pip install PyPDF2 python-docx
```

### Step 2: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### Step 3: Set Environment Variable

**Recommended: Use `GEMINI_API_KEY` (official)**
```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key-here"
```

```cmd
# Windows CMD
set GEMINI_API_KEY=your-api-key-here
```

```bash
# Linux/Mac
export GEMINI_API_KEY="your-api-key-here"
```

**Alternative: `GOOGLE_API_KEY` (also supported for compatibility)**
```powershell
# Windows PowerShell
$env:GOOGLE_API_KEY="your-api-key-here"
```

**Permanent Setup (Windows):**
1. Open System Properties → Environment Variables
2. Add new User variable: `GEMINI_API_KEY` = `your-api-key-here`

**Permanent Setup (Linux/Mac):**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Step 4: Test Gemini Setup (Recommended)

Run the setup script to verify everything works:

```bash
python setup_gemini.py
```

You should see:
```
✅ GOOGLE_API_KEY found: ...
✅ Gemini API initialized successfully!
✅ Gemini test successful!
✅ GEMINI IS READY TO USE!
```

### Step 5: Run the Pipeline (without Streamlit)

To run the full pipeline from the command line (no Streamlit UI):

```bash
python integrated_pipeline.py --source Data/source --target Data/target
```

**All CLI options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Folder with source AAS/XML/JSON files | *(required)* |
| `--target` | Folder with target AAS/XML/JSON files | *(required)* |
| `--output` | Folder for output files | `output` |
| `--support` | Folder with support documents for enrichment | `support_files` |
| `--support-urls` | URL(s) to load as support docs (e.g. SimVSM parameter definitions); repeat for multiple | (none) |
| `--eclass` | Custom eCl@ss library file | (none) |
| `--ieccdd` | Custom IEC CDD library file | (none) |
| `--no-gemini` | Disable Gemini; use Llama/OpenAI only | Gemini enabled |

**Examples:**

```powershell
# Windows PowerShell – basic run
python integrated_pipeline.py --source Data/source --target Data/target

# Custom output folder
python integrated_pipeline.py --source Data/source --target Data/target --output results

# With support documents in Data/support_files
python integrated_pipeline.py --source Data/source --target Data/target --support Data/support_files

# With SimVSM process/product parameter definitions (URL loaded as support doc)
python integrated_pipeline.py --source Data/source --target Data/target --support-urls "https://simvsm.info/en/index.html?processsingle.html"

# Without Gemini (Llama/OpenAI only)
python integrated_pipeline.py --source Data/source --target Data/target --no-gemini
```

## Complete Example

### Windows PowerShell:
```powershell
# Navigate to project folder
cd D:\Thesis\template

# 1. Set API key (official way)
$env:GEMINI_API_KEY="AIzaSy..."

# 2. Test Gemini
python setup_gemini.py

# 3. Run pipeline
python integrated_pipeline.py --source Data/source --target Data/target
```

### Linux/Mac:
```bash
# 1. Set API key
export GEMINI_API_KEY="AIzaSy..."

# 2. Test Gemini
python setup_gemini.py

# 3. Run pipeline
python integrated_pipeline.py --source Data/source --target Data/target
```

## Troubleshooting

### "GOOGLE_API_KEY not set"
- Make sure you set the environment variable in the SAME terminal window
- On Windows, use PowerShell or CMD (not Git Bash)
- Restart your terminal after setting the variable

### "google-generativeai package not found"
```bash
pip install google-generativeai
```

### "Gemini API call failed"
- Check your API key is correct
- Verify you have API quota available
- Check your internet connection

### Run without Gemini (if issues persist)
```bash
python integrated_pipeline.py --source Data/source --target Data/target --no-gemini
```

## What Happens When You Run the Pipeline

1. **Extracts** semantic nodes from source files
2. **Extracts** semantic nodes from target files
3. **Enriches** source nodes:
   - First: Searches support documents (Data/support_files/ and any --support-urls)
   - Then: Searches eClass library (EClass folder)
   - Then: Searches IEC CDD library
   - Finally: Uses Gemini AI (if enabled)
4. **Keeps** target nodes as extracted (no enrichment)
5. **Maps** source to target nodes
6. **Generates** reports in output/ folder

## Output Files

All results are saved to `output/` folder:
- `source_nodes.csv` - Source nodes with enrichments
- `target_nodes.csv` - Target nodes (as extracted, no enrichment)
- `semantic_mapping_*.json` - Mapping results
- `pipeline_report_*.txt` - Human-readable report
- `pipeline_summary_*.json` - Machine-readable summary

