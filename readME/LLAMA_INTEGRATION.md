# Llama 4 Integration for Local Reasoning

This document explains how to use Llama 4 (or Llama 3.x) for local reasoning tasks in the semantic enrichment pipeline, as specified in your AI Model Selection Strategy.

## Overview

The system now supports **Llama for local reasoning** tasks, providing privacy-focused AI processing that runs entirely on your local machine or university servers. This aligns with your strategy document which specifies:

- **Local Reasoning:** Mistral-7B or **Llama-3** for local deployment on university servers to maintain data privacy

## Supported Backends

The system automatically detects and supports four Llama backends:

### 1. llama-stack (Official Meta CLI) - **NEW for Llama 4**
**For downloading and using official Llama 4 models from Meta**

1. **Install llama-stack CLI:**
   ```bash
   pip install llama-stack
   # or update if already installed
   pip install llama-stack -U
   ```

2. **List available models:**
   ```bash
   llama model list
   # For all versions including older ones:
   llama model list --show-all
   ```

3. **Download Llama 4 Scout model:**
   ```bash
   llama model download --source meta --model-id Llama-4-Scout-17B-16E-Instruct
   ```
   
   When prompted for the custom URL, paste your unique URL:
   ```
   https://llama4.llamameta.net/*?Policy=...
   ```

4. **Configure the system:**
   The system will automatically detect models downloaded via llama-stack. You can also set:
   ```bash
   set LLAMA_STACK_MODEL_PATH=C:\Users\YourName\.llama\models\Llama-4-Scout-17B-16E-Instruct
   set LOAD_LLAMA_TRANSFORMERS=true
   ```

**Available Llama 4 Models:**
- `Llama-4-Scout-17B-16E-Instruct` (Recommended for instruction following)
- `Llama-4-Scout-17B-16E` (Pretrained base model)
- `Llama-Guard-4-12B` (Protections model)
- `Llama-Prompt-Guard-2-86M` (Lightweight prompt guard)
- `Llama-Prompt-Guard-2-22M` (Ultra-lightweight prompt guard)

**Note:** The custom URL is valid for 48 hours and allows up to 5 downloads. Save it if you need to download again.

### 2. Ollama (Recommended for Easy Setup)
**Easiest to set up and use**

1. Install Ollama from https://ollama.ai/
2. Pull a Llama model:
   ```bash
   ollama pull llama3.2
   # or
   ollama pull llama3.1
   # or
   ollama pull mistral
   ```
3. The system will automatically detect Ollama running on `http://localhost:11434`

**Configuration:**
- Set `OLLAMA_URL` environment variable if using a different URL
- Set `LLAMA_MODEL_NAME` environment variable to specify model (default: "llama3.2")

### 3. llama-cpp-python (For GGUF Models)
**For direct model file usage**

1. Install: `pip install llama-cpp-python`
2. Download a GGUF model file (e.g., from Hugging Face)
3. Set environment variable:
   ```bash
   set LLAMA_MODEL_PATH=C:\path\to\your\model.gguf
   ```

### 4. Transformers (Hugging Face)
**For full model loading**

1. Install: `pip install transformers torch`
2. Set environment variables:
   ```bash
   set LLAMA_MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
   set LOAD_LLAMA_TRANSFORMERS=true
   ```

**Note:** This requires significant RAM/VRAM and is memory-intensive.

## Usage

### Basic Usage

The `SemanticNodeEnricher` now supports Llama for local reasoning:

```python
from enrichment_module import SemanticNodeEnricher

# Enable Llama for local reasoning (privacy-focused)
enricher = SemanticNodeEnricher(
    use_llama=True,        # Enable Llama
    use_gemini=True,       # Keep Gemini as fallback
    prefer_local=True      # Use Llama before Gemini when both available
)
```

### Priority Order

When both Llama and Gemini are available:
- If `prefer_local=True`: Llama (local) → Gemini (cloud)
- If `prefer_local=False`: Gemini (cloud) → Llama (local)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` |
| `LLAMA_MODEL_NAME` | Model name for Ollama or Hugging Face | `llama3.2` |
| `LLAMA_MODEL_PATH` | Path to GGUF model file | None |
| `LLAMA_STACK_MODEL_PATH` | Path to llama-stack downloaded model | Auto-detected |
| `LOAD_LLAMA_TRANSFORMERS` | Load transformers model on startup | `false` |

## Integration with Your Strategy

According to your AI Model Selection Strategy document:

- ✅ **Extraction/Mining:** Uses Gemini 1.5 Flash or GPT-4o-mini (already implemented)
- ✅ **Vector Embeddings:** Uses Salesforce SFR-Embedding-Mistral (can be added)
- ✅ **Local Reasoning:** Uses **Llama-3/4** for local deployment (now implemented)

## Benefits

1. **Privacy:** All processing happens locally, no data sent to cloud APIs
2. **Cost:** No API costs for local models
3. **Control:** Full control over model selection and configuration
4. **Compliance:** Suitable for proprietary data and university servers

## Example Output

When Llama generates descriptions, they are marked with `source: "llama_local"`:

```python
{
    "definition": "Maximum velocity represents the highest speed...",
    "usage": "Used for performance specifications...",
    "source": "llama_local"
}
```

## Troubleshooting

### Ollama not detected
- Ensure Ollama is running: `ollama serve`
- Check if model is pulled: `ollama list`
- Verify URL: `curl http://localhost:11434/api/tags`

### llama-cpp-python issues
- Verify model file exists and is valid GGUF format
- Check `LLAMA_MODEL_PATH` is set correctly
- Ensure sufficient RAM for model size

### Transformers issues
- Requires significant memory (8GB+ RAM for 3B models)
- Set `LOAD_LLAMA_TRANSFORMERS=true` explicitly
- Consider using smaller models or quantization

## Next Steps

1. Install and configure your preferred Llama backend
2. Test with: `use_llama=True` in your enrichment pipeline
3. Monitor performance and adjust model selection as needed

For questions or issues, check the console output for detailed backend detection messages.
