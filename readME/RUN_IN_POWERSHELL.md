# How to Run in PowerShell

## Complete Step-by-Step Guide for Windows PowerShell

### Step 1: Open PowerShell

1. Press `Win + X` and select "Windows PowerShell" or "Terminal"
2. Navigate to your project folder:
```powershell
cd D:\Thesis\template
```

### Step 2: Set Your Gemini API Key

**Option A: Set for Current Session (Recommended for Testing)**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

**Option B: Use Legacy Variable (Also Works)**
```powershell
$env:GOOGLE_API_KEY="your-api-key-here"
```

**Verify it's set:**
```powershell
echo $env:GEMINI_API_KEY
```

### Step 3: Test Gemini Setup (Optional but Recommended)

```powershell
python setup_gemini.py
```

**Expected Output:**
```
✅ GEMINI_API_KEY found: AIzaSy...xxxx
✅ Gemini API initialized successfully!
✅ Gemini test successful!
✅ GEMINI IS READY TO USE!
```

### Step 4: Run the Integrated Pipeline

```powershell
python integrated_pipeline.py --source Data/source --target Data/target
```

**With Custom Options:**
```powershell
# Custom output folder
python integrated_pipeline.py --source Data/source --target Data/target --output results/

# Custom support files folder
python integrated_pipeline.py --source Data/source --target Data/target --support Data/support_files

# Disable Gemini (if you have issues)
python integrated_pipeline.py --source Data/source --target Data/target --no-gemini
```

## Complete Example (Copy-Paste Ready)

```powershell
# Navigate to project folder
cd D:\Thesis\template

# Set API key (replace with your actual key)
$env:GEMINI_API_KEY="AIzaSyYourActualKeyHere"

# Test Gemini setup
python setup_gemini.py

# Run the pipeline
python integrated_pipeline.py --source Data/source --target Data/target
```

## Troubleshooting

### "python is not recognized"
```powershell
# Try python3 instead
python3 setup_gemini.py

# Or use full path
C:\Python\python.exe setup_gemini.py
```

### "GOOGLE_API_KEY not set"
- Make sure you set the variable in the SAME PowerShell window
- Don't close PowerShell after setting the variable
- Verify with: `echo $env:GEMINI_API_KEY`

### "Module not found"
```powershell
# Install required packages
pip install google-genai
# OR
pip install google-generativeai
```

### Environment Variable Not Persisting
- PowerShell variables only last for the current session
- To make permanent, use System Environment Variables:
  1. Right-click "This PC" → Properties
  2. Advanced System Settings → Environment Variables
  3. Add new User variable: `GEMINI_API_KEY` = `your-key`

## Quick Reference

| Task | Command |
|------|---------|
| Set API Key | `$env:GEMINI_API_KEY="your-key"` |
| Test Setup | `python setup_gemini.py` |
| Run Pipeline | `python integrated_pipeline.py --source Data/source --target Data/target` |
| Check API Key | `echo $env:GEMINI_API_KEY` |
| Install Package | `pip install google-genai` |

