#!/usr/bin/env python3
"""
Demo: How the pipeline asks Ollama for enrichment.

This script shows the exact prompts and API request bodies sent to Ollama in three cases:
  1. Ollama table (full row: Name, Conceptual definition, Usage of data, Value, Value type, Unit, Source description)
  2. Llama enricher (definition + usage when libraries didn't find a match)
  3. Normalization (expand name, e.g. max_V → Maximum Velocity)

Run with:  python demo_ollama_enrichment.py
No API key or running Ollama required to see the prompts; set DRY_RUN=1 to skip real calls.
"""

import os
import json

# ---------------------------------------------------------------------------
# 1. OLLAMA TABLE (used when you run pipeline with --ollama-table)
#    Source: ollama_table_from_nodes.build_prompt + call_ollama
# ---------------------------------------------------------------------------

def demo_ollama_table_prompt():
    """Build the same prompt the pipeline sends for one node when filling the table via Ollama."""
    node = {
        "Name": "NumberOfWorkers",
        "Value": "0",
        "Value type": "number",
        "Unit": "",
        "Conceptual definition": "",
        "Usage of data": "",
        "Source description": "",
    }
    support_text = (
        "[Document: simvsm_descriptions.txt]\n"
        "NumberOfWorkers: The number of workers involved in the process. "
        "Used to calculate workload and potential bottlenecks.\n"
        "Availability: The percentage of time the resource is available (%).\n"
    )
    from ollama_table_from_nodes import build_prompt
    prompt = build_prompt(node, support_text)
    return prompt, node


# ---------------------------------------------------------------------------
# 2. LLAMA ENRICHER (used in normal enrichment when support/eClass/IEC didn't find a match)
#    Source: enrichment_module.LlamaEnricher.generate_description
# ---------------------------------------------------------------------------

def demo_llama_enricher_prompt():
    """Same prompt the pipeline uses for definition + usage when libraries fail."""
    class FakeNode:
        name = "max_V"
        value_type = "Float"
        unit = "m/s"
        value = 1.5
    node = FakeNode()
    prompt = f"""Generate a concise technical definition and usage description for the following semantic node:

Name: {node.name}
Value Type: {node.value_type}
Unit: {node.unit if node.unit else 'N/A'}
Current Value: {node.value if node.value else 'N/A'}

Provide:
1. A clear, technical definition (1-2 sentences)
2. A brief usage description explaining when/why this data would be used

Format your response as:
DEFINITION: [definition text]
USAGE: [usage text]"""
    return prompt


# ---------------------------------------------------------------------------
# 3. NORMALIZATION (expand name using path/context)
#    Source: enrichment_module.expand_name_with_llama
# ---------------------------------------------------------------------------

def demo_normalization_prompt():
    """Same prompt the pipeline uses to expand e.g. max_V → Maximum Velocity."""
    name = "max_V"
    path = "Actuator/Mechanical/Linear"
    context = "Asset: RobotArm; Submodel: ProcessParameters"
    prompt_parts = []
    if path and path.strip():
        prompt_parts.append(f"Path: {path.strip()}")
        prompt_parts.append("")
    if context and context.strip():
        prompt_parts.append(f"Context: {context.strip()}")
        prompt_parts.append("")
    prompt_parts.append("Task: Expand this technical variable name into a clear, human-readable phrase.")
    prompt_parts.append("")
    prompt_parts.append("Use the Path/Context to disambiguate abbreviations:")
    prompt_parts.append("- In IndustrialMotor/Electrical: V->Voltage, I->Current, R->Resistance, n->Rotation Speed")
    prompt_parts.append("- In Mechanical/Linear: V->Velocity, n->Rotation Speed")
    prompt_parts.append("- In Electrical contexts: V->Voltage, I->Current, P->Power")
    prompt_parts.append("- In Fluid/Pressure contexts: P->Pressure, f->Flow")
    prompt_parts.append("")
    prompt_parts.append("IMPORTANT: Expand ALL abbreviations fully. Single letters must become full words.")
    prompt_parts.append("Examples: V_nom->Nominal Voltage, n_idle->Idle Rotation Speed, I_peak->Peak Current")
    prompt_parts.append("")
    prompt_parts.append(f"Variable name: {name}")
    prompt_parts.append("Expanded phrase:")
    return "\n".join(prompt_parts)


# ---------------------------------------------------------------------------
# API REQUEST (what is actually sent to Ollama)
# ---------------------------------------------------------------------------

def ollama_request_body(prompt: str, model: str = "gemma3:4b", max_tokens: int = 800) -> dict:
    """Exact JSON body sent to POST http://localhost:11434/api/generate"""
    return {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": max_tokens,
        },
    }


def main():
    print("=" * 70)
    print("DEMO: How the pipeline asks Ollama for enrichment")
    print("=" * 70)

    # ---- 1. Ollama table ----
    print("\n" + "-" * 70)
    print("1. OLLAMA TABLE (--ollama-table): one prompt per node, full table row")
    print("-" * 70)
    prompt1, node = demo_ollama_table_prompt()
    print("Example node:", node.get("Name"), "| Value type:", node.get("Value type"))
    print("\n--- PROMPT SENT TO OLLAMA ---\n")
    print(prompt1[:1800] + ("\n... [truncated]" if len(prompt1) > 1800 else ""))
    print("\n--- API REQUEST (POST /api/generate) ---")
    body1 = ollama_request_body(prompt1, max_tokens=800)
    print(json.dumps({**body1, "prompt": body1["prompt"][:400] + "..."}, indent=2))

    # ---- 2. Llama enricher ----
    print("\n" + "-" * 70)
    print("2. LLAMA ENRICHER (normal flow when eClass/IEC/support didn't find a match)")
    print("-" * 70)
    prompt2 = demo_llama_enricher_prompt()
    print("\n--- PROMPT SENT TO OLLAMA ---\n")
    print(prompt2)
    print("\n--- API REQUEST (POST /api/generate) ---")
    body2 = {
        "model": os.getenv("LLAMA_MODEL_NAME", "gemma3:4b"),
        "prompt": prompt2,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 300},
    }
    print(json.dumps(body2, indent=2))

    # ---- 3. Normalization ----
    print("\n" + "-" * 70)
    print("3. NORMALIZATION (expand name using path/context, before enrichment)")
    print("-" * 70)
    prompt3 = demo_normalization_prompt()
    print("\n--- PROMPT SENT TO OLLAMA ---\n")
    print(prompt3)
    print("\n--- API REQUEST (POST /api/generate) ---")
    body3 = {
        "model": os.getenv("LLAMA_MODEL_NAME", "gemma3:4b"),
        "prompt": prompt3,
        "stream": False,
        "options": {"temperature": 0.3, "max_tokens": 100},
    }
    print(json.dumps(body3, indent=2))

    print("\n" + "=" * 70)
    print("Summary: Ollama is called at")
    print("  - Normalization: 1 call per node (expand name) or 0 if document hint exists")
    print("  - With --ollama-table: 1 call per node (full table row)")
    print("  - Without --ollama-table: 1 call per node that libraries didn't enrich (definition + usage)")
    print("=" * 70)


if __name__ == "__main__":
    main()
