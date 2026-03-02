# Quick Start Guide - Streamlit Interface

## Start the Application

```bash
streamlit run streamlit_app.py
```

## Step-by-Step Workflow

### 1. Upload Files (Sidebar)
- **Source Files**: Drag and drop your source XML/JSON/AML files
- **Target Files**: Drag and drop your target XML/JSON/AML files  
- **Support Files** (Optional): Upload documentation files for enrichment

### 2. Extract Nodes
- Click **"🔍 Extract Nodes"** button
- Wait for extraction to complete
- Review the success messages

### 3. Review & Edit Nodes
- Go to **"📊 Source Nodes"** tab
- Go to **"📊 Target Nodes"** tab
- Edit any node details directly in the tables
- All changes are saved automatically

### 4. Run Mapping
- Click **"🚀 Start Mapping Process"** button
- Wait for the pipeline to complete (may take a few minutes)
- View the results automatically

### 5. View Results
- See mapping statistics
- Browse the matches table
- Download results as CSV

## Tips

- ✅ You can edit nodes before running mapping
- ✅ Support files help with enrichment
- ✅ Results are saved in session state
- ✅ Use "Reset" button to start fresh

## Troubleshooting

**App won't start?**
```bash
pip install streamlit pandas
```

**No nodes extracted?**
- Check file formats are supported
- Verify files are not corrupted

**Mapping fails?**
- Ensure both source and target nodes exist
- Check that Ollama is running (if using LLM)
