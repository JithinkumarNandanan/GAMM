#!/usr/bin/env python3
"""
Semantic Node Enrichment Module

This module enriches semantic nodes with descriptions using a multi-layer approach:

1. Normalization Layer: Expands abbreviations (e.g., max_V → maximum velocity)
   - Uses rule-based expansion
   - Can be enhanced with Gemini AI for complex abbreviations

2. Enrichment Priority Order:
   a) Support Documents (FIRST): Searches user-provided documents in support_files/
      - Uses normalization to expand abbreviations before searching
   b) eCl@ss Library: International product and service classification standard
      - Top-K search (top 10 matches) with 90% similarity threshold
      - Uses normalization to expand abbreviations before searching
   c) IEC CDD Library: IEC 61360 Common Data Dictionary
      - Top-K search (top 10 matches) with 90% similarity threshold
      - Uses normalization to expand abbreviations before searching
   d) OpenAI (when OPENAI_API_KEY is set): Used when description not found in support files or libraries
   e) Llama AI (local) / Gemini AI: AI-generated descriptions when no matches in libraries/documents

When a semantic node lacks a conceptual definition or usage description,
this module searches these sources in priority order based on:
- Node name (with abbreviation expansion)
- Unit
- Value type
"""

import json
import re
import os
import importlib
import pickle
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Set, Any
from semantic_node_enhanced import SemanticNode, SemanticNodeCollection

# Set GRPC verbosity to reduce noise (helps with firewall/proxy issues)
os.environ["GRPC_VERBOSITY"] = "ERROR"

# Gemini API setup - try new google-genai package first, then fallback to google.generativeai
GEMINI_CLIENT = None
GEMINI_MODEL = None
GEMINI_AVAILABLE = False

try:
    # Try new google-genai package (official, uses GEMINI_API_KEY)
    from google import genai
    
    # Check for API key - new package uses GEMINI_API_KEY, but also check GOOGLE_API_KEY for compatibility
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if api_key:
        # New package: Client() automatically picks up GEMINI_API_KEY, or we can pass it
        if os.getenv("GEMINI_API_KEY"):
            # Use environment variable automatically
            GEMINI_CLIENT = genai.Client()
        else:
            # Pass API key explicitly (for GOOGLE_API_KEY compatibility)
            GEMINI_CLIENT = genai.Client(api_key=api_key)
        GEMINI_AVAILABLE = True
        print("Gemini API initialized using google-genai package (official)")
    else:
        print("Warning: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
except ImportError:
    # Fallback to google.generativeai package (legacy)
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            GEMINI_MODEL = genai.GenerativeModel("gemini-1.5-flash")
            GEMINI_AVAILABLE = True
            print("Gemini API initialized using google.generativeai package (legacy)")
        else:
            print("Warning: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")
    except ImportError:
        print("Warning: Neither google-genai nor google.generativeai package found.")
        print("Install with: pip install google-genai")
        print("Or for legacy: pip install google-generativeai")
    except Exception as e:
        print(f"Warning: Could not initialize Gemini (generativeai): {e}")
except Exception as e:
    print(f"Warning: Could not initialize Gemini (genai): {e}")

# OpenAI setup - used when OPENAI_API_KEY is set (fallback for descriptions not in support files)
OPENAI_CLIENT = None
OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        OPENAI_CLIENT = OpenAI(api_key=api_key)
        OPENAI_AVAILABLE = True
        print("OpenAI API initialized (OPENAI_API_KEY set)")
except ImportError:
    pass
except Exception as e:
    print(f"Warning: Could not initialize OpenAI: {e}")

# Llama setup for local reasoning (privacy-focused) - PRIMARY AI MODEL
LLAMA_MODEL = None
LLAMA_AVAILABLE = False
LLAMA_BACKEND = None  # 'ollama', 'llama_cpp', 'transformers', or None

try:
    # Try Ollama first (most common for local deployment)
    import requests
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        if response.status_code == 200:
            LLAMA_BACKEND = 'ollama'
            LLAMA_AVAILABLE = True
            print(f"Llama/Ollama detected at {ollama_url}")
    except:
        pass
except ImportError:
    pass

# Try llama-cpp-python (for GGUF models)
if not LLAMA_AVAILABLE:
    try:
        from llama_cpp import Llama
        LLAMA_BACKEND = 'llama_cpp'
        llama_model_path = os.getenv("LLAMA_MODEL_PATH")
        if llama_model_path and os.path.exists(llama_model_path):
            try:
                LLAMA_MODEL = Llama(model_path=llama_model_path, n_ctx=2048, verbose=False)
                LLAMA_AVAILABLE = True
                print(f"Llama model loaded from {llama_model_path}")
            except Exception as e:
                print(f"Warning: Could not load Llama model from {llama_model_path}: {e}")
    except ImportError:
        pass

# Try transformers (Hugging Face) as fallback - also supports llama-stack models
if not LLAMA_AVAILABLE:
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        try:
            import torch
        except ImportError:
            torch = None
        LLAMA_BACKEND = 'transformers'
        
        # Check for llama-stack downloaded models first
        llama_stack_path = os.getenv("LLAMA_STACK_MODEL_PATH")
        if not llama_stack_path:
            home_dir = os.path.expanduser("~")
            possible_paths = [
                os.path.join(home_dir, ".llama", "models"),
                os.path.join(home_dir, ".cache", "llama", "models"),
                os.path.join(os.getcwd(), "models", "llama"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    for item in os.listdir(path):
                        item_path = os.path.join(path, item)
                        if os.path.isdir(item_path) and ("llama-4" in item.lower() or "scout" in item.lower()):
                            llama_stack_path = item_path
                            break
                    if llama_stack_path:
                        break
        
        if llama_stack_path and os.path.exists(llama_stack_path):
            try:
                if os.getenv("LOAD_LLAMA_TRANSFORMERS", "false").lower() == "true":
                    LLAMA_MODEL = {
                        "tokenizer": AutoTokenizer.from_pretrained(llama_stack_path),
                        "model": AutoModelForCausalLM.from_pretrained(llama_stack_path)
                    }
                    LLAMA_AVAILABLE = True
                    print(f"Llama 4 model loaded via transformers from llama-stack: {llama_stack_path}")
            except Exception as e:
                print(f"Warning: Could not load llama-stack model from {llama_stack_path}: {e}")
        
        if not LLAMA_AVAILABLE:
            llama_model_name = os.getenv("LLAMA_MODEL_NAME", "meta-llama/Llama-3.2-3B-Instruct")
            try:
                if os.getenv("LOAD_LLAMA_TRANSFORMERS", "false").lower() == "true":
                    LLAMA_MODEL = {
                        "tokenizer": AutoTokenizer.from_pretrained(llama_model_name),
                        "model": AutoModelForCausalLM.from_pretrained(llama_model_name)
                    }
                    LLAMA_AVAILABLE = True
                    print(f"Llama model loaded via transformers: {llama_model_name}")
            except Exception as e:
                print(f"Warning: Could not load Llama via transformers: {e}")
    except ImportError:
        pass

if not LLAMA_AVAILABLE:
    print("Info: No Llama backend detected. Install one of:")
    print("  - Ollama: https://ollama.ai/ (recommended)")
    print("  - llama-cpp-python: pip install llama-cpp-python")
    print("  - transformers: pip install transformers torch")


# ---------------------------------------------------------------------------
# Unit equivalence: same quantity, different units (e.g. m/s and km/h = velocity).
# Used to normalize suggested units and to recognize equivalent units when matching.
# Canonical form is the first in each tuple (prefer SI where sensible).
# ---------------------------------------------------------------------------
UNIT_EQUIVALENCE_GROUPS = [
    # Geometry / Length
    ("mm", "mm", "m", "cm", "µm", "inch", "in", "length", "displacement", "stroke", "gap", "width", "position", "radius"),
    # Linear Motion / Velocity
    ("m/s", "m/s", "km/h", "mm/s", "in/s", "velocity", "speed", "feedrate"),
    # Rotary Motion / Angular Velocity
    ("rpm", "rpm", "rad/s", "1/s", "1/min", "°/s", "rotations per minute", "angular velocity", "rotational speed"),
    # Force
    ("N", "N", "kN", "mN", "lbf", "force", "load", "tension", "feedforce"),
    # Torque
    ("N·m", "N·m", "Nm", "kNm", "lb-ft", "torque", "driving torque", "moment", "drivetorque"),
    # Mass / Weight
    ("kg", "kg", "g", "mg", "t", "lb", "mass", "weight", "payload", "toolmass"),
    # Pressure
    ("bar", "bar", "Pa", "kPa", "MPa", "psi", "pressure", "systempressure", "vacuum"),
    # Electricity - Voltage
    ("V", "V", "kV", "mV", "voltage", "u_nom"),
    # Electricity - Current
    ("A", "A", "mA", "current", "i_peak"),
    # Energy / Power
    ("W", "W", "kW", "mW", "J", "kJ", "kWh", "power", "energy", "consumption", "heatloss", "p_rated"),
    # Thermodynamics / Temperature
    ("°C", "°C", "K", "°F", "temperature", "temp", "ambient", "cooling_t"),
    # Time
    ("s", "s", "ms", "µs", "min", "time", "cycletime", "delay"),
    # Frequency
    ("Hz", "Hz", "kHz", "frequency", "samplingrate"),
    # Flow
    ("l/min", "l/min", "m³/h", "ml/s", "flow", "flowrate", "discharge", "q_max"),
    # Accuracy / Error
    ("%", "%", "percent", "accuracy", "repetition accuracy", "hysteresis", "error"),
    ("µm", "µm", "micrometer", "micrometre", "tolerance"),
    ("arcsec", "arcsec", "arc second", "angular accuracy"),
    # Ratio / Logic (no unit)
    ("NONE", "NONE", "none", "ratio", "gearratio", "status", "count", "pcs", "index"),
]


def normalize_unit_to_canonical(unit: str) -> str:
    """
    Map a unit string to a canonical form from UNIT_EQUIVALENCE_GROUPS.
    If the unit (or its lowercase form) appears in any group, return the canonical (first) unit of that group.
    Otherwise return the original unit stripped.
    
    Prioritizes exact matches and compound units (with /, ·, etc.) over single-letter matches.
    """
    if not unit or not isinstance(unit, str):
        return (unit or "").strip()
    u = unit.strip()
    u_lower = u.lower()
    import re
    
    # Strategy 1: Exact matches (most precise) - check canonical first, then equivalents
    for group in UNIT_EQUIVALENCE_GROUPS:
        canonical = group[0]
        if u == canonical or u_lower == canonical.lower():
            return canonical
        for equiv in group[1:]:
            if u == equiv or u_lower == equiv.lower():
                return canonical
    
    # Strategy 2: Check compound units (contain /, ·, ³, etc.) - prioritize longer matches
    # Sort groups by canonical unit length (longest first) to match "m/s" before "m"
    compound_indicators = ['/', '·', '³', '²', '-', ' ']
    has_compound = any(indicator in u for indicator in compound_indicators)
    
    if has_compound:
        # For compound units, check groups with compound canonical units first
        compound_groups = [g for g in UNIT_EQUIVALENCE_GROUPS if any(ind in g[0] for ind in compound_indicators)]
        [g for g in UNIT_EQUIVALENCE_GROUPS if g not in compound_groups]
        
        # Check compound groups first
        for group in compound_groups:
            canonical = group[0]
            for equiv in group:
                equiv_lower = equiv.lower()
                # Exact match or if unit contains the equivalent as a whole
                if u_lower == equiv_lower or u_lower == equiv_lower.replace('·', '.').replace('·', '*'):
                    return canonical
                # Check if compound unit matches (e.g., "m/s" matches "m/s")
                if '/' in equiv and '/' in u:
                    # Compare parts
                    equiv_parts = [p.strip() for p in equiv_lower.split('/')]
                    u_parts = [p.strip() for p in u_lower.split('/')]
                    if len(equiv_parts) == len(u_parts) and all(ep == up or ep in up or up in ep for ep, up in zip(equiv_parts, u_parts)):
                        return canonical
        
        # If no compound match found, don't try simple groups for compound units
        return u
    
    # Strategy 3: For simple units, try substring matches with word boundaries
    # But prioritize longer matches (e.g., "mm" before "m")
    for group in sorted(UNIT_EQUIVALENCE_GROUPS, key=lambda g: len(g[0]), reverse=True):
        canonical = group[0]
        for equiv in group:
            equiv_lower = equiv.lower()
            # Use word boundaries to avoid false matches
            # But skip if equiv is a substring of a longer unit we've already checked
            pattern = r'\b' + re.escape(equiv_lower) + r'\b'
            if re.search(pattern, u_lower):
                return canonical
    
    return u


def units_are_equivalent(unit_a: str, unit_b: str) -> bool:
    """Return True if both units belong to the same equivalence group (same quantity)."""
    if not unit_a or not unit_b:
        return False
    a = unit_a.strip().lower()
    b = unit_b.strip().lower()
    if a == b:
        return True
    for group in UNIT_EQUIVALENCE_GROUPS:
        members = [g.lower() for g in group]
        if a in members and b in members:
            return True
    return False


class NameNormalizer:
    """
    Normalization layer that expands abbreviations and standardizes names.
    
    This layer implements the normalization function from the pipeline:
    - Expands common abbreviations (e.g., max_v → maximum velocity)
    - Standardizes naming conventions
    - Generates multiple search variants for better matching
    """
    
    def __init__(self, use_gemini: bool = False):
        """
        Initialize the normalizer with abbreviation dictionary.
        
        Args:
            use_gemini: Whether to use Gemini AI for complex abbreviation expansion
        """
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        # Common abbreviation mappings
        self.abbreviations = {
            # Common prefixes/suffixes
            'max': 'maximum',
            'min': 'minimum',
            'avg': 'average',
            'std': 'standard',
            'rms': 'root mean square',
            
            # Units and measurements
            'rpm': 'rotations per minute',
            'v': 'velocity',
            'vel': 'velocity',
            'acc': 'acceleration',
            'f': 'force',
            'fx': 'force x',
            'fy': 'force y',
            'fz': 'force z',
            'torque': 'torque',
            't': 'torque',
            'temp': 'temperature',
            'press': 'pressure',
            'p': 'pressure',
            
            # Technical terms
            'feed': 'feed',
            'stroke': 'stroke',
            'driving': 'driving',
            'load': 'load',
            'no-load': 'no load',
            'accuracy': 'accuracy',
            'rep': 'repetition',
            'repetition': 'repetition',
        }
        # Word separators
        self.separators = ['_', '-', ' ', '']
    
    def expand_abbreviations(self, name: str) -> str:
        """
        Expand abbreviations in a name.
        
        Args:
            name: Original name (e.g., "max_V", "Max_feed_force_Fx")
        
        Returns:
            Expanded name (e.g., "maximum velocity", "maximum feed force x")
        """
        # Normalize to lowercase for processing
        normalized = name.lower()
        # Split by common separators (preserve case info for single letters)
        parts = re.split(r'[_\-\s]+', normalized)
        
        expanded_parts = []
        for part in parts:
            if not part:
                continue
            if len(part) == 1 and part.isalpha():
                if part in self.abbreviations:
                    expanded_parts.append(self.abbreviations[part])
                else:
                    expanded_parts.append(part)
            elif part in self.abbreviations:
                expanded_parts.append(self.abbreviations[part])
            else:
                expanded = self._expand_embedded_abbreviation(part)
                expanded_parts.append(expanded)
        
        return ' '.join(expanded_parts)
    
    def _expand_embedded_abbreviation(self, text: str) -> str:
        """Expand abbreviations embedded in text (e.g., "maxv" → "maximum velocity")."""
        # Common patterns
        patterns = [
            (r'^max(.+)$', r'maximum \1'),
            (r'^min(.+)$', r'minimum \1'),
            (r'^(.+)max$', r'\1 maximum'),
            (r'^(.+)min$', r'\1 minimum'),
        ]
        
        for pattern, replacement in patterns:
            if re.match(pattern, text):
                result = re.sub(pattern, replacement, text)
                # Further expand if result contains known abbreviations
                words = result.split()
                expanded_words = [self.abbreviations.get(w, w) for w in words]
                return ' '.join(expanded_words)
        
        return text
    
    def normalize_name(self, name: str) -> List[str]:
        """
        Normalize a name and return multiple search variants.
        
        This function standardizes names and generates variants for searching:
        1. Original name (normalized)
        2. Expanded abbreviations
        3. Alternative word orders
        
        Args:
            name: Original semantic node name
        
        Returns:
            List of normalized name variants to search
        """
        variants: Set[str] = set()
        
        # Original normalized (lowercase, standardized separators)
        original_norm = name.lower().replace('-', '_').replace(' ', '_')
        variants.add(original_norm)
        
        # Expanded version
        expanded = self.expand_abbreviations(name)
        expanded_norm = expanded.lower().replace('-', '_').replace(' ', '_')
        variants.add(expanded_norm)
        
        # Also add space-separated version for fuzzy matching
        variants.add(expanded.lower().replace('_', ' ').replace('-', ' '))
        variants.add(original_norm.replace('_', ' '))
        
        # Remove empty strings
        variants.discard('')
        
        return list(variants)
    
    def get_search_terms(self, name: str) -> List[str]:
        """
        Get all search terms (original + expanded) for eClass search.
        
        Uses Gemini AI if available and rule-based expansion fails.
        
        Args:
            name: Original name
        
        Returns:
            List of search terms to try
        """
        terms = self.normalize_name(name)
        
        # Also add the expanded full form (space-separated)
        expanded = self.expand_abbreviations(name)
        if expanded != name.lower():
            terms.append(expanded)
            # Add underscore version too for library matching
            terms.append(expanded.replace(' ', '_'))
        elif self.use_gemini:
            # If rule-based expansion didn't work, try Gemini
            gemini_expanded = self._expand_with_gemini(name)
            if gemini_expanded and gemini_expanded != name.lower():
                terms.append(gemini_expanded)
                terms.append(gemini_expanded.replace(' ', '_'))
        
        return terms
    
    def _expand_with_gemini(self, name: str) -> Optional[str]:
        """
        Use Gemini AI to expand abbreviations that rule-based methods couldn't handle.
        
        Args:
            name: Node name with potential abbreviations
        
        Returns:
            Expanded name or None if failed
        """
        if not self.use_gemini:
            return None
        
        try:
            prompt = f"""Expand the following technical abbreviation or short form into its full form.
Return only the expanded form, nothing else.

Example:
Input: max_V
Output: maximum velocity

Input: {name}
Output:"""
            
            text = ""
            if GEMINI_CLIENT:
                try:
                    # Try different model names - newest first
                    model_names = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro", "gemini-1.5-pro"]
                    for model_name in model_names:
                        try:
                            response = GEMINI_CLIENT.models.generate_content(
                                model=model_name,
                                contents=prompt
                            )
                            if response.text:
                                text = response.text.strip()
                                break
                        except Exception as model_error:
                            # Print debug info for troubleshooting
                            print(f"  DEBUG: Model '{model_name}' failed in normalization: {str(model_error)}")
                            continue
                    
                except Exception as e:
                    print(f"  DEBUG: Gemini normalization error: {str(e)}")
            
            # Use google.generativeai package (this is what you have)
            if not text and GEMINI_MODEL:
                try:
                    response = GEMINI_MODEL.generate_content(prompt)
                    # Handle different response formats from google.generativeai
                    if hasattr(response, 'text') and response.text:
                        text = response.text.strip()
                    elif hasattr(response, 'candidates') and response.candidates:
                        if response.candidates[0].content.parts:
                            text = response.candidates[0].content.parts[0].text.strip()
                    else:
                        print(f"  DEBUG: Unexpected response format from google.generativeai")
                except Exception as e:
                    print(f"  DEBUG: google.generativeai model failed: {str(e)}")
            
            if text and text.lower() != name.lower():
                return text
        
        except Exception:
            pass  # Silently fail, fallback to rule-based
        
        return None


def _generic_normalize_name(name: str) -> str:
    """
    Domain-agnostic fallback: split on _/-, expand only universal terms (max, min, avg, std), title-case.
    Does not guess domain (no V→voltage or V→velocity). Works for any domain when Llama is unavailable.
    """
    universal = {'max': 'maximum', 'min': 'minimum', 'avg': 'average', 'std': 'standard'}
    parts = re.split(r'[_\-\s]+', name)
    out = []
    for p in parts:
        if not p:
            continue
        out.append(universal.get(p.lower(), p))
    # Title-case each word; keep single uppercase letters as-is (e.g. V, I)
    result = []
    for w in out:
        if len(w) == 1:
            result.append(w.upper() if w.isalpha() else w)
        else:
            result.append(w.title() if w.islower() else w)
    return ' '.join(result)


def expand_name_with_llama(name: str, context: str = "", path: str = "") -> Optional[str]:
    """
    Use local Llama to expand a technical variable name into a human-readable phrase.
    Context-aware: Same abbreviation (V, P, T, f) can mean different things based on Path.
    Example: max_V in "Actuator/Mechanical/Linear" → "Maximum Velocity" (m/s)
             max_V in "Inverter/Electrical/Output" → "Maximum Voltage" (V)
    
    Args:
        name: Node name (e.g. max_V, avg_P, T_amb, f_op)
        context: Optional context (e.g. Asset: X; Submodel: Y) for domain-aware expansion
        path: Optional path (e.g., "Actuator/Mechanical/Linear") for context-aware disambiguation
    
    Returns:
        Expanded name or None if Llama unavailable/failed
    """
    if not LLAMA_AVAILABLE:
        return None
    
    # Build prompt with path/context for disambiguation
    # Simplified prompt - relies on training data for context-aware disambiguation
    prompt_parts = []
    
    if path and path.strip():
        prompt_parts.append(f"Path: {path.strip()}")
        prompt_parts.append("")
    
    if context and context.strip():
        prompt_parts.append(f"Context: {context.strip()}")
        prompt_parts.append("")
    
    prompt_parts.append(f"Task: Expand this technical variable name into a clear, human-readable phrase.")
    prompt_parts.append("")
    prompt_parts.append("Use the Path/Context to disambiguate abbreviations:")
    prompt_parts.append("- In IndustrialMotor/Electrical: V→Voltage, I→Current, R→Resistance, n→Rotation Speed")
    prompt_parts.append("- In Mechanical/Linear: V→Velocity, n→Rotation Speed")
    prompt_parts.append("- In Electrical contexts: V→Voltage, I→Current, P→Power")
    prompt_parts.append("- In Fluid/Pressure contexts: P→Pressure, f→Flow")
    prompt_parts.append("")
    prompt_parts.append("IMPORTANT: Expand ALL abbreviations fully. Single letters must become full words.")
    prompt_parts.append("Examples: V_nom→Nominal Voltage, n_idle→Idle Rotation Speed, I_peak→Peak Current")
    prompt_parts.append("")
    prompt_parts.append(f"Variable name: {name}")
    prompt_parts.append("Expanded phrase:")
    
    prompt = "\n".join(prompt_parts)
    text = ""
    try:
        if LLAMA_BACKEND == 'ollama':
            import requests
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            model_name = os.getenv("LLAMA_MODEL_NAME", "llama3.2")
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "max_tokens": 100}
                },
                timeout=20
            )
            if response.status_code == 200:
                text = (response.json().get("response") or "").strip()
        elif LLAMA_BACKEND == 'llama_cpp' and LLAMA_MODEL:
            response = LLAMA_MODEL(prompt, max_tokens=100, temperature=0.3, stop=["\n", "Output:"], echo=False)
            if response and response.get('choices'):
                text = (response['choices'][0].get('text') or "").strip()
        # Remove any "Output:" or similar prefix
        if text:
            for prefix in ("Output:", "output:", "Expanded form:", "->"):
                if text.strip().lower().startswith(prefix.lower()):
                    text = text.strip()[len(prefix):].strip()
            text = text.strip()
        
        # Post-process: Only expand single-letter abbreviations if Llama left them (fallback)
        # This is a safety net - ideally Llama should handle this from training
        if text:
            words = text.split()
            expanded_words = []
            for word in words:
                # Only expand if Llama left a single uppercase letter (indicates it didn't expand)
                if len(word) == 1 and word.isupper() and word.isalpha():
                    # Minimal fallback expansion based on path (only if path available)
                    expanded_word = None
                    if path:
                        path_lower = path.lower()
                        # Simple keyword matching as last resort
                        if word == "V" and ("motor" in path_lower or "industrial" in path_lower or "electrical" in path_lower):
                            expanded_word = "Voltage"
                        elif word == "n" and ("motor" in path_lower or "mechanical" in path_lower or "idle" in name.lower()):
                            expanded_word = "Rotation Speed"
                        elif word == "I" and ("motor" in path_lower or "industrial" in path_lower or "electrical" in path_lower):
                            expanded_word = "Current"
                        elif word == "R" and ("motor" in path_lower or "electrical" in path_lower or "phase" in name.lower()):
                            expanded_word = "Resistance"
                    
                    if expanded_word:
                        expanded_words.append(expanded_word)
                    else:
                        # Keep as-is if we can't determine - let user correct if needed
                        expanded_words.append(word)
                else:
                    expanded_words.append(word)
            text = " ".join(expanded_words)
        
        if text and text.lower() != name.lower():
            return text
    except Exception:
        pass
    return None


def _build_path_from_metadata(meta: Dict) -> str:
    """
    Build a path string from metadata (source_asset, source_submodel) for context-aware normalization.
    Example: {"source_asset": "Actuator", "source_submodel": "Mechanical/Linear"} → "Actuator/Mechanical/Linear"
    """
    path_parts = []
    if meta.get("source_asset"):
        path_parts.append(str(meta["source_asset"]))
    if meta.get("source_submodel"):
        submodel = str(meta["source_submodel"])
        # If submodel contains slashes, use as-is; otherwise append
        if "/" in submodel:
            path_parts.append(submodel)
        else:
            path_parts.append(submodel)
    return "/".join(path_parts) if path_parts else ""


def normalize_node_with_llama(node: SemanticNode, normalizer: Optional[NameNormalizer] = None) -> None:
    """
    Normalize a semantic node name: Llama (with path/context) first, then domain-agnostic generic fallback.
    Context-aware: Uses path (asset/submodel) to disambiguate abbreviations (V, P, T, f).
    Stores result in node.metadata["normalized_name"].
    """
    meta = getattr(node, 'metadata', None) or {}
    
    # Build path for context-aware disambiguation
    path = _build_path_from_metadata(meta)
    
    # Build context string
    context_parts = []
    if meta.get("source_asset"):
        context_parts.append(f"Asset: {meta['source_asset']}")
    if meta.get("source_submodel"):
        context_parts.append(f"Submodel: {meta['source_submodel']}")
    context = "; ".join(context_parts)
    
    # Use path-aware expansion
    llama_expanded = expand_name_with_llama(node.name, context=context, path=path)
    if llama_expanded:
        node.metadata["normalized_name"] = llama_expanded
    else:
        # Domain-agnostic fallback: no guessing V/i/n etc.; only universal terms + title-case
        node.metadata["normalized_name"] = _generic_normalize_name(node.name)


def normalize_collection(collection: SemanticNodeCollection, document_library=None, fast_only: bool = False) -> None:
    """
    Normalize all nodes in a collection using document data (if provided) and optionally Ollama.
    Sets metadata['normalized_name'] on each node.
    
    When document_library is provided (e.g. enricher.documents), first tries to get
    a normalization hint from support documents (e.g. "max_V: maximum velocity" -> "maximum velocity").
    If no hint is found:
      - fast_only=True: use generic expansion only (no Ollama) – fast, good for large collections.
      - fast_only=False: use Ollama to expand the name (context-aware) – slow (one Ollama call per node).
    """
    normalizer = NameNormalizer(use_gemini=False) if not fast_only else None
    for node in collection.nodes:
        hint = None
        if document_library and getattr(document_library, "get_normalization_hint", None):
            hint = document_library.get_normalization_hint(node.name)
        if hint:
            if not node.metadata:
                node.metadata = {}
            node.metadata["normalized_name"] = hint
        elif fast_only:
            if not node.metadata:
                node.metadata = {}
            node.metadata["normalized_name"] = _generic_normalize_name(node.name)
        else:
            normalize_node_with_llama(node, normalizer=normalizer)


# eCl@ss CDP Webservice API (https://www.eclass-cdp.com/) - certificate/token required
ECLASS_CDP_AVAILABLE = False


def _resolve_path(raw: str, bases: tuple = ("", "EClass", "EClass/API License", "Data")) -> Optional[str]:
    """Return absolute path if raw is an existing file, or when joined with one of bases."""
    raw = raw.strip()
    if os.path.isfile(raw):
        return os.path.abspath(raw)
    for base in bases:
        path = os.path.join(base, raw) if base else raw
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


def _pem_contains_private_key(path: str) -> bool:
    """Return True if the file contains a private key (PRIVATE KEY or RSA PRIVATE KEY)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return "PRIVATE KEY" in content
    except Exception:
        return False


def _get_eclass_cdp_cert_key() -> tuple:
    """
    Get eCl@ss CDP client certificate and private key paths for TLS client auth.
    - ECLASS_CDP_CERT: path to certificate (.crt, .pem, .cer)
    - ECLASS_CDP_KEY: path to private key (.key, .pem)
    If only KEY is set, look for a cert in the same directory (same base name .crt/.pem or *.full.pem).
    If KEY points to a .pem that contains both cert and private key, use it for both (cert_path=key_path).
    Returns (cert_path, key_path); either can be None.
    """
    cert_raw = os.getenv("ECLASS_CDP_CERT", "").strip()
    key_raw = os.getenv("ECLASS_CDP_KEY", "").strip()
    cert_path = _resolve_path(cert_raw) if cert_raw else None
    key_path = _resolve_path(key_raw) if key_raw else None
    if key_path and not cert_path:
        # Single file: .pem containing both cert and private key
        if key_path.lower().endswith(".pem") and _pem_contains_private_key(key_path):
            cert_path = key_path
            return (cert_path, key_path)
        # Try same directory: same base name with .crt, .pem, .cer; or any .full.pem
        key_dir = os.path.dirname(key_path)
        key_base = os.path.splitext(os.path.basename(key_path))[0]
        for ext in (".crt", ".pem", ".cer"):
            candidate = os.path.join(key_dir, key_base + ext)
            if os.path.isfile(candidate):
                cert_path = os.path.abspath(candidate)
                break
        if not cert_path:
            for name in os.listdir(key_dir or "."):
                if name.endswith(".full.pem") or (name.endswith(".pem") and "full" in name.lower()):
                    cert_path = os.path.abspath(os.path.join(key_dir, name))
                    break
    return (cert_path, key_path)


def _get_eclass_cdp_api_key() -> Optional[str]:
    """
    Get eCl@ss CDP API key/token from environment or from a license file.
    - ECLASS_CDP_API_KEY or ECLASS_CDP_TOKEN: the token string, or path to a file containing the token.
    - If the value looks like a file path and the file exists, the token is read from that file (first line, stripped).
    """
    raw = os.getenv("ECLASS_CDP_API_KEY") or os.getenv("ECLASS_CDP_TOKEN")
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    # If it's a path to an existing file, read token from file
    if os.path.isfile(raw):
        try:
            with open(raw, "r", encoding="utf-8") as f:
                token = f.readline().strip() or f.read().strip()
            return token if token else None
        except Exception:
            return None
    # Check common project paths if raw is a relative path
    for base in ("", "EClass", "EClass/API License", "Data"):
        path = os.path.join(base, raw) if base else raw
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    token = f.readline().strip() or f.read().strip()
                return token if token else None
            except Exception:
                pass
    return raw


def _eclass_cdp_search(name: str, unit: str = "", value_type: str = "") -> Optional[Dict]:
    """
    Query eCl@ss CDP Webservice (JSON API) for a property or class by preferred name.
    Uses ECLASS_CDP_KEY + ECLASS_CDP_CERT (client certificate) or ECLASS_CDP_API_KEY (Bearer token) - see ECLASS_CDP_SETUP.md.
    """
    cert_path, key_path = _get_eclass_cdp_cert_key()
    api_key = _get_eclass_cdp_api_key()
    use_cert = cert_path and key_path
    if not use_cert and not api_key:
        return None
    base = os.getenv("ECLASS_CDP_BASE_URL", "https://www.eclass-cdp.com").rstrip("/")
    url = f"{base}/jsonapi/v2/properties"
    headers = {"Accept": "application/json", "Accept-Language": "en-US"}
    if api_key and not use_cert:
        headers["Authorization"] = f"Bearer {api_key}"
    kwargs = {"headers": headers, "params": {}, "timeout": 15, "allow_redirects": False}
    if use_cert:
        kwargs["cert"] = (cert_path, key_path)
    try:
        import requests
        for param_name in ("search", "preferredName", "q", "name"):
            kwargs["params"] = {param_name: name, "limit": 10}
            resp = requests.get(url, **kwargs)
            if resp.status_code != 200:
                continue
            data = resp.json()
            items = data if isinstance(data, list) else data.get("member", data.get("data", data.get("items", [])))
            if not items:
                continue
            for item in items[:5]:
                if not isinstance(item, dict):
                    continue
                preferred_name = item.get("preferredName") or item.get("name") or item.get("label")
                if isinstance(preferred_name, list):
                    preferred_name = next((x.get("label", "") for x in preferred_name if isinstance(x, dict)), "") if preferred_name else ""
                elif isinstance(preferred_name, dict):
                    preferred_name = preferred_name.get("en-US", preferred_name.get("en", ""))
                definition = item.get("definition") or item.get("description")
                if isinstance(definition, list):
                    definition = next((x.get("label", "") for x in definition if isinstance(x, dict)), "")
                elif isinstance(definition, dict):
                    definition = definition.get("en-US", definition.get("en", ""))
                if not definition and preferred_name:
                    definition = str(preferred_name)
                if definition:
                    return {
                        "definition": definition,
                        "usage": item.get("usage") or f"eCl@ss property: {preferred_name}",
                        "unit": item.get("unit") or item.get("unitCode") or unit,
                        "value_type": item.get("valueType") or item.get("dataType") or value_type,
                        "eclass_id": item.get("irdi") or item.get("id", ""),
                    }
    except Exception as e:
        print(f"  [DEBUG] eCl@ss CDP API search failed: {e}")
    return None


def _irdi_to_path(irdi: str) -> str:
    """Convert eClass IRDI to URL path form: 0173-1#02-AAY070#001 -> 0173-1-02-AAY070-001 (preferred per API doc)."""
    if not irdi or not isinstance(irdi, str):
        return ""
    return irdi.strip().replace("#", "-")


def _is_eclass_cdp_url(value: Any) -> Optional[str]:
    """
    If value is a string URL pointing to eClass CDP (api.eclass-cdp.com or www.eclass-cdp.com), return the URL.
    Otherwise return None. Used to fetch parameter info from API instead of searching local eClass files.
    """
    if not value or not isinstance(value, str):
        return None
    s = value.strip()
    if not s.startswith("http"):
        return None
    s_lower = s.lower()
    if "api.eclass-cdp.com" in s_lower or "www.eclass-cdp.com" in s_lower:
        return s
    return None


def _eclass_cdp_fetch_by_url(url: str) -> Optional[Dict]:
    """
    Fetch eClass parameter info from a full CDP URL (e.g. https://api.eclass-cdp.com/0173-1-02-AAR710-003).
    Uses the same client cert/token as other CDP calls. Parses XML response into definition, unit, value_type.
    Returns None on failure or if URL is not allowed (only api.eclass-cdp.com / www.eclass-cdp.com).
    """
    if not _is_eclass_cdp_url(url):
        return None
    cert_path, key_path = _get_eclass_cdp_cert_key()
    api_key = _get_eclass_cdp_api_key()
    use_cert = cert_path and key_path
    if not use_cert and not api_key:
        return None
    headers = {"Accept": "application/x.eclass.v5+xml", "Accept-Language": "en-US"}
    kwargs = {"headers": headers, "timeout": 15, "allow_redirects": False}
    if use_cert:
        kwargs["cert"] = (cert_path, key_path)
    elif api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        import requests
        resp = requests.get(url, **kwargs)
        if not resp or resp.status_code != 200:
            return None
        text = resp.text
        if not text or "<" not in text:
            return None
        root = ET.fromstring(text)

        def find_text_any(el: ET.Element, *tags: str) -> str:
            for e in el.iter("*"):
                local = (e.tag or "").split("}")[-1]
                if local in tags and e.text and e.text.strip():
                    return e.text.strip()
            return ""

        preferred_name = find_text_any(root, "preferredName", "preferred_name", "name")
        definition = find_text_any(root, "definition", "description")
        if not definition and preferred_name:
            definition = preferred_name
        unit = find_text_any(root, "unit", "unitCode", "unitSymbol", "symbol")
        if not unit:
            for e in root.iter("*"):
                if "unit" in (e.tag or "").lower():
                    if e.text and e.text.strip():
                        unit = e.text.strip()
                        break
                    ref = e.get("unitRef") or e.get("ref")
                    if ref:
                        unit = ref
                        break
        value_type = find_text_any(root, "valueType", "value_type", "dataType", "data_type")
        # IRDI from URL (last path segment: 0173-1-02-AAR710-003 -> 0173-1#02-AAR710#003)
        irdi_from_url = url.rstrip("/").split("/")[-1] if "/" in url else ""
        if irdi_from_url and "#" not in irdi_from_url:
            parts = irdi_from_url.split("-")
            if len(parts) >= 5:
                irdi_from_url = f"{parts[0]}-{parts[1]}#{parts[2]}-{parts[3]}#{parts[4]}"
            elif len(parts) >= 3:
                irdi_from_url = f"{parts[0]}-{parts[1]}#{'-'.join(parts[2:])}"
        if not irdi_from_url:
            irdi_from_url = url
        return {
            "definition": definition or "",
            "usage": f"eCl@ss: {preferred_name}" if preferred_name else "",
            "unit": unit or "",
            "value_type": value_type or "",
            "eclass_id": irdi_from_url,
        }
    except Exception as e:
        print(f"  [DEBUG] eCl@ss CDP fetch by URL failed: {e}")
        return None


def _eclass_cdp_request_get(path: str, accept: str = "application/x.eclass.v5+xml", params: Optional[Dict] = None):
    """Perform GET on eClass CDP with cert or Bearer auth. Returns requests.Response or None."""
    cert_path, key_path = _get_eclass_cdp_cert_key()
    api_key = _get_eclass_cdp_api_key()
    use_cert = cert_path and key_path
    if not use_cert and not api_key:
        return None
    base = os.getenv("ECLASS_CDP_BASE_URL", "https://www.eclass-cdp.com").rstrip("/")
    url = f"{base}{path}" if path.startswith("/") else f"{base}/{path}"
    headers = {"Accept": accept, "Accept-Language": "en-US"}
    if api_key and not use_cert:
        headers["Authorization"] = f"Bearer {api_key}"
    kwargs = {"headers": headers, "timeout": 15}
    if params:
        kwargs["params"] = params
    if use_cert:
        kwargs["cert"] = (cert_path, key_path)
    kwargs["allow_redirects"] = False  # do not follow redirects to portal/seam/... URLs
    try:
        import requests
        return requests.get(url, **kwargs)
    except Exception as e:
        print(f"  [DEBUG] eCl@ss CDP request failed: {e}")
        return None


def _eclass_cdp_get_property_xml(irdi: str) -> Optional[Dict]:
    """
    GET /xmlapi/v2/properties/{irdi} (eClass CDP XML Read Service).
    Returns dict with definition, unit, value_type, eclass_id or None.
    """
    path_irdi = _irdi_to_path(irdi)
    if not path_irdi:
        return None
    resp = _eclass_cdp_request_get(f"/xmlapi/v2/properties/{path_irdi}")
    if not resp or resp.status_code != 200:
        return None
    text = resp.text
    if not text or "<" not in text:
        return None
    try:
        root = ET.fromstring(text)

        def find_text_any(el: ET.Element, *tags: str) -> str:
            for e in el.iter("*"):
                local = (e.tag or "").split("}")[-1]
                if local in tags and e.text and e.text.strip():
                    return e.text.strip()
            return ""

        preferred_name = find_text_any(root, "preferredName", "preferred_name", "name")
        definition = find_text_any(root, "definition", "description")
        if not definition and preferred_name:
            definition = preferred_name
        # Unit: often ref by IRDI or symbol
        unit = find_text_any(root, "unit", "unitCode", "unitSymbol", "symbol")
        if not unit:
            for e in root.iter("*"):
                if "unit" in (e.tag or "").lower():
                    if e.text and e.text.strip():
                        unit = e.text.strip()
                        break
                    ref = e.get("unitRef") or e.get("unitRef") or e.get("ref")
                    if ref:
                        unit = ref
                        break
        value_type = find_text_any(root, "valueType", "value_type", "dataType", "data_type")
        return {
            "definition": definition or "",
            "usage": f"eCl@ss property: {preferred_name}" if preferred_name else "",
            "unit": unit or "",
            "value_type": value_type or "",
            "eclass_id": irdi,
        }
    except Exception as e:
        print(f"  [DEBUG] eCl@ss CDP property XML parse failed: {e}")
        return None


def get_eclass_description_by_irdi(irdi: str) -> Optional[Dict]:
    """
    Get the description (and unit, value type) for a parameter by its eClass IRDI.
    Uses CDP API (certificate or token must be set via ECLASS_CDP_KEY or ECLASS_CDP_API_KEY).
    When base URL is api.eclass-cdp.com: uses direct path only (base/irdi), never portal paths.
    When base is www.eclass-cdp.com: tries xmlapi/v2/properties then direct.
    Redirects are not followed, so we never hit portal/seam/resource/rest/dictionary/...
    """
    if not irdi or not isinstance(irdi, str):
        return None
    irdi = irdi.strip()
    if "#" not in irdi and "-" in irdi:
        parts = irdi.split("-")
        if len(parts) >= 5:
            irdi = f"{parts[0]}-{parts[1]}#{parts[2]}-{parts[3]}#{parts[4]}"
    base = os.getenv("ECLASS_CDP_BASE_URL", "https://www.eclass-cdp.com").rstrip("/")
    path_irdi = _irdi_to_path(irdi)
    # api.eclass-cdp.com: use direct path only (no /xmlapi/... so we never get redirected to portal)
    if "api.eclass-cdp.com" in base.lower():
        if path_irdi:
            url = f"{base}/{path_irdi}"
            if _is_eclass_cdp_url(url):
                result = _eclass_cdp_fetch_by_url(url)
                if result:
                    return result
        return None
    # www.eclass-cdp.com or other: try xmlapi then direct
    result = _eclass_cdp_get_property_xml(irdi)
    if result:
        return result
    if path_irdi:
        url = f"{base}/{path_irdi}"
        if _is_eclass_cdp_url(url):
            result = _eclass_cdp_fetch_by_url(url)
            if result:
                return result
    return None


def _eclass_cdp_get_unit_xml(irdi: str) -> Optional[str]:
    """
    GET /xmlapi/v2/units/{irdi} (eClass CDP XML Read Service).
    Returns unit symbol/code string or None.
    """
    path_irdi = _irdi_to_path(irdi)
    if not path_irdi:
        return None
    resp = _eclass_cdp_request_get(f"/xmlapi/v2/units/{path_irdi}")
    if not resp or resp.status_code != 200:
        return None
    text = resp.text
    if not text or "<" not in text:
        return None
    try:
        root = ET.fromstring(text)
        for e in root.iter("*"):
            local = (e.tag or "").split("}")[-1]
            if local in ("symbol", "unitSymbol", "code", "preferredName") and e.text and e.text.strip():
                return e.text.strip()
        return None
    except Exception:
        return None


class EClassLibrary:
    """
    eCl@ss library interface for semantic enrichment.
    
    Uses local library and/or eCl@ss CDP Webservice (https://www.eclass-cdp.com/)
    when ECLASS_CDP_API_KEY is set (certificate/token from ECLASS Shop).
    """
    
    def __init__(self, library_file: Optional[str] = None, eclass_folder: Optional[str] = None, lazy_load: bool = False):
        """
        Initialize eCl@ss library. Enables CDP API if ECLASS_CDP_API_KEY is set.
        """
        self.library = {}
        self.normalizer = NameNormalizer()
        self.eclass_folder = eclass_folder if eclass_folder else "EClass"
        self.library_file = library_file
        self.lazy_load = lazy_load
        self._folder_loaded = False
        
        self.load_builtin_library()
        
        # Auto-load XML files from EClass folder if it exists (unless lazy_load)
        if not lazy_load and os.path.exists(self.eclass_folder):
            self._load_eclass_folder(self.eclass_folder)
            self._folder_loaded = True
        
        # Load custom library file if provided
        if library_file:
            self.load_library_file(library_file)
        
        _cert, _key = _get_eclass_cdp_cert_key()
        self.use_cdp_api = bool(_get_eclass_cdp_api_key()) or bool(_cert and _key)
        if self.use_cdp_api:
            globals()["ECLASS_CDP_AVAILABLE"] = True
            print("  [INFO] eCl@ss CDP Webservice API enabled")
    
    def _ensure_folder_loaded(self):
        """Ensure EClass folder is loaded (for lazy loading)."""
        if not self._folder_loaded and os.path.exists(self.eclass_folder):
            self._load_eclass_folder(self.eclass_folder)
            self._folder_loaded = True
    
    def load_builtin_library(self):
        """Load built-in eCl@ss definitions for common terms."""
        # Built-in library with common industrial terms
        self.library = {
            # Temperature related
            "temperature": {
                "definition": "Physical quantity expressing the degree of heat or cold of an object or environment",
                "usage": "Used for monitoring, control, and documentation of thermal conditions in processes",
                "unit": "°C, K, °F",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV232#001"
            },
            "process_temperature": {
                "definition": "Temperature at which a manufacturing or treatment process operates",
                "usage": "Critical parameter for quality control and process optimization",
                "unit": "°C, K",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV235#001"
            },
            "ambient_temperature": {
                "definition": "Temperature of the surrounding environment",
                "usage": "Environmental monitoring and equipment operation conditions",
                "unit": "°C, K",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV233#001"
            },
            
            # Pressure related
            "pressure": {
                "definition": "Force per unit area applied in a perpendicular direction to the surface of an object",
                "usage": "Critical parameter for fluid systems, pneumatic and hydraulic systems",
                "unit": "bar, Pa, psi",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV470#001"
            },
            "operating_pressure": {
                "definition": "Pressure at which a system or component normally operates",
                "usage": "Safety and performance monitoring of pressurized systems",
                "unit": "bar, Pa",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV471#001"
            },
            
            # Speed/Velocity
            "speed": {
                "definition": "Rate of motion or operation measured in distance per time or revolutions per time",
                "usage": "Motor control, conveyor systems, and process timing",
                "unit": "rpm, m/s, Hz",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV534#001"
            },
            "rotational_speed": {
                "definition": "Number of complete rotations per unit time",
                "usage": "Motor and drive system monitoring and control",
                "unit": "rpm, rad/s",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV535#001"
            },
            
            # Weight/Mass
            "weight": {
                "definition": "Force exerted on an object due to gravity, proportional to mass",
                "usage": "Product specification, logistics, and quality control",
                "unit": "kg, g, t",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV320#001"
            },
            "mass": {
                "definition": "Quantity of matter in an object, independent of gravity",
                "usage": "Material requirements, shipping, and inventory management",
                "unit": "kg, g",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV321#001"
            },
            
            # Dimensions
            "length": {
                "definition": "Linear extent in space from one end to the other",
                "usage": "Product specification, layout planning, and compatibility checking",
                "unit": "mm, m, cm",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV270#001"
            },
            "width": {
                "definition": "Measurement or extent from side to side",
                "usage": "Dimensional specification for products and components",
                "unit": "mm, m",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV271#001"
            },
            "height": {
                "definition": "Measurement from base to top or from bottom to top",
                "usage": "Spatial planning and product specification",
                "unit": "mm, m",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV272#001"
            },
            
            # Electrical
            "voltage": {
                "definition": "Electrical potential difference between two points",
                "usage": "Electrical system specification and power supply requirements",
                "unit": "V, kV, mV",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV201#001"
            },
            "current": {
                "definition": "Rate of flow of electric charge",
                "usage": "Electrical load monitoring and circuit protection",
                "unit": "A, mA",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV202#001"
            },
            "power": {
                "definition": "Rate at which energy is transferred or converted",
                "usage": "Energy consumption and system capacity specification",
                "unit": "W, kW, MW",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV210#001"
            },
            
            # Identification
            "serial_number": {
                "definition": "Unique identifier assigned to an individual unit for tracking purposes",
                "usage": "Asset tracking, warranty management, and traceability",
                "unit": "",
                "value_type": "String",
                "eclass_id": "0173-1#02-AAO057#001"
            },
            "manufacturer": {
                "definition": "Company or entity that produces the product or component",
                "usage": "Supply chain management and product identification",
                "unit": "",
                "value_type": "String",
                "eclass_id": "0173-1#02-AAO677#001"
            },
            "manufacturer_name": {
                "definition": "Name of the company or entity that manufactures the item",
                "usage": "Product documentation and procurement",
                "unit": "",
                "value_type": "String",
                "eclass_id": "0173-1#02-AAO677#001"
            },
            "model_number": {
                "definition": "Identifier assigned by manufacturer to distinguish product variants",
                "usage": "Product specification and ordering",
                "unit": "",
                "value_type": "String",
                "eclass_id": "0173-1#02-AAO056#001"
            },
            
            # Time
            "cycle_time": {
                "definition": "Time required to complete one cycle of an operation",
                "usage": "Production planning and throughput calculation",
                "unit": "s, min, h",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV620#001"
            },
            "processing_time": {
                "definition": "Duration required to complete a processing operation",
                "usage": "Production scheduling and capacity planning",
                "unit": "s, min, h",
                "value_type": "Float",
                "eclass_id": "0173-1#02-AAV621#001"
            }
        }
    
    def load_library_file(self, filepath: str):
        """
        Load additional eCl@ss definitions from file.

        Supports:
        - JSON files in the existing expected format
        - ECLASS ADVANCED XML dictionary files (e.g. ECLASS15_0_ADVANCED_EN_SG_13.xml)
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".xml":
            loaded = self._load_eclass_xml(filepath)
            self.library.update(loaded)
            print(f"Loaded {len(loaded)} additional eCl@ss definitions from XML")
            return

        # Fallback: JSON (original behaviour)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                additional_library = json.load(f)
                self.library.update(additional_library)
                print(f"Loaded {len(additional_library)} additional eCl@ss definitions")
        except Exception as e:
            print(f"Warning: Could not load eCl@ss library file: {e}")

    def _load_eclass_xml(self, filepath: str) -> Dict[str, Dict]:
        """
        Load eCl@ss definitions directly from an ADVANCED XML dictionary file.

        This implementation extracts:
        - preferred_name/label  -> used as the key (normalized)
        - definition/text       -> definition
        - class id attribute    -> eclass_id
        - preferred_unit/unit    -> unit (if available)
        - preferred_data_type/data_type -> value_type (if available)

        Units and value types are extracted when available to improve matching confidence.
        """
        ns = {
            "dic": "urn:eclass:xml-schema:dictionary:5.0",
            "ontoml": "urn:iso:std:iso:is:13584:-32:ed-1:tech:xml-schema:ontoml",
        }

        library: Dict[str, Dict] = {}

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Classes are under: dic:eclass_dictionary/ontoml:ontoml/dictionary/contained_classes/ontoml:class
            for cls in root.findall(".//ontoml:class", ns):
                class_id = cls.get("id", "").strip()

                # Preferred name label
                pref_name_el = cls.find(".//preferred_name/label", ns)
                name = ""
                if pref_name_el is not None and pref_name_el.text:
                    name = pref_name_el.text.strip()
                if not name:
                    # Skip unnamed entries
                    continue

                # Definition text
                def_el = cls.find(".//definition/text", ns)
                definition = ""
                if def_el is not None and def_el.text:
                    definition = def_el.text.strip()

                # Extract unit from eClass XML
                # Units can be in various places: preferred_unit, unit, or unit_of_measure
                unit = ""
                unit_el = cls.find(".//preferred_unit", ns)
                if unit_el is None:
                    unit_el = cls.find(".//unit", ns)
                if unit_el is None:
                    unit_el = cls.find(".//unit_of_measure", ns)
                if unit_el is not None:
                    # Try to get unit text or label
                    unit_text = unit_el.text
                    if not unit_text:
                        unit_label = unit_el.find(".//label", ns)
                        if unit_label is not None and unit_label.text:
                            unit_text = unit_label.text
                    if unit_text:
                        unit = unit_text.strip()

                # Extract value type (data type) from eClass XML
                # Data types can be in: preferred_data_type, data_type, or value_type
                value_type = ""
                type_el = cls.find(".//preferred_data_type", ns)
                if type_el is None:
                    type_el = cls.find(".//data_type", ns)
                if type_el is None:
                    type_el = cls.find(".//value_type", ns)
                if type_el is not None:
                    type_text = type_el.text
                    if not type_text:
                        type_label = type_el.find(".//label", ns)
                        if type_label is not None and type_label.text:
                            type_text = type_label.text
                    if type_text:
                        value_type = type_text.strip()

                # Build normalized key similar to built‑in entries
                key = name.lower().replace(" ", "_").replace("-", "_")

                # Basic usage text
                usage = f"Class '{name}' from eCl@ss ADVANCED XML dictionary"

                entry: Dict[str, str] = {
                    "definition": definition or f"eCl@ss class {class_id}",
                    "usage": usage,
                }
                if class_id:
                    entry["eclass_id"] = class_id
                if unit:
                    entry["unit"] = unit
                if value_type:
                    entry["value_type"] = value_type

                library[key] = entry

        except Exception as e:
            print(f"Warning: Could not parse eCl@ss XML file '{filepath}': {e}")

        return library
    
    def _get_cache_path(self, folder_path: str) -> str:
        """Get the path to the cache file for the ECLASS folder."""
        folder_hash = hashlib.md5(folder_path.encode()).hexdigest()[:8]
        cache_dir = os.path.join(os.path.dirname(folder_path) if folder_path != "EClass" else ".", ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"eclass_library_{folder_hash}.pkl")
    
    def _get_source_files_mtime(self, folder_path: str) -> float:
        """Get the maximum modification time of all XML dictionary files."""
        if not os.path.exists(folder_path):
            return 0
        
        max_mtime = 0
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.lower().endswith(".xml") and ('ECLASS' in file_name.upper() or 'SG_' in file_name or 'dictionary' in root.lower()):
                    filepath = os.path.join(root, file_name)
                    try:
                        mtime = os.path.getmtime(filepath)
                        max_mtime = max(max_mtime, mtime)
                    except OSError:
                        continue
        
        return max_mtime
    
    def _load_from_cache(self, cache_path: str, folder_path: str) -> Optional[Dict]:
        """Load library from cache if it exists and is valid."""
        if not os.path.exists(cache_path):
            return None
        
        try:
            # Load from cache without checking modification time
            # Cache is always used if it exists (user preference for performance)
            with open(cache_path, 'rb') as f:
                cached_library = pickle.load(f)
                print(f"  [CACHE] Loaded eCl@ss library from cache ({len(cached_library)} entries)")
                return cached_library
        except Exception as e:
            print(f"  [WARNING] Could not load eCl@ss library cache: {e}")
            return None
    
    def _save_to_cache(self, cache_path: str, library: Dict):
        """Save library to cache."""
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(library, f)
            print(f"  [CACHE] Saved eCl@ss library to cache ({len(library)} entries)")
        except Exception as e:
            print(f"  [WARNING] Could not save eCl@ss library cache: {e}")
    
    def _load_eclass_folder(self, folder_path: str):
        """
        Automatically load all eCl@ss XML dictionary files from a folder.
        
        Uses pickle caching to speed up subsequent loads.
        Recursively searches for XML files in subdirectories and loads them.
        
        Args:
            folder_path: Path to folder containing eCl@ss XML files
        """
        # Try to load from cache first
        cache_path = self._get_cache_path(folder_path)
        cached_library = self._load_from_cache(cache_path, folder_path)
        
        if cached_library:
            self.library.update(cached_library)
            return
        
        # Cache miss or invalid - load from files
        xml_files = []
        
        # Recursively find all XML files
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.xml'):
                    # Look for ECLASS dictionary files (typically contain "ECLASS" or "SG_" in name)
                    if 'ECLASS' in file.upper() or 'SG_' in file or 'dictionary' in root.lower():
                        xml_files.append(os.path.join(root, file))
        
        if not xml_files:
            print(f"No eCl@ss XML files found in {folder_path}")
            return
        
        print(f"Found {len(xml_files)} eCl@ss XML file(s) in {folder_path}")
        print(f"  [INFO] Loading from source files (this may take a minute)...")
        
        total_loaded = 0
        for i, xml_file in enumerate(xml_files):
            try:
                loaded = self._load_eclass_xml(xml_file)
                if loaded:
                    self.library.update(loaded)
                    total_loaded += len(loaded)
                    # Only print every 10th file or last file to reduce output
                    if (i + 1) % 10 == 0 or i == len(xml_files) - 1:
                        print(f"  Progress: {i+1}/{len(xml_files)} files, {total_loaded} definitions loaded...")
            except Exception as e:
                print(f"  [WARNING] Could not load {os.path.basename(xml_file)}: {e}")
        
        if total_loaded > 0:
            print(f"  [OK] Total: {total_loaded} eCl@ss definitions loaded")
            # Save to cache for next time
            self._save_to_cache(cache_path, self.library)
    
    def _search_property_in_xml(self, property_id: str, field: str = "unit") -> Optional[str]:
        """
        Search for a specific property ID in eClass XML files and extract unit or value_type.
        
        Args:
            property_id: eClass property ID (e.g., "0173-1#02-AAO740#002")
            field: Field to extract ("unit" or "value_type")
        
        Returns:
            Extracted value or None if not found
        """
        ns = {
            "dic": "urn:eclass:xml-schema:dictionary:5.0",
            "ontoml": "urn:iso:std:iso:is:13584:-32:ed-1:tech:xml-schema:ontoml",
        }
        
        # Search in the eClass folder
        eclass_folder = "EClass"
        if not os.path.exists(eclass_folder):
            return None
        
        # Find all XML files
        xml_files = []
        for root, dirs, files in os.walk(eclass_folder):
            for file in files:
                if file.lower().endswith('.xml') and ('ADVANCED' in file or 'BASIC' in file or 'Dictionary' in file):
                    xml_files.append(os.path.join(root, file))
        
        # Search each XML file for the property
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Find property with matching ID
                property_elem = root.find(f".//ontoml:property[@id='{property_id}']", ns)
                if property_elem is not None:
                    if field == "unit":
                        # Look for unit in domain/referred_type or preferred_unit
                        unit_elem = property_elem.find(".//preferred_unit", ns)
                        if unit_elem is None:
                            unit_elem = property_elem.find(".//unit", ns)
                        if unit_elem is not None:
                            unit_text = unit_elem.text
                            if not unit_text:
                                unit_label = unit_elem.find(".//label", ns)
                                if unit_label is not None and unit_label.text:
                                    unit_text = unit_label.text
                            if unit_text:
                                return unit_text.strip()
                    
                    elif field == "value_type":
                        # Look for data type in domain
                        domain = property_elem.find(".//domain", ns)
                        if domain is not None:
                            # Check domain type attribute
                            domain_type = domain.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
                            if "REAL_TYPE" in domain_type or "FLOAT_TYPE" in domain_type:
                                return "Float"
                            elif "INT_TYPE" in domain_type or "INTEGER_TYPE" in domain_type:
                                return "Integer"
                            elif "STRING_TYPE" in domain_type or "TRANSLATABLE_STRING_TYPE" in domain_type:
                                return "String"
                            elif "BOOLEAN_TYPE" in domain_type or "BOOL_TYPE" in domain_type:
                                return "Boolean"
            except Exception:
                # Continue searching other files
                continue
        
        return None
    
    def _calculate_similarity(self, search_key: str, library_key: str) -> float:
        """
        Calculate similarity score between search key and library key.
        
        Returns a score between 0.0 and 1.0 (1.0 = exact match, 0.0 = no match).
        """
        # Exact match
        if search_key == library_key:
            return 1.0
        
        # Word-based similarity
        search_words = set(search_key.replace('_', ' ').split())
        library_words = set(library_key.replace('_', ' ').split())
        
        if not search_words or not library_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(search_words & library_words)
        union = len(search_words | library_words)
        jaccard = intersection / union if union > 0 else 0.0
        
        # Bonus for substring match
        if search_key in library_key or library_key in search_key:
            jaccard = max(jaccard, 0.8)
        
        return jaccard
    
    def search_top_k(self, name: str, unit: str = "", value_type: str = "", k: int = 10, threshold: float = 0.9) -> List[Tuple[Dict, float]]:
        """
        Search for top-K matches in eCl@ss library with similarity scoring.
        
        Uses normalization layer to expand abbreviations before searching.
        Returns top K matches above the similarity threshold.
        
        Args:
            name: Node name (e.g., "max_V")
            unit: Measurement unit
            value_type: Data type
            k: Number of top matches to return (default: 10)
            threshold: Minimum similarity score (0.0-1.0, default: 0.9)
        
        Returns:
            List of tuples (entry_dict, similarity_score) sorted by score descending
        """
        # Lazy load folder if needed
        self._ensure_folder_loaded()
        
        # Get normalized search terms (original + expanded)
        search_terms = self.normalizer.get_search_terms(name)
        
        candidates: List[Tuple[Dict, float]] = []
        seen_keys: Set[str] = set()
        
        # Try each search term variant
        for search_term in search_terms:
            # Normalize to library key format
            search_key = search_term.lower().replace(" ", "_").replace("-", "_")
            
            # Search through all library entries
            for key, entry in self.library.items():
                # Skip if already processed
                if key in seen_keys:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(search_key, key)
                
                # Apply unit/value_type matching bonus
                if self._matches_criteria(entry, unit, value_type):
                    similarity = min(1.0, similarity + 0.1)  # Small bonus for unit/type match
                
                # Only consider matches above threshold
                if similarity >= threshold:
                    candidates.append((entry, similarity))
                    seen_keys.add(key)
        
        # Sort by similarity (descending) and return top K
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:k]
    
    def search(self, name: str, unit: str = "", value_type: str = "", context: str = "", enricher=None, skip_cdp_api: bool = False) -> Optional[Dict]:
        """
        Search for semantic node definition in eCl@ss library.
        
        Uses normalization layer to expand abbreviations before searching.
        Uses LLM for context-aware matching when available (e.g., "capacity" as volume vs charge).
        
        This method uses top-K search and returns the best match above 90% threshold.
        If multiple candidates exist, uses LLM to select the best match based on context.
        
        Args:
            name: Node name (e.g., "max_V")
            unit: Measurement unit
            value_type: Data type
            context: Optional context string for LLM understanding
            enricher: Optional SemanticNodeEnricher instance for LLM matching
            skip_cdp_api: If True, do not call eClass CDP API (e.g. when description is already available)
        
        Returns:
            Dictionary with definition and usage, or None if not found
        """
        # If eCl@ss CDP API is configured, try API first (unless skip_cdp_api e.g. description already available)
        if self.use_cdp_api and not skip_cdp_api:
            api_result = _eclass_cdp_search(name, unit=unit, value_type=value_type)
            if api_result:
                return api_result
        
        # Use top-K search with lower threshold to get more candidates for LLM selection
        top_matches = self.search_top_k(name, unit, value_type, k=10, threshold=0.7)
        
        if not top_matches:
            return None
        
        # If we have context and LLM available, use intelligent matching
        if context and enricher and LLAMA_AVAILABLE and len(top_matches) > 1:
            # Create a temporary node for context-aware matching
            from semantic_node_enhanced import SemanticNode
            temp_node = SemanticNode(name=name, unit=unit, value_type=value_type)
            best_match = enricher._understand_semantic_meaning(temp_node, top_matches)
            if best_match:
                return best_match
        
        # Fallback: Return the best match (highest similarity)
        return top_matches[0][0]
    
    def _fuzzy_match(self, search_key: str, library_key: str) -> bool:
        """Check if search key fuzzy matches library key."""
        # Simple fuzzy matching - can be enhanced
        search_words = set(search_key.split('_'))
        library_words = set(library_key.split('_'))
        
        # Check if at least 50% of words match
        if len(search_words) == 0:
            return False
        
        matches = len(search_words & library_words)
        return matches / len(search_words) >= 0.5
    
    def _matches_criteria(self, entry: Dict, unit: str, value_type: str) -> bool:
        """Check if entry matches search criteria."""
        if unit and "unit" in entry:
            if unit.lower() not in entry["unit"].lower():
                return False
        
        if value_type and "value_type" in entry:
            if value_type.lower() != entry["value_type"].lower():
                return False
        
        return True


# IEC Smart-enabled API (OAuth2) - for IEC CDD when approved by IEC
IEC_CDD_API_AVAILABLE = False
IEC_CDD_API_CLIENT = None

def _get_iec_cdd_api_client():
    """Build IEC CDD API client if credentials are set (OAuth2 or single API key)."""
    global IEC_CDD_API_CLIENT
    if IEC_CDD_API_CLIENT is not None:
        return IEC_CDD_API_CLIENT
    # Option A: Single API key (Bearer token) - use as-is
    api_key = os.getenv("IEC_CDD_API_KEY") or os.getenv("IEC_SMART_API_KEY")
    if api_key and api_key.strip():
        import time
        IEC_CDD_API_CLIENT = {
            "token": api_key.strip(),
            "expires_at": time.time() + 86400,  # assume 24h
            "client_id": None,
            "client_secret": None
        }
        print("  [INFO] IEC CDD API (API key) initialized")
        return IEC_CDD_API_CLIENT
    # Option B: OAuth2 with client_id and client_secret (after IEC approval)
    client_id = os.getenv("IEC_CDD_CLIENT_ID") or os.getenv("IEC_SMART_CLIENT_ID")
    client_secret = os.getenv("IEC_CDD_CLIENT_SECRET") or os.getenv("IEC_SMART_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    try:
        import requests
        resp = requests.post(
            "https://auth.smart.iec.ch/realms/iec/protocol/openid-connect/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "openid"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        if resp.status_code != 200:
            print(f"  [WARNING] IEC CDD API token request failed: {resp.status_code}")
            return None
        data = resp.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in", 300)
        if not token:
            return None
        IEC_CDD_API_CLIENT = {
            "token": token,
            "expires_at": (importlib.import_module("time").time() + max(0, expires_in - 60)),
            "client_id": client_id,
            "client_secret": client_secret
        }
        print("  [INFO] IEC CDD API (OAuth2) initialized successfully")
        return IEC_CDD_API_CLIENT
    except Exception as e:
        print(f"  [WARNING] IEC CDD API init failed: {e}")
        return None


def _iec_cdd_api_get_bearer_token():
    """Return valid Bearer token for IEC API; refresh if expired."""
    import time
    global IEC_CDD_API_CLIENT
    client = IEC_CDD_API_CLIENT
    if client and time.time() < client.get("expires_at", 0):
        return client.get("token")
    if client and time.time() >= client.get("expires_at", 0):
        IEC_CDD_API_CLIENT = None
    client = _get_iec_cdd_api_client()
    return client.get("token") if client else None


def _iec_cdd_api_search(name: str, unit: str = "", value_type: str = "") -> Optional[Dict]:
    """
    Query IEC Smart-enabled API for a concept matching the given name.
    Uses standards/dictionary endpoint if available; returns dict with definition, usage, unit, value_type, irdi.
    """
    token = _iec_cdd_api_get_bearer_token()
    if not token:
        return None
    base = os.getenv("IEC_CDD_API_BASE_URL", "https://sim-apim.azure-api.net/preprod/v1")
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/ld+json"
        }
        # Try standards list with search-like params; API may support search or filter
        url = f"{base}/standards"
        params = {"limit": 20, "offset": 0}
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        # Map API response to our format; structure may be list of standards or graph
        items = data if isinstance(data, list) else data.get("member", data.get("items", []))
        if not items:
            return None
        # Use first relevant item that has text matching name, or first item
        name_lower = name.lower()
        for item in items[:10]:
            if not isinstance(item, dict):
                continue
            label = (item.get("preferredName") or item.get("name") or item.get("label") or item.get("title") or "")
            if isinstance(label, dict):
                label = label.get("en", label.get("@value", ""))
            if name_lower in str(label).lower() or (name_lower.replace("_", " ") in str(label).lower()):
                definition = item.get("definition") or item.get("description") or ""
                if isinstance(definition, dict):
                    definition = definition.get("en", definition.get("@value", ""))
                usage = item.get("usage") or item.get("scope") or ""
                if isinstance(usage, dict):
                    usage = usage.get("en", usage.get("@value", ""))
                irdi = item.get("irdi") or item.get("id") or item.get("identifier") or ""
                u = item.get("unit") or item.get("unitCode") or unit
                vt = item.get("valueType") or item.get("dataType") or value_type
                return {
                    "definition": definition or str(label),
                    "usage": usage or f"From IEC CDD: {label}",
                    "irdi": irdi,
                    "unit": u,
                    "value_type": vt
                }
        # No name match: use first item if it has definition
        for item in items[:3]:
            if not isinstance(item, dict):
                continue
            definition = item.get("definition") or item.get("description")
            if definition:
                if isinstance(definition, dict):
                    definition = definition.get("en", definition.get("@value", ""))
                label = (item.get("preferredName") or item.get("name") or item.get("label") or "")
                if isinstance(label, dict):
                    label = label.get("en", label.get("@value", ""))
                return {
                    "definition": definition,
                    "usage": item.get("usage") or f"From IEC CDD: {label}",
                    "irdi": item.get("irdi") or item.get("id", ""),
                    "unit": item.get("unit") or unit,
                    "value_type": item.get("valueType") or value_type
                }
    except Exception as e:
        print(f"  [DEBUG] IEC CDD API search failed: {e}")
    return None


class IECCDDLibrary:
    """
    IEC CDD (IEC 61360 Common Data Dictionary) interface.
    
    Uses local library and/or IEC Smart-enabled API (OAuth2) when
    IEC_CDD_CLIENT_ID and IEC_CDD_CLIENT_SECRET are set (after IEC approval).
    """
    
    def __init__(self, library_file: Optional[str] = None):
        """Initialize IEC CDD library. Enables API if IEC_CDD_CLIENT_ID + IEC_CDD_CLIENT_SECRET are set."""
        self.library = {}
        self.normalizer = NameNormalizer()
        self.load_builtin_library()
        
        if library_file:
            self.load_library_file(library_file)
        
        self.use_api = _get_iec_cdd_api_client() is not None
    
    def load_builtin_library(self):
        """Load built-in IEC CDD definitions."""
        self.library = {
            # Process parameters
            "temperature": {
                "definition": "Thermodynamic property representing the average kinetic energy of particles",
                "usage": "Measurement and control of thermal states in systems and processes",
                "irdi": "0112/2///61360_4#UAA123",
                "unit": "°C, K",
                "value_type": "Real"
            },
            "pressure": {
                "definition": "Force exerted per unit area on a surface",
                "usage": "Monitoring and control of fluid and gas systems",
                "irdi": "0112/2///61360_4#UAA456",
                "unit": "Pa, bar",
                "value_type": "Real"
            },
            
            # Electrical properties
            "rated_voltage": {
                "definition": "Voltage value assigned for a specified operating condition",
                "usage": "Electrical equipment specification and selection",
                "irdi": "0112/2///61360_4#UAA789",
                "unit": "V",
                "value_type": "Real"
            },
            "rated_current": {
                "definition": "Current value assigned for a specified operating condition",
                "usage": "Electrical system design and protection",
                "irdi": "0112/2///61360_4#UAA790",
                "unit": "A",
                "value_type": "Real"
            },
            
            # Mechanical properties
            "nominal_speed": {
                "definition": "Speed value specified for normal operation",
                "usage": "Motor and drive system specification",
                "irdi": "0112/2///61360_4#UAA345",
                "unit": "rpm, rad/s",
                "value_type": "Real"
            },
            "torque": {
                "definition": "Rotational force that produces or tends to produce rotation",
                "usage": "Drive system specification and performance monitoring",
                "irdi": "0112/2///61360_4#UAA346",
                "unit": "Nm",
                "value_type": "Real"
            }
        }
    
    def load_library_file(self, filepath: str):
        """Load additional IEC CDD definitions from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                additional_library = json.load(f)
                self.library.update(additional_library)
                print(f"Loaded {len(additional_library)} additional IEC CDD definitions")
        except Exception as e:
            print(f"Warning: Could not load IEC CDD library file: {e}")
    
    def _calculate_similarity(self, search_key: str, library_key: str) -> float:
        """
        Calculate similarity score between search key and library key.
        
        Returns a score between 0.0 and 1.0 (1.0 = exact match, 0.0 = no match).
        """
        # Exact match
        if search_key == library_key:
            return 1.0
        
        # Word-based similarity
        search_words = set(search_key.replace('_', ' ').split())
        library_words = set(library_key.replace('_', ' ').split())
        
        if not search_words or not library_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(search_words & library_words)
        union = len(search_words | library_words)
        jaccard = intersection / union if union > 0 else 0.0
        
        # Bonus for substring match
        if search_key in library_key or library_key in search_key:
            jaccard = max(jaccard, 0.8)
        
        return jaccard
    
    def search_top_k(self, name: str, unit: str = "", value_type: str = "", k: int = 10, threshold: float = 0.9) -> List[Tuple[Dict, float]]:
        """
        Search for top-K matches in IEC CDD library with similarity scoring.
        
        Uses normalization layer to expand abbreviations before searching.
        Returns top K matches above the similarity threshold.
        
        Args:
            name: Node name (e.g., "max_V")
            unit: Measurement unit
            value_type: Data type
            k: Number of top matches to return (default: 10)
            threshold: Minimum similarity score (0.0-1.0, default: 0.9)
        
        Returns:
            List of tuples (entry_dict, similarity_score) sorted by score descending
        """
        # Get normalized search terms (original + expanded)
        search_terms = self.normalizer.get_search_terms(name)
        
        candidates: List[Tuple[Dict, float]] = []
        seen_keys: Set[str] = set()
        
        # Try each search term variant
        for search_term in search_terms:
            # Normalize to library key format
            search_key = search_term.lower().replace(" ", "_").replace("-", "_")
            
            # Search through all library entries
            for key, entry in self.library.items():
                # Skip if already processed
                if key in seen_keys:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(search_key, key)
                
                # Apply unit/value_type matching bonus
                if self._matches_criteria(entry, unit, value_type):
                    similarity = min(1.0, similarity + 0.1)  # Small bonus for unit/type match
                
                # Only consider matches above threshold
                if similarity >= threshold:
                    candidates.append((entry, similarity))
                    seen_keys.add(key)
        
        # Sort by similarity (descending) and return top K
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:k]
    
    def search(self, name: str, unit: str = "", value_type: str = "", context: str = "", enricher=None) -> Optional[Dict]:
        """
        Search for definition in IEC CDD library.
        
        Uses normalization layer and top-K search with 90% threshold.
        Uses LLM for context-aware matching when available.
        
        Args:
            name: Node name (e.g., "max_V")
            unit: Measurement unit
            value_type: Data type
            context: Optional context string for LLM understanding
            enricher: Optional SemanticNodeEnricher instance for LLM matching
        
        Returns:
            Dictionary with definition and usage, or None if not found
        """
        # If IEC Smart API (OAuth2) is configured, try API first
        if self.use_api:
            api_result = _iec_cdd_api_search(name, unit=unit, value_type=value_type)
            if api_result:
                return api_result
        
        # Use top-K search with lower threshold to get more candidates for LLM selection
        top_matches = self.search_top_k(name, unit, value_type, k=10, threshold=0.7)
        
        if not top_matches:
            return None
        
        # If we have context and LLM available, use intelligent matching
        if context and enricher and LLAMA_AVAILABLE and len(top_matches) > 1:
            # Create a temporary node for context-aware matching
            from semantic_node_enhanced import SemanticNode
            temp_node = SemanticNode(name=name, unit=unit, value_type=value_type)
            best_match = enricher._understand_semantic_meaning(temp_node, top_matches)
            if best_match:
                return best_match
        
        # Fallback: Return the best match (highest similarity)
        return top_matches[0][0]
    
    def _matches_criteria(self, entry: Dict, unit: str, value_type: str) -> bool:
        """Check if entry matches search criteria."""
        if unit and "unit" in entry:
            if unit.lower() not in entry["unit"].lower():
                return False
        
        if value_type and "value_type" in entry:
            if value_type.lower() != entry["value_type"].lower():
                return False
        
        return True
    
    def _fuzzy_match(self, search_key: str, library_key: str) -> bool:
        """Check if search key fuzzy matches library key."""
        search_words = set(search_key.split('_'))
        library_words = set(library_key.split('_'))
        
        if len(search_words) == 0:
            return False
        
        matches = len(search_words & library_words)
        return matches / len(search_words) >= 0.5


class DocumentLibrary:
    """
    Document library interface for semantic enrichment from support files.
    
    Reads documents from support_files folder and searches for relevant
    information about semantic nodes.
    """
    
    def __init__(self, support_folder: Optional[str] = "support_files", support_urls: Optional[List[str]] = None):
        """
        Initialize document library.
        
        Args:
            support_folder: Path to folder containing support documents (default "support_files" if None)
            support_urls: Optional list of URLs to fetch HTML content from
        """
        self.support_folder = support_folder if support_folder is not None else "support_files"
        self.support_urls = support_urls or []
        self.documents = {}
        self.normalizer = NameNormalizer()
        self.load_documents()
    
    def load_documents(self):
        """Load all documents from support_files folder and URLs."""
        # Load from local folder
        folder = self.support_folder or "support_files"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            folder,
            os.path.join(base_dir, folder),
            os.path.join(base_dir, "Data", folder),
            os.path.join(base_dir, "data", folder),
        ]
        
        chosen = None
        for path in candidates:
            if os.path.exists(path):
                chosen = path
                break
        
        file_count = 0
        
        if chosen:
            self.support_folder = chosen
            print(f"  [INFO] Loading support documents from: {self.support_folder}")
            
            for filename in os.listdir(self.support_folder):
                filepath = os.path.join(self.support_folder, filename)
                if os.path.isfile(filepath):
                    try:
                        content = self._read_document(filepath)
                        if content:
                            self.documents[filename] = content
                            file_count += 1
                            print(f"    [OK] Loaded: {filename} ({len(content)} characters)")
                    except Exception as e:
                        print(f"    [WARNING] Could not read document {filename}: {e}")
        else:
            print(f"  [INFO] Support folder not found: {self.support_folder}")
            print(f"  [INFO] Tried: {candidates}")
        
        # Load from URLs
        if self.support_urls:
            print(f"  [INFO] Loading support documents from {len(self.support_urls)} URL(s)...")
            for url in self.support_urls:
                try:
                    content = self._fetch_url_content(url)
                    if content:
                        # Use URL as key (sanitized)
                        url_key = url.replace("://", "_").replace("/", "_").replace(":", "_")[:100]
                        self.documents[f"url_{url_key}"] = content
                        file_count += 1
                        print(f"    [OK] Loaded from URL: {url[:80]}... ({len(content)} characters)")
                except Exception as e:
                    print(f"    [WARNING] Could not fetch URL {url}: {e}")
        
        if file_count > 0:
            print(f"  [OK] Loaded {file_count} support document(s)")
        else:
            print(f"  [WARNING] No documents loaded")
    
    def _fetch_url_content(self, url: str) -> str:
        """
        Fetch HTML content from a URL and extract text.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Extracted text content from the HTML page
        """
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            # Use the same HTML parsing logic as local files
            return self._parse_html_content(html_content)
        except Exception as e:
            print(f"    [ERROR] Failed to fetch URL {url}: {e}")
            return ""
    
    def _parse_html_content(self, html_content: str) -> str:
        """
        Parse HTML content and extract text, removing tags.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Extracted text content
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            return text
        except ImportError:
            # Fallback: use regex to strip HTML tags if BeautifulSoup not available
            import re
            # Remove script and style tags
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html_content)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def _read_document(self, filepath: str) -> str:
        """
        Read document content based on file type.
        
        Supports multiple formats flexibly:
        - Text files (.txt, .text)
        - HTML files (.html, .htm) - extracts text content, strips HTML tags
        - JSON files (.json) - extracts text from values
        - Markdown files (.md, .markdown)
        - PDF files (.pdf) - requires PyPDF2
        - Word documents (.docx, .doc) - requires python-docx
        - CSV files (.csv) - converts to text
        - YAML files (.yaml, .yml) - converts to text
        - Unknown formats - tries to read as text
        """
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if ext in ['.txt', '.text']:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif ext in ['.html', '.htm']:
                # Read HTML and extract text content
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                return self._parse_html_content(html_content)
            
            elif ext == '.json':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    # Try to extract meaningful text from JSON
                    return self._extract_text_from_json(data)
            
            elif ext in ['.md', '.markdown']:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif ext == '.pdf':
                # Try to read PDF if PyPDF2 is available
                try:
                    import PyPDF2
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        return text
                except ImportError:
                    print(f"Warning: PyPDF2 not installed. Cannot read PDF: {filepath}")
                    return ""
                except Exception as e:
                    print(f"Warning: Error reading PDF {filepath}: {e}")
                    return ""
            
            elif ext in ['.docx', '.doc']:
                # Try to read DOCX if python-docx is available
                try:
                    from docx import Document
                    doc = Document(filepath)
                    return "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    print(f"Warning: python-docx not installed. Cannot read DOCX: {filepath}")
                    return ""
                except Exception as e:
                    print(f"Warning: Error reading DOCX {filepath}: {e}")
                    return ""
            
            elif ext == '.csv':
                # Read CSV and convert to text
                try:
                    import csv
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        reader = csv.reader(f)
                        lines = []
                        for row in reader:
                            lines.append(' | '.join(row))
                        return '\n'.join(lines)
                except Exception as e:
                    print(f"Warning: Error reading CSV {filepath}: {e}")
                    return ""
            
            elif ext in ['.yaml', '.yml']:
                # Try to read YAML
                try:
                    import yaml
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        data = yaml.safe_load(f)
                        return self._extract_text_from_json(data)  # YAML is similar to JSON
                except ImportError:
                    # Fallback: read as text
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except Exception as e:
                    print(f"Warning: Error reading YAML {filepath}: {e}")
                    return ""
            
            else:
                # Unknown extension - try to read as text (flexible for user files)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except Exception:
                    return ""
        
        except Exception as e:
            print(f"Warning: Error reading file {filepath}: {e}")
            return ""
    
    def _extract_text_from_json(self, data: Any, max_depth: int = 10) -> str:
        """
        Extract meaningful text from JSON structure.
        
        Recursively extracts string values and keys that might contain descriptions.
        Handles various JSON structures flexibly.
        """
        if max_depth <= 0:
            return ""
        
        text_parts = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Include key if it looks like a description field
                if any(desc_word in key.lower() for desc_word in ['description', 'definition', 'text', 'content', 'name', 'label']):
                    if isinstance(value, str) and value.strip():
                        text_parts.append(f"{key}: {value}")
                    elif isinstance(value, (dict, list)):
                        text_parts.append(f"{key}: {self._extract_text_from_json(value, max_depth - 1)}")
                elif isinstance(value, str) and len(value) > 10:  # Include longer strings
                    text_parts.append(value)
                elif isinstance(value, (dict, list)):
                    text_parts.append(self._extract_text_from_json(value, max_depth - 1))
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and len(item) > 10:
                    text_parts.append(item)
                elif isinstance(item, (dict, list)):
                    text_parts.append(self._extract_text_from_json(item, max_depth - 1))
        
        elif isinstance(data, str) and len(data) > 5:
            text_parts.append(data)
        
        return '\n'.join(text_parts)
    
    def get_normalization_hint(self, name: str) -> Optional[str]:
        """
        Get a normalization/expansion hint for a name from support documents.
        Looks for patterns like "name: expansion" or "name - expansion" and returns
        the expansion part. Used by normalize_collection to use document data for normalization.
        """
        if not name or not self.documents:
            return None
        name_variations = [name, name.lower(), name.upper(), name.title(), name.replace('_', ' '), name.replace('-', ' ')]
        separators = [':', '-', '—', '–', '|', '=']
        for filename, content in self.documents.items():
            content_lower = content.lower()
            for nv in name_variations:
                for sep in separators:
                    pattern = f"{nv}{sep}"
                    idx = content_lower.find(pattern.lower())
                    if idx == -1:
                        continue
                    after = content[idx + len(pattern):].strip()
                    if not after:
                        continue
                    first_line = after.split('\n')[0].strip()
                    if len(first_line) > 1 and len(first_line) < 200:
                        return first_line
        return None
    
    @staticmethod
    def _camel_case_to_readable(name: str) -> List[str]:
        """Convert CamelCase to space-separated forms so 'NumberOfWorkers' matches 'Number of workers' in docs."""
        if not name or len(name) < 2:
            return []
        import re
        spaced = re.sub(r'([a-z\d])([A-Z])', r'\1 \2', name)
        spaced = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', spaced)
        if spaced == name:
            return []
        words = spaced.split()
        if not words:
            return []
        lower = ' '.join(w.lower() for w in words)
        title = ' '.join(w.capitalize() for w in words)
        sentence = words[0].capitalize() + ' ' + ' '.join(w.lower() for w in words[1:]) if len(words) > 1 else words[0].capitalize()
        return [lower, title, sentence]
    
    def search(self, name: str, unit: str = "", value_type: str = "", context: str = "", name_variants: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Search for semantic node information in support documents.
        
        Searches using both the given name and any name_variants so that descriptions
        can be found whether the user stored them under the original name (e.g. max_V)
        or the normalized name (e.g. maximum velocity).
        
        Uses normalization layer to expand abbreviations before searching.
        Uses LLM for intelligent context-aware search when available.
        Supports formats like "Name: Description" or "Name - Description".
        
        Args:
            name: Primary node name (e.g., normalized "maximum velocity" or original "max_V")
            unit: Measurement unit
            value_type: Data type
            context: Optional context string for LLM understanding
            name_variants: Optional list of alternate names to search for (e.g. [original "max_V"]
                          when name is normalized). Ensures match whether doc uses "max_V" or "maximum velocity".
        
        Returns:
            Dictionary with definition and usage, or None if not found
        """
        # Collect all names to try: primary name + variants (original, normalized, etc.)
        all_names = [name]
        if name_variants:
            for v in name_variants:
                if v and v.strip() and v.strip() not in all_names:
                    all_names.append(v.strip())
        
        # Get normalized search terms for each name and merge (no duplicates)
        search_terms = []
        seen = set()
        for n in all_names:
            for term in self.normalizer.get_search_terms(n):
                if term.lower() not in seen:
                    search_terms.append(term)
                    seen.add(term.lower())
            expanded = self.normalizer.expand_abbreviations(n)
            if expanded and expanded.lower() not in seen and expanded != n.lower():
                search_terms.append(expanded)
                seen.add(expanded.lower())
            # CamelCase -> "Word word word" so e.g. NumberOfWorkers matches "Number of workers" in SimVSM docs
            for readable in self._camel_case_to_readable(n):
                if readable and readable.lower() not in seen:
                    search_terms.append(readable)
                    seen.add(readable.lower())
        
        # Add each name and its case variants
        for n in all_names:
            search_terms.append(n)
            search_terms.append(n.lower())
            if n.upper() not in seen:
                search_terms.append(n.upper())
            if n.title() not in seen:
                search_terms.append(n.title())
        
        # Deduplicate while preserving order
        search_terms = list(dict.fromkeys([t for t in search_terms if t]))
        
        best_match = None
        best_score = 0
        
        # Debug: Check if documents are loaded
        if len(self.documents) == 0:
            print(f"    [DEBUG] No documents loaded in DocumentLibrary")
            return None
        
        for filename, content in self.documents.items():
            content_lower = content.lower()
            
            # Calculate relevance score for all search terms
            score = 0
            matched_term = None
            
            # First, try to find structured patterns (Name: Description, Name - Description, etc.)
            # Check ALL name variants (original + normalized + case forms + CamelCase readable)
            name_variations = []
            for n in all_names:
                name_variations.extend([n, n.lower(), n.upper(), n.title()])
                name_variations.extend(self._camel_case_to_readable(n))
            name_variations = list(dict.fromkeys([v for v in name_variations if v]))
            
            # Try different separators: :, -, —, |, etc.
            separators = [':', '-', '—', '–', '|', '=']
            
            for name_var in name_variations:
                for sep in separators:
                    pattern = f"{name_var}{sep}"
                    pattern_lower = pattern.lower()
                    
                    if pattern_lower in content_lower:
                        # Found structured pattern - extract description
                        score = 100  # High score for exact pattern match
                        matched_term = pattern
                        break
                
                if score > 0:
                    break
            
            # If not found with original name, try search terms
            if score == 0:
                for search_term in search_terms:
                    for sep in separators:
                        pattern = f"{search_term}{sep}"
                        pattern_lower = pattern.lower()
                        
                        if pattern_lower in content_lower:
                            # Found structured pattern
                            score = 100
                            matched_term = pattern
                            break
                    
                    if score > 0:
                        break
            
            # If no "Name:" pattern found, try general content search
            if score == 0:
                for search_term in search_terms:
                    search_lower = search_term.lower()
                    
                    # Exact match gets highest score
                    if search_lower in content_lower:
                        score += 15
                        matched_term = search_term
                    # Word-based match
                    elif any(word in content_lower for word in search_lower.split() if len(word) > 2):
                        score += 10
                        if not matched_term:
                            matched_term = search_term
            
            # Check for unit matches
            if unit and unit.lower() in content_lower:
                score += 5
            
            # Check for value type matches
            if value_type and value_type.lower() in content_lower:
                score += 3
            
            # Extract context around matches
            if score > 0:
                context = ""
                
                # If we found structured pattern (Name: Description, Name - Description, etc.)
                if matched_term and any(sep in matched_term for sep in [':', '-', '—', '–', '|', '=']):
                    context = self._extract_description_after_colon(content, matched_term)
                
                # If no structured pattern match, try general context extraction
                if not context:
                    # Try each name variant for context extraction (original, normalized, etc.)
                    for try_name in all_names + search_terms[:5]:
                        if not try_name or len(str(try_name)) < 2:
                            continue
                        context = self._extract_context(content, try_name, unit)
                        if context:
                            break
                    # Also try searching for name at start of line (common in lists)
                    if not context:
                        context = self._extract_line_based_context(content, name, search_terms)
                
                if context:
                    if score > best_score:
                        best_match = {
                            "definition": context,
                            "usage": f"Information extracted from {filename}",
                            "source_file": filename
                        }
                        best_score = score
        
        # If no match found with traditional search, try LLM-enhanced search
        if not best_match and LLAMA_AVAILABLE and context:
            best_match = self._llm_search_documents(name, unit, value_type, context, alternate_names=all_names)
        
        # Debug output
        if best_match:
            print(f"    [DEBUG] Found match in {best_match.get('source_file', 'documents')} with score {best_score}")
        elif len(self.documents) > 0:
            print(f"    [DEBUG] No match found in support documents (searched {len(self.documents)} files)")
        
        return best_match if best_score > 0 or best_match else None
    
    def _llm_search_documents(self, name: str, unit: str, value_type: str, context: str, alternate_names: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Use LLM to intelligently search support documents for semantic node information.
        
        Args:
            name: Primary node name
            unit: Measurement unit
            value_type: Data type
            context: Context information about the node
            alternate_names: Other names the property might have in docs (e.g. original "max_V" and normalized "maximum velocity")
        
        Returns:
            Dictionary with definition and usage, or None if not found
        """
        if not LLAMA_AVAILABLE:
            return None
        
        try:
            # Build prompt for LLM to search documents
            doc_summaries = []
            for filename, content in list(self.documents.items())[:5]:  # Limit to 5 docs for prompt size
                # Get first 1000 chars of each document
                summary = content[:1000].replace('\n', ' ').strip()
                doc_summaries.append(f"Document '{filename}':\n{summary}...")
            
            names_hint = ""
            if alternate_names and len(alternate_names) > 1:
                names_hint = f"\nThe property may appear under any of these names in the documents: {', '.join(alternate_names)}. Search for all of them."
            
            prompt = f"""Search the following documents to find information about a semantic property.

Property to find:
Name: {name}
Unit: {unit if unit else 'N/A'}
Value Type: {value_type if value_type else 'N/A'}
Context: {context if context else 'No additional context'}
{names_hint}

Documents to search:
{chr(10).join(doc_summaries)}

Task: Find the definition and usage description for this property considering the context.
The property might be named differently in the documents (e.g. "max_V" or "maximum velocity"; "capacity" could mean volume, charge, or occupancy). Search for the name and any alternate names above.

If found, respond in this format:
DEFINITION: [definition text]
USAGE: [usage text]
SOURCE: [document filename]

If not found, respond with:
NOT_FOUND

Response:"""
            
            text = ""
            
            # Use Ollama
            if LLAMA_BACKEND == 'ollama':
                import requests
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                model_name = os.getenv("LLAMA_MODEL_NAME", "llama3.2")
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "max_tokens": 300
                        }
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "").strip()
            
            # Parse LLM response
            if text and "NOT_FOUND" not in text.upper():
                definition = ""
                usage = ""
                source_file = ""
                
                if "DEFINITION:" in text:
                    parts = text.split("DEFINITION:")
                    if len(parts) > 1:
                        definition_part = parts[1].split("USAGE:")[0].split("SOURCE:")[0].strip()
                        definition = definition_part
                
                if "USAGE:" in text:
                    parts = text.split("USAGE:")
                    if len(parts) > 1:
                        usage_part = parts[1].split("SOURCE:")[0].strip()
                        usage = usage_part
                
                if "SOURCE:" in text:
                    parts = text.split("SOURCE:")
                    if len(parts) > 1:
                        source_file = parts[1].strip().split('\n')[0].strip()
                
                if definition:
                    return {
                        "definition": definition,
                        "usage": usage or f"Information about {name}",
                        "source_file": source_file or "support_documents"
                    }
        
        except Exception as e:
            print(f"  [DEBUG] LLM document search failed: {e}")
        
        return None
    
    def _extract_description_after_colon(self, content: str, pattern: str) -> str:
        """
        Extract description that comes after various patterns.
        
        Handles multiple formats:
        - "Name: Description"
        - "Name - Description"
        - "Name Description" (on same line)
        - "Name\nDescription" (on next line)
        - JSON format: {"name": "Description"}
        - Markdown: ## Name\nDescription
        
        Args:
            content: Full document content
            pattern: Pattern to search for (e.g., "max_V:" or "max_v:")
        
        Returns:
            Extracted description text
        """
        # Remove separators from pattern for matching
        pattern_base = pattern.rstrip(':-').strip()
        
        # Try different name variations (case-insensitive)
        name_variations = [
            pattern_base,
            pattern_base.lower(),
            pattern_base.upper(),
            pattern_base.title(),
            pattern_base.replace('_', ''),
            pattern_base.replace('_', ' '),
            pattern_base.replace('-', ''),
            pattern_base.replace('-', ' '),
        ]
        
        lines = content.split('\n')
        
        for name_var in name_variations:
            # Pattern 1: "Name: Description" or "Name - Description"
            separators = [':', '-', '—', '–', '|']
            for sep in separators:
                search_pattern = f"{name_var}{sep}"
                search_pattern_lower = search_pattern.lower()
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    
                    if search_pattern_lower in line_lower:
                        # Find the separator position (case-insensitive)
                        sep_idx = line_lower.find(search_pattern_lower)
                        if sep_idx >= 0:
                            # Extract text after separator
                            description = line[sep_idx + len(search_pattern):].strip()
                            if description:
                                return description
                            
                            # If nothing after separator, check next line
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                if next_line and not any(next_line.lower().startswith(v.lower() + sep) for v in name_variations for sep in separators):
                                    return next_line
            
            # Pattern 2: "Name Description" (on same line, space-separated)
            search_pattern = f"{name_var} "
            search_pattern_lower = search_pattern.lower()
            
            for line in lines:
                line_lower = line.lower()
                if line_lower.startswith(search_pattern_lower):
                    # Extract text after name
                    description = line[len(search_pattern):].strip()
                    if description and len(description) > 5:  # Must have meaningful content
                        return description
            
            # Pattern 3: Name on one line, description on next line
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped.lower() == name_var.lower():
                    # Check next few lines for description
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith('#') and len(next_line) > 10:
                            return next_line
        
        return ""
    
    def _extract_context(self, content: str, name: str, unit: str = "") -> str:
        """Extract relevant context around search terms."""
        # Find sentences containing the name
        sentences = re.split(r'[.!?]+', content)
        relevant_sentences = []
        
        name_lower = name.lower()
        for sentence in sentences:
            if name_lower in sentence.lower():
                # Clean up sentence
                sentence = sentence.strip()
                if len(sentence) > 20 and len(sentence) < 500:
                    relevant_sentences.append(sentence)
        
        if relevant_sentences:
            # Return first 2-3 relevant sentences
            return " ".join(relevant_sentences[:3])
        
        return ""
    
    def _extract_line_based_context(self, content: str, name: str, search_terms: List[str]) -> str:
        """
        Extract context when name appears at start of line (common in lists, definitions).
        
        Handles formats like:
        - "Name\n  Description text"
        - "Name\nDescription text"
        - Bullet points, numbered lists, etc.
        """
        lines = content.split('\n')
        name_variations = [name, name.lower(), name.upper(), name.title()]
        name_variations.extend(search_terms)
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if line starts with any name variation
            for name_var in name_variations:
                if line_stripped.lower().startswith(name_var.lower()):
                    # Check if there's description on the same line after the name
                    if len(line_stripped) > len(name_var) + 5:
                        # Extract description from same line
                        description = line_stripped[len(name_var):].strip()
                        # Remove leading separators
                        description = re.sub(r'^[:\-\|—–\s]+', '', description)
                        if description:
                            return description
                    
                    # Check next few lines for description
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j].strip()
                        # Skip empty lines, headers, and other names
                        if (next_line and 
                            len(next_line) > 10 and 
                            not next_line.startswith('#') and
                            not any(next_line.lower().startswith(v.lower()) for v in name_variations if v != name_var)):
                            return next_line
        
        return ""


class GeminiEnricher:
    """
    Uses Gemini API to generate descriptions for semantic nodes
    when no enrichment is found from libraries or documents.
    """
    
    def __init__(self, use_gemini: bool = True):
        """
        Initialize Gemini enricher.
        
        Args:
            use_gemini: Whether to use Gemini API
        """
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        self.generated_count = 0
    
    def generate_description(self, node: SemanticNode) -> Optional[Dict]:
        """
        Generate description using Gemini API.
        
        Args:
            node: Semantic node to generate description for
        
        Returns:
            Dictionary with generated definition and usage, or None if failed
        """
        if not self.use_gemini or not GEMINI_AVAILABLE:
            return None
        
        try:
            # Build prompt for Gemini
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

            text = ""
            
            # Try new API first (google-genai package - official)
            if GEMINI_CLIENT:
                try:
                    # Try different model names - newest first
                    model_names = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro", "gemini-1.5-pro"]
                    
                    for model_name in model_names:
                        try:
                            # CORRECT: Always generate content via the client, not a model object
                            response = GEMINI_CLIENT.models.generate_content(
                                model=model_name,
                                contents=prompt
                            )
                            # Check if text exists (handling safety blocks)
                            if response.text:
                                text = response.text
                                break  # Success, exit loop
                        except Exception as model_error:
                            # PRINT THE ERROR so we know what's wrong
                            print(f"  DEBUG: Model '{model_name}' failed: {str(model_error)}")
                            continue
                    
                    if not text:
                        raise Exception("All model name attempts failed")
                            
                except Exception as e:
                    print(f"Warning: Gemini API call failed: {e}")
                    return None
            
            # Use google.generativeai package (this is what you have)
            if not text and GEMINI_MODEL:
                try:
                    response = GEMINI_MODEL.generate_content(prompt)
                    # Handle different response formats from google.generativeai
                    if hasattr(response, 'text') and response.text:
                        text = response.text
                    elif hasattr(response, 'candidates') and response.candidates:
                        # Sometimes text is in candidates[0].content.parts[0].text
                        if response.candidates and response.candidates[0].content.parts:
                            text = response.candidates[0].content.parts[0].text
                    else:
                        print("  DEBUG: Response received but no text found in expected locations")
                        return None
                except Exception as e:
                    print(f"Warning: Gemini model generation failed: {e}")
                    print(f"  DEBUG: Full error details: {str(e)}")
                    return None
            
            if not text:
                return None
            
            # Parse response
            definition = ""
            usage = ""
            
            if "DEFINITION:" in text:
                parts = text.split("DEFINITION:")
                if len(parts) > 1:
                    definition_part = parts[1].split("USAGE:")[0].strip()
                    definition = definition_part
            
            if "USAGE:" in text:
                parts = text.split("USAGE:")
                if len(parts) > 1:
                    usage = parts[1].strip()
            
            # Fallback: if parsing failed, use first paragraph as definition
            if not definition and text:
                lines = text.split('\n')
                definition = lines[0].strip() if lines else text[:200]
            
            if definition:
                self.generated_count += 1
                return {
                    "definition": definition,
                    "usage": usage or f"Generated description for {node.name}",
                    "source": "gemini"
                }
        
        except Exception as e:
            print(f"Warning: Gemini description generation failed: {e}")
        
        return None


class OpenAIEnricher:
    """
    Uses OpenAI API to generate descriptions for semantic nodes
    when no enrichment is found from support files or libraries.
    Used when OPENAI_API_KEY is set.
    """
    
    def __init__(self, use_openai: bool = True):
        """
        Initialize OpenAI enricher.
        
        Args:
            use_openai: Whether to use OpenAI API (when key is available)
        """
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.generated_count = 0
    
    def generate_description(self, node: SemanticNode, context: str = "") -> Optional[Dict]:
        """
        Generate description using OpenAI API.
        
        Args:
            node: Semantic node to generate description for
            context: Optional context (e.g. asset/submodel, related nodes) for accurate descriptions
        
        Returns:
            Dictionary with generated definition and usage, or None if failed
        """
        if not self.use_openai or not OPENAI_AVAILABLE or not OPENAI_CLIENT:
            return None
        
        try:
            context_block = ""
            if context and context.strip():
                context_block = f"\nContext (use this to generate an accurate, domain-specific description):\n{context.strip()}\n"
            prompt = f"""Generate a concise technical definition and usage description for the following semantic node:{context_block}

Name: {node.name}
Value Type: {node.value_type}
Unit: {node.unit if node.unit else 'N/A'}
Current Value: {node.value if node.value else 'N/A'}

Provide:
1. A clear, technical definition (1-2 sentences) that fits the given context (e.g. industrial motor technical data)
2. A brief usage description explaining when/why this data would be used

Format your response as:
DEFINITION: [definition text]
USAGE: [usage text]"""

            # Try OPENAI_MODEL first; then fallbacks (default: gpt-5-mini)
            model = os.getenv("OPENAI_MODEL", "").strip()
            fallbacks = ["gpt-5-mini", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
            models_to_try = ([model] + [m for m in fallbacks if m != model]) if model else fallbacks

            text = ""
            last_error = None
            for try_model in models_to_try:
                try:
                    response = OPENAI_CLIENT.chat.completions.create(
                        model=try_model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=300,
                        temperature=0.7
                    )
                    if response.choices and len(response.choices) > 0:
                        choice = response.choices[0]
                        if choice.message and choice.message.content:
                            text = choice.message.content.strip()
                    if text:
                        break
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    if "403" in err_str or "model_not_found" in err_str or "does not have access" in err_str:
                        continue  # try next model
                    if "max_tokens" in err_str or "max_completion_tokens" in err_str:
                        # Older API: try max_tokens instead
                        try:
                            response = OPENAI_CLIENT.chat.completions.create(
                                model=try_model,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=300,
                                temperature=0.7
                            )
                            if response.choices and len(response.choices) > 0:
                                choice = response.choices[0]
                                if choice.message and choice.message.content:
                                    text = choice.message.content.strip()
                            if text:
                                break
                        except Exception:
                            pass
                        continue
                    raise

            if not text:
                if last_error:
                    print(f"Warning: OpenAI description generation failed: {last_error}")
                return None

            definition = ""
            usage = ""
            if "DEFINITION:" in text:
                parts = text.split("DEFINITION:")
                if len(parts) > 1:
                    definition_part = parts[1].split("USAGE:")[0].strip()
                    definition = definition_part
            if "USAGE:" in text:
                parts = text.split("USAGE:")
                if len(parts) > 1:
                    usage = parts[1].strip()
            if not definition and text:
                lines = text.split('\n')
                definition = lines[0].strip() if lines else text[:200]
            
            if definition:
                self.generated_count += 1
                return {
                    "definition": definition,
                    "usage": usage or f"Generated description for {node.name}",
                    "source": "openai"
                }
        except Exception as e:
            print(f"Warning: OpenAI description generation failed: {e}")
        return None


class LlamaEnricher:
    """
    Uses Llama for local reasoning to generate descriptions for semantic nodes
    when no enrichment is found from libraries or documents.
    
    Supports Ollama backend for local deployment (privacy-focused).
    """
    
    def __init__(self, use_llama: bool = True, model_name: Optional[str] = None):
        """
        Initialize Llama enricher.
        
        Args:
            use_llama: Whether to use Llama for local reasoning
            model_name: Model name for Ollama (e.g., "llama3.2", "llama3.1", "mistral")
                       If None, uses LLAMA_MODEL_NAME env var or defaults to "llama3.2"
        """
        self.use_llama = use_llama and LLAMA_AVAILABLE
        self.backend = LLAMA_BACKEND
        self.model_name = model_name or os.getenv("LLAMA_MODEL_NAME", "llama3.2")
        self.generated_count = 0
        
        if self.use_llama:
            print(f"Llama enricher initialized with backend: {self.backend}")
            if self.backend == 'ollama':
                print(f"  Using Ollama model: {self.model_name}")
    
    def generate_description(self, node: SemanticNode) -> Optional[Dict]:
        """
        Generate description using local Llama model.
        
        Args:
            node: Semantic node to generate description for
        
        Returns:
            Dictionary with generated definition and usage, or None if failed
        """
        if not self.use_llama or not LLAMA_AVAILABLE:
            return None
        
        try:
            # Build prompt for Llama
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

            text = ""
            
            # Try Ollama backend
            if self.backend == 'ollama':
                try:
                    import requests
                    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                    response = requests.post(
                        f"{ollama_url}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "max_tokens": 300
                            }
                        },
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        text = result.get("response", "").strip()
                except Exception as e:
                    print(f"Warning: Ollama API call failed: {e}")
                    return None
            
            # Try llama-cpp-python backend
            elif self.backend == 'llama_cpp' and LLAMA_MODEL:
                try:
                    response = LLAMA_MODEL(
                        prompt,
                        max_tokens=300,
                        temperature=0.7,
                        top_p=0.9,
                        stop=["\n\n\n"],
                        echo=False
                    )
                    if response and 'choices' in response and len(response['choices']) > 0:
                        text = response['choices'][0]['text'].strip()
                    elif isinstance(response, str):
                        text = response.strip()
                except Exception as e:
                    print(f"Warning: llama-cpp-python generation failed: {e}")
                    return None
            
            # Try transformers backend
            elif self.backend == 'transformers' and LLAMA_MODEL:
                try:
                    import torch
                    tokenizer = LLAMA_MODEL.get("tokenizer")
                    model = LLAMA_MODEL.get("model")
                    
                    if tokenizer and model and torch:
                        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                        with torch.no_grad():
                            outputs = model.generate(
                                **inputs,
                                max_new_tokens=300,
                                temperature=0.7,
                                top_p=0.9,
                                do_sample=True,
                                pad_token_id=tokenizer.eos_token_id
                            )
                        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        # Remove the prompt from the response
                        if prompt in text:
                            text = text.split(prompt, 1)[1].strip()
                except Exception as e:
                    print(f"Warning: transformers generation failed: {e}")
                    return None
            
            if not text:
                return None
            
            # Parse response
            definition = ""
            usage = ""
            
            if "DEFINITION:" in text:
                parts = text.split("DEFINITION:")
                if len(parts) > 1:
                    definition_part = parts[1].split("USAGE:")[0].strip()
                    definition = definition_part
            
            if "USAGE:" in text:
                parts = text.split("USAGE:")
                if len(parts) > 1:
                    usage = parts[1].strip()
            
            # Fallback: if parsing failed, use first paragraph as definition
            if not definition and text:
                lines = text.split('\n')
                definition = lines[0].strip() if lines else text[:200]
            
            if definition:
                self.generated_count += 1
                return {
                    "definition": definition,
                    "usage": usage or f"Generated description for {node.name}",
                    "source": "llama_local"
                }
        
        except Exception as e:
            print(f"Warning: Llama description generation failed: {e}")
        
        return None

    def node_needs_unit(self, node: SemanticNode) -> bool:
        """
        Ask Ollama whether this semantic node has a measurement unit (yes/no).
        Nodes like product ID, serial number, name, code, URI have no unit – we skip unit search for those.
        Returns True only if Ollama says the node has or needs a unit; False to skip.
        """
        if not self.use_llama or not LLAMA_AVAILABLE:
            return True  # no Ollama: assume unit may be needed, proceed with search
        name = (node.name or "").strip()
        desc = (node.conceptual_definition or "").strip()[:200]
        (node.value_type or "").strip()
        meta = getattr(node, "metadata", None) or {}
        path = _build_path_from_metadata(meta)
        prompt_parts = [
            "Does this semantic node have a measurement unit?",
            "",
            f"Node name: {name}",
        ]
        if path:
            prompt_parts.append(f"Context/path: {path}")
        if desc:
            prompt_parts.append(f"Description: {desc}")
        prompt_parts.extend([
            "",
            "Identifiers, names, IDs, codes, URIs, dates, booleans, free text have NO unit.",
            "Only physical quantities (length, speed, force, pressure, temperature, etc.) have units.",
            "",
            "Reply with exactly one word: YES or NO",
        ])
        prompt = "\n".join(prompt_parts)
        text = ""
        try:
            if self.backend == "ollama":
                import requests
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1, "top_p": 0.9, "num_predict": 10},
                    },
                    timeout=15,
                )
                if response.status_code == 200:
                    text = (response.json().get("response") or response.json().get("text") or "").strip()
        except Exception:
            return True
        if not text:
            return True
        first_word = text.upper().split()[0] if text.split() else ""
        if first_word == "NO" or first_word.startswith("NO"):
            return False
        return True

    def generate_unit(self, node: SemanticNode) -> Optional[str]:
        """
        Ask Llama to suggest a suitable measurement unit from node name, description, and path/context.
        Context-aware: Same abbreviation (V, P, T, f) can mean different units based on Path.
        Example: max_V in "Actuator/Mechanical/Linear" → m/s (velocity)
                 max_V in "Inverter/Electrical/Output" → V (voltage)
        
        Prefer SI or common canonical form. Equivalent units (e.g. m/s and km/h for velocity)
        are treated as the same quantity; we return a canonical form when possible.
        """
        if not self.use_llama or not LLAMA_AVAILABLE:
            return None
        
        desc = (node.conceptual_definition or "").strip()
        name = (node.name or "").strip()
        (node.value_type or "String").strip()
        
        # Build path from metadata for context-aware unit inference
        meta = getattr(node, 'metadata', None) or {}
        path = _build_path_from_metadata(meta)
        
        # Build prompt with path/context
        prompt_parts = []
        if path and path.strip():
            prompt_parts.append(f"Path (use this to disambiguate abbreviations): {path.strip()}")
            prompt_parts.append("")
            prompt_parts.append("Examples:")
            prompt_parts.append("- max_V in 'Actuator/Mechanical/Linear' → m/s (velocity)")
            prompt_parts.append("- max_V in 'Inverter/Electrical/Output' → V (voltage)")
            prompt_parts.append("- avg_P in 'Pump/Fluid/Pressure' → bar (pressure)")
            prompt_parts.append("- avg_P in 'Motor/Electrical/Rating' → kW (power)")
            prompt_parts.append("")
        
        # Very simple, direct prompt - just ask for the unit
        if path:
            prompt_parts.append(f"What unit for '{name}' in context '{path}'?")
        else:
            prompt_parts.append(f"What unit for '{name}'?")
        
        if desc:
            prompt_parts.append(f"Description: {desc}")
        
        prompt_parts.append("")
        prompt_parts.append("Examples: Stroke→mm, max_V→m/s, force→N, torque→N·m, RPM→rpm, pressure→bar")
        prompt_parts.append("")
        prompt_parts.append("Reply with only the unit symbol (mm, m/s, rpm, N·m, bar, V, W, °C, Hz, %) or NONE:")
        
        prompt = "\n".join(prompt_parts)
        text = ""
        try:
            if self.backend == 'ollama':
                import requests
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.2, "top_p": 0.9, "max_tokens": 50}
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    # Ollama can return response in different formats
                    text = result.get("response", "") or result.get("text", "") or ""
                    text = text.strip()
                    # Debug: log what Llama returned
                    if not text:
                        print(f"    [DEBUG] Llama returned empty response for '{name}'. Full response: {result}")
                    else:
                        print(f"    [DEBUG] Llama raw response for '{name}': '{text[:100]}'")
                else:
                    error_text = response.text if hasattr(response, 'text') else str(response.content)
                    print(f"    [DEBUG] Ollama API returned status {response.status_code} for '{name}': {error_text[:200]}")
            elif self.backend == 'llama_cpp' and LLAMA_MODEL:
                response = LLAMA_MODEL(prompt, max_tokens=50, temperature=0.2, top_p=0.9, stop=["\n"], echo=False)
                if response and response.get('choices'):
                    text = response['choices'][0].get('text', '').strip()
                elif isinstance(response, str):
                    text = response.strip()
                if text:
                    print(f"    [DEBUG] Llama raw response for '{name}': '{text[:100]}'")
            elif self.backend == 'transformers' and LLAMA_MODEL:
                tokenizer = LLAMA_MODEL.get("tokenizer")
                model = LLAMA_MODEL.get("model")
                if tokenizer and model:
                    import torch
                    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
                    with torch.no_grad():
                        outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.2, top_p=0.9,
                                                do_sample=True, pad_token_id=tokenizer.eos_token_id)
                    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    if prompt in text:
                        text = text.split(prompt, 1)[1].strip()
                    if text:
                        print(f"    [DEBUG] Llama raw response for '{name}': '{text[:100]}'")
        except Exception as e:
            print(f"    [WARNING] Llama unit generation failed for '{name}': {e}")
            return None
        
        if not text:
            print(f"    [DEBUG] No text returned from Llama for '{name}'")
            return None
        
        # Extract unit from response - try multiple parsing strategies
        # Strategy 1: Look for unit patterns in the response
        import re
        
        # Common unit patterns - ORDER MATTERS: compound units first, then simple
        # This prevents "m" from matching in "m/s" or "N·m"
        unit_patterns = [
            r'\b(m/s|mm/s|km/h|in/s)\b',  # Velocity (compound - check first!)
            r'\b(N·m|Nm|kNm|lb-ft)\b',  # Torque (compound - check first!)
            r'\b(l/min|m³/h|ml/s)\b',  # Flow (compound - check first!)
            r'\b(rpm|rad/s|1/s|°/s)\b',  # Angular velocity
            r'\b(mm|cm|µm|inch|in)\b',  # Length (multi-char first)
            r'\b(kN|mN|lbf)\b',  # Force (multi-char first)
            r'\b(kg|mg|t|lb)\b',  # Mass (multi-char first)
            r'\b(bar|kPa|MPa|psi)\b',  # Pressure (multi-char first)
            r'\b(kV|mV)\b',  # Voltage (multi-char first)
            r'\b(mA)\b',  # Current (multi-char first)
            r'\b(kW|mW|MW)\b',  # Power (multi-char first)
            r'\b(ms|µs|min|h)\b',  # Time (multi-char first)
            r'\b(kHz|MHz)\b',  # Frequency (multi-char first)
            r'\b(°C|°F)\b',  # Temperature (with symbols)
            r'\b(%|percent)\b',  # Percentage
            # Single-letter units last (to avoid matching parts of compound units)
            r'\b(m)\b',  # Length (single - last!)
            r'\b(N)\b',  # Force (single - last!)
            r'\b(g)\b',  # Mass (single - last!)
            r'\b(Pa)\b',  # Pressure (single - last!)
            r'\b(V)\b',  # Voltage (single - last!)
            r'\b(A)\b',  # Current (single - last!)
            r'\b(W)\b',  # Power (single - last!)
            r'\b(K)\b',  # Temperature (single - last!)
            r'\b(s)\b',  # Time (single - last!)
            r'\b(Hz)\b',  # Frequency (single - last!)
        ]
        
        # Try to find unit pattern in response
        found_unit = None
        for pattern in unit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found_unit = match.group(1)
                break
        
        # Strategy 2: Parse first line if no pattern found
        if not found_unit:
            line = text.split("\n")[0].strip().strip(".").strip()
            
            # Remove common prefixes/suffixes
            for prefix in ["Unit:", "unit:", "Unit is:", "The unit is:", "->", "Answer:", "answer:", "Reply:", "Response:"]:
                if line.lower().startswith(prefix.lower()):
                    line = line[len(prefix):].strip()
            
            # Remove quotes and extra whitespace
            line = line.strip('"').strip("'").strip()
            
            # Check if it's a valid unit (short, alphanumeric with common symbols)
            if line and len(line) <= 10 and re.match(r'^[a-zA-Z0-9·°³/%\-\s]+$', line):
                found_unit = line
        
        if not found_unit or found_unit.upper() == "NONE" or len(found_unit) > 20:
            print(f"    [DEBUG] Unit inference filtered out for '{name}': raw='{text[:50]}', parsed='{found_unit}'")
            return None
        
        # Normalize to canonical form (e.g., km/h → m/s)
        normalized = normalize_unit_to_canonical(found_unit)
        result = normalized if normalized else found_unit.strip()
        print(f"    [DEBUG] Unit inference result for '{name}': '{found_unit}' → '{result}'")
        return result


class SemanticNodeEnricher:
    """
    Main enrichment engine that uses eCl@ss and IEC CDD libraries
    to complete semantic nodes with missing information.
    
    Enhanced with context-aware LLM intelligence for understanding
    semantic meaning in different contexts (e.g., "capacity" as volume vs charge).
    """
    
    def __init__(self, 
                 eclass_file: Optional[str] = None,
                 ieccdd_file: Optional[str] = None,
                 support_folder: str = "support_files",
                 support_urls: Optional[List[str]] = None,
                 use_llama: bool = True,
                 use_gemini: bool = False,
                 use_openai: bool = False,
                 collection: Optional[SemanticNodeCollection] = None):
        """
        Initialize enrichment engine.
        
        Args:
            eclass_file: Path to custom eCl@ss library file
            ieccdd_file: Path to custom IEC CDD library file
            support_folder: Path to folder containing support documents
            support_urls: Optional list of URLs to fetch HTML content from
            use_llama: Whether to use Llama for local reasoning (default: True)
            use_gemini: Whether to use Gemini API as fallback (default: False)
            use_openai: Whether to use OpenAI API (default: False, only Llama used)
            collection: Optional collection of semantic nodes for context gathering
        """
        self.eclass = EClassLibrary(eclass_file, eclass_folder="EClass", lazy_load=True)
        self.ieccdd = IECCDDLibrary(ieccdd_file)
        self.documents = DocumentLibrary(support_folder, support_urls=support_urls)
        self.llama = LlamaEnricher(use_llama)
        self.gemini = GeminiEnricher(use_gemini)
        self.openai = OpenAIEnricher(use_openai=use_openai)
        self.collection = collection  # For context gathering
        # Skip eClass CDP API by default (local files faster); set ECLASS_CDP_SKIP_API=0 to enable
        self.skip_eclass_cdp_api = os.getenv("ECLASS_CDP_SKIP_API", "1").strip().lower() in ("1", "true", "yes")
        self.enrichment_stats = {
            "total_processed": 0,
            "enriched_from_eclass": 0,
            "enriched_from_ieccdd": 0,
            "enriched_from_documents": 0,
            "enriched_from_llama": 0,
            "enriched_from_gemini": 0,
            "enriched_from_openai": 0,
            "not_found": 0,
            "eclass_cdp_api": "skipped (local files used)" if self.skip_eclass_cdp_api else "available",
        }
    
    def _gather_context(self, node: SemanticNode) -> str:
        """
        Gather context from surrounding nodes in the collection to understand
        the semantic meaning of the current node.
        
        Args:
            node: The semantic node to gather context for
        
        Returns:
            Context string describing the domain/application
        """
        # AAS context: asset and submodel so OpenAI/eClass can generate accurate descriptions
        context_parts = []
        if getattr(node, 'metadata', None):
            source_asset = (node.metadata or {}).get("source_asset", "")
            source_submodel = (node.metadata or {}).get("source_submodel", "")
            parent_id = (node.metadata or {}).get("parent_id", "")
            
            if parent_id:
                context_parts.append(f"This parameter belongs to parent object/process [{parent_id}].")
                
            if source_asset or source_submodel:
                if source_submodel and source_asset:
                    context_parts.append(f"This node is part of the [{source_submodel}] submodel of asset [{source_asset}]. Use this context for accurate technical definitions and eClass matching.")
                elif source_submodel:
                    context_parts.append(f"This node is part of the [{source_submodel}] submodel. Use this context for accurate technical definitions and eClass matching.")
                elif source_asset:
                    context_parts.append(f"This node belongs to asset [{source_asset}]. Use this context for accurate technical definitions and eClass matching.")
        
        if not self.collection:
            return "\n".join(context_parts) if context_parts else ""
        
        # Get related nodes (same file, similar units, etc.)
        context_nodes = []
        for other_node in self.collection.nodes:
            if other_node == node:
                continue
            # Same source file indicates related context
            if other_node.source_file == node.source_file:
                context_nodes.append(other_node)
            # Similar units might indicate same domain
            elif other_node.unit and node.unit and other_node.unit == node.unit:
                context_nodes.append(other_node)
        
        # Build context description (context_parts may already contain asset/submodel)
        if context_nodes:
            context_parts.append("Related semantic nodes in the same context:")
            for ctx_node in context_nodes[:5]:  # Limit to 5 for prompt size
                ctx_desc = f"- {ctx_node.name}"
                if ctx_node.unit:
                    ctx_desc += f" ({ctx_node.unit})"
                if ctx_node.conceptual_definition:
                    ctx_desc += f": {ctx_node.conceptual_definition[:50]}"
                context_parts.append(ctx_desc)
        
        # Add domain hints from node properties
        if node.unit:
            context_parts.append(f"Unit: {node.unit}")
        if node.value_type:
            context_parts.append(f"Value type: {node.value_type}")
        if node.source_file:
            context_parts.append(f"Source: {node.source_file}")
        
        return "\n".join(context_parts)
    
    def _understand_semantic_meaning(self, node: SemanticNode, candidates: List[Tuple[Dict, float]]) -> Optional[Dict]:
        """
        Use LLM to understand the semantic meaning of a node in context
        and select the best matching property from candidates.
        
        Example: "capacity" could mean:
        - Volume (mechanical context: "capacity: 100L")
        - Electrical charge (capacitor context: "capacity: 1000µF")
        - Number of people (hall context: "capacity: 50 persons")
        
        Args:
            node: Semantic node to understand
            candidates: List of (property_dict, similarity_score) tuples
        
        Returns:
            Best matching property dict or None
        """
        if not candidates or not LLAMA_AVAILABLE:
            return None
        
        context = self._gather_context(node)
        
        # Build candidate descriptions
        candidate_descriptions = []
        for i, (prop, score) in enumerate(candidates[:10]):  # Top 10 candidates
            desc = f"Candidate {i+1} (similarity: {score:.2f}):\n"
            desc += f"  Name: {prop.get('definition', 'N/A')[:100]}\n"
            if prop.get('unit'):
                desc += f"  Unit: {prop.get('unit')}\n"
            if prop.get('eclass_id'):
                desc += f"  eClass ID: {prop.get('eclass_id')}"
            candidate_descriptions.append(desc)
        
        prompt = f"""Analyze the semantic meaning of a property in context and select the best match.

Target Property:
Name: {node.name}
Unit: {node.unit if node.unit else 'N/A'}
Value Type: {node.value_type}
Value: {node.value if node.value else 'N/A'}

Context:
{context if context else 'No additional context available'}

Candidates:
{chr(10).join(candidate_descriptions)}

Task: Determine which candidate best matches the target property considering:
1. Semantic meaning in the given context (e.g., "capacity" could mean volume, charge, or occupancy)
2. Unit compatibility
3. Value type compatibility
4. Domain/application context

Respond with ONLY the candidate number (1-{len(candidates[:10])}) that best matches, or "NONE" if no good match.
Response:"""
        
        try:
            text = ""
            
            # Use Ollama
            if LLAMA_BACKEND == 'ollama':
                import requests
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                model_name = os.getenv("LLAMA_MODEL_NAME", "llama3.2")
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "max_tokens": 50
                        }
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "").strip()
            
            # Parse response
            if text:
                # Extract number from response
                import re
                match = re.search(r'\b(\d+)\b', text)
                if match:
                    candidate_idx = int(match.group(1)) - 1
                    if 0 <= candidate_idx < len(candidates):
                        return candidates[candidate_idx][0]  # Return the property dict
        
        except Exception as e:
            print(f"  [DEBUG] LLM semantic understanding failed: {e}")
        
        # Fallback: return highest similarity match
        if candidates:
            return candidates[0][0]
        
        return None
    
    def enrich_node(self, node: SemanticNode, libraries_only: bool = False) -> bool:
        """
        Enrich a single semantic node with missing information.
        
        Uses multiple enrichment sources in priority order (unless libraries_only=True):
        1. Support documents (with normalization) - FIRST PRIORITY
        2. eCl@ss library (top-K search with 90% threshold)
        3. IEC CDD library (top-K search with 90% threshold)
        4. Llama AI (local) - generates descriptions using local AI (ONLY AI MODEL USED)
        5. OpenAI (disabled by default) - only if explicitly enabled
        6. Gemini AI (disabled by default) - only if explicitly enabled
        
        When libraries_only=True (e.g. after Ollama table failed for this node), only
        eCl@ss and IEC CDD are tried; documents and all AI backends are skipped.
        
        IMPORTANT: Uses normalized name (from metadata["normalized_name"]) if available,
        otherwise falls back to node.name. This ensures abbreviations like "max_V" are
        expanded to "maximum velocity" before searching libraries.
        
        Args:
            node: Semantic node to enrich
            libraries_only: If True, only try eCl@ss and IEC CDD (no documents, no Llama/OpenAI/Gemini)
        
        Returns:
            True if enrichment was successful, False otherwise
        """
        self.enrichment_stats["total_processed"] += 1
        
        if not node.needs_enrichment():
            return False
        
        # Use normalized name if available (from normalization step), otherwise use original name
        # This ensures "max_V" → "maximum velocity" is used for searching, improving match quality
        search_name = node.name
        if node.metadata and "normalized_name" in node.metadata and node.metadata["normalized_name"]:
            search_name = node.metadata["normalized_name"]
            print(f"    [INFO] Using normalized name for search: '{node.name}' → '{search_name}'")
        
        # Gather context from surrounding nodes for intelligent matching
        context = self._gather_context(node)
        
        if not libraries_only:
            # PRIORITY 1: Try support documents FIRST (with LLM-enhanced search)
            # Pass both original and normalized names so we find descriptions whether the user
            # stored them under "max_V"/"max_v" or "maximum velocity" in support files
            doc_name_variants = None
            if node.name and (node.name != search_name or node.name.lower() != search_name.lower()):
                doc_name_variants = [node.name]
            doc_result = self.documents.search(
                search_name, node.unit, node.value_type, context=context,
                name_variants=doc_name_variants
            )
            if doc_result:
                was_enriched_before = node.enriched
                self._apply_enrichment(node, doc_result, "documents")
                # Only count as enriched if we actually filled missing data
                if node.enriched and not was_enriched_before:
                    self.enrichment_stats["enriched_from_documents"] += 1
                    return True
        
        # PRIORITY 2: Try eCl@ss (local library; CDP API skipped by default – see report)
        # If description is already available, or ECLASS_CDP_SKIP_API=1, skip CDP API (no network calls)
        has_description = bool((node.conceptual_definition or "").strip() or (node.usage_of_data or "").strip())
        use_cdp_api = not self.skip_eclass_cdp_api and not has_description
        eclass_result = None
        if use_cdp_api:
            # 2a) If node.value is an eClass CDP URL, fetch from API
            if node.value and isinstance(node.value, str):
                eclass_result = _eclass_cdp_fetch_by_url(node.value)
            # 2b) Else if node has eClass IRDI, fetch via xmlapi/v2/properties/{irdi}
            if not eclass_result:
                eclass_id = (node.metadata or {}).get("eclass_id")
                if not eclass_id and node.value and isinstance(node.value, str):
                    m = re.search(r"0173-1#\d{2}-[A-Z0-9]+#\d{3}", node.value)
                    if m:
                        eclass_id = m.group(0)
                if eclass_id and isinstance(eclass_id, str) and (_get_eclass_cdp_cert_key()[0] or _get_eclass_cdp_api_key()):
                    eclass_result = _eclass_cdp_get_property_xml(eclass_id.strip())
                    if eclass_result and not (eclass_result.get("definition") or eclass_result.get("usage")):
                        eclass_result = None
        # 2c) Search local eClass folder (XML files); skip CDP API if API disabled or description already available
        if not eclass_result:
            eclass_result = self.eclass.search(
                search_name, node.unit, node.value_type, context=context, enricher=self,
                skip_cdp_api=self.skip_eclass_cdp_api or has_description
            )
        if eclass_result:
            was_enriched_before = node.enriched
            self._apply_enrichment(node, eclass_result, "eclass")
            # Only count as enriched if we actually filled missing data
            if node.enriched and not was_enriched_before:
                self.enrichment_stats["enriched_from_eclass"] += 1
                return True
        
        # PRIORITY 3: Try IEC CDD library (with context-aware LLM matching)
        ieccdd_result = self.ieccdd.search(search_name, node.unit, node.value_type, context=context, enricher=self)
        if ieccdd_result:
            was_enriched_before = node.enriched
            self._apply_enrichment(node, ieccdd_result, "ieccdd")
            # Only count as enriched if we actually filled missing data
            if node.enriched and not was_enriched_before:
                self.enrichment_stats["enriched_from_ieccdd"] += 1
                return True
        
        if libraries_only:
            # Only libraries requested; skip all AI backends
            self.enrichment_stats["not_found"] += 1
            return False
        
        # PRIORITY 4: Use Llama AI (local, privacy-focused) to generate description (ONLY AI MODEL)
        if self.llama.use_llama:
            llama_result = self.llama.generate_description(node)
            if llama_result:
                was_enriched_before = node.enriched
                self._apply_enrichment(node, llama_result, "llama")
                # Only count as enriched if we actually filled missing data
                if node.enriched and not was_enriched_before:
                    self.enrichment_stats["enriched_from_llama"] += 1
                    return True
        
        # PRIORITY 5: Use OpenAI (disabled by default - only if explicitly enabled)
        if self.openai.use_openai:
            openai_result = self.openai.generate_description(node, context=context)
            if openai_result:
                was_enriched_before = node.enriched
                self._apply_enrichment(node, openai_result, "openai")
                if node.enriched and not was_enriched_before:
                    self.enrichment_stats["enriched_from_openai"] += 1
                    return True
        
        # PRIORITY 6: Use Gemini (disabled by default - only if explicitly enabled)
        if self.gemini.use_gemini:
            gemini_result = self.gemini.generate_description(node)
            if gemini_result:
                was_enriched_before = node.enriched
                self._apply_enrichment(node, gemini_result, "gemini")
                # Only count as enriched if we actually filled missing data
                if node.enriched and not was_enriched_before:
                    self.enrichment_stats["enriched_from_gemini"] += 1
                    return True
        
        # Unit fallback: if unit is still empty, use Llama to suggest unit from name + description (skip when libraries_only)
        if not libraries_only and not node.unit and self.llama.use_llama:
            suggested_unit = self.llama.generate_unit(node)
            if suggested_unit:
                node.unit = suggested_unit
                print(f"    [INFO] Applied unit from Llama (inferred): {node.unit}")
        
        # If nothing found, mark as not found
        self.enrichment_stats["not_found"] += 1
        return False
    
    def _generate_gemini_description(self, node: SemanticNode):
        """Generate Gemini description and store in metadata for comparison."""
        gemini_result = self.gemini.generate_description(node)
        if gemini_result:
            node.metadata["gemini_definition"] = gemini_result.get("definition", "")
            node.metadata["gemini_usage"] = gemini_result.get("usage", "")
    
    def _apply_enrichment(self, node: SemanticNode, result: Dict, source: str):
        """
        Apply enrichment result to semantic node.
        
        For eClass and IEC CDD sources, also extracts and applies unit and value_type
        to improve matching confidence scores.
        
        Only marks node as enriched if missing data (conceptual_definition or usage_of_data)
        was actually filled from support files, libraries, or LLM.
        """
        # Track what was missing before enrichment
        was_missing_definition = not bool(node.conceptual_definition)
        was_missing_usage = not bool(node.usage_of_data)
        
        # Fill missing data
        if was_missing_definition and "definition" in result and result["definition"]:
            node.conceptual_definition = result["definition"]
        
        if was_missing_usage and "usage" in result and result["usage"]:
            node.usage_of_data = result["usage"]
        
        # Only mark as enriched if we actually filled missing data
        data_was_filled = (was_missing_definition and bool(node.conceptual_definition)) or \
                         (was_missing_usage and bool(node.usage_of_data))
        
        if data_was_filled:
            node.enriched = True
            node.enrichment_source = source
        else:
            # If no missing data was filled, don't mark as enriched
            # (node might already have had all data from source/target files)
            pass
        
        # Extract unit and value_type from eClass/IEC CDD if available
        # This improves matching confidence by ensuring standardized units and types
        if source in ["eclass", "ieccdd"]:
            # Extract unit from eClass/IEC CDD if node doesn't have one or if eClass has a standard unit
            if "unit" in result and result["unit"]:
                eclass_unit = result["unit"].strip()
                if eclass_unit:
                    # If node has no unit, use eClass unit
                    if not node.unit:
                        node.unit = eclass_unit.split(',')[0].strip()  # Take first unit if multiple
                        print(f"    [INFO] Applied unit from {source}: {node.unit}")
                    # If node has unit but eClass unit is more standard, consider updating
                    # (For now, we keep the original unit if it exists)
            
            # Extract value_type from eClass/IEC CDD if node doesn't have a proper one
            if "value_type" in result and result["value_type"]:
                eclass_type = result["value_type"].strip()
                if eclass_type:
                    # Normalize eClass type to match our type system
                    normalized_eclass_type = self._normalize_eclass_type(eclass_type)
                    
                    # If node has no type or has default "String", use eClass type
                    if not node.value_type or node.value_type == "String":
                        node.value_type = normalized_eclass_type
                        print(f"    [INFO] Applied value_type from {source}: {node.value_type}")
                    # If node has a type but eClass type is more specific, consider updating
                    # (For now, we keep the original type if it exists and is not default)
            
            # Always try to extract eClass ID and look up unit/value_type
            # This ensures we get units even if the search result doesn't include them
            eclass_id_to_use = None
            if source == "eclass" and "eclass_id" in result:
                eclass_id_to_use = result["eclass_id"]
            
            # Also check if node's value field contains an eClass ID (common case)
            if not eclass_id_to_use and node.value and isinstance(node.value, str):
                # Check if value looks like an eClass ID (format: 0173-1#02-XXXXX#XXX)
                import re
                eclass_id_pattern = r'0173-1#\d{2}-[A-Z0-9]+#\d{3}'
                match = re.search(eclass_id_pattern, str(node.value))
                if match:
                    eclass_id_to_use = match.group(0)
            
            # Also check metadata for eClass ID (stored during extraction)
            if not eclass_id_to_use and "eclass_id" in node.metadata:
                eclass_id_to_use = node.metadata["eclass_id"]
            
            # Look up unit from eClass ID if we have one and node doesn't have unit
            if not node.unit and eclass_id_to_use:
                unit_from_id = self._lookup_eclass_unit_by_id(eclass_id_to_use)
                if unit_from_id:
                    node.unit = unit_from_id
                    print(f"    [INFO] Applied unit from eClass ID lookup ({eclass_id_to_use}): {node.unit}")
            
            # Look up value_type from eClass ID if we have one
            if (not node.value_type or node.value_type == "String") and eclass_id_to_use:
                type_from_id = self._lookup_eclass_type_by_id(eclass_id_to_use)
                if type_from_id:
                    node.value_type = self._normalize_eclass_type(type_from_id)
                    print(f"    [INFO] Applied value_type from eClass ID lookup ({eclass_id_to_use}): {node.value_type}")
        
        # Store additional metadata (only if enriched)
        if node.enriched:
            if source == "eclass" and "eclass_id" in result:
                node.metadata["eclass_id"] = result["eclass_id"]
            elif source == "ieccdd" and "irdi" in result:
                node.metadata["irdi"] = result["irdi"]
    
    def _lookup_eclass_unit_by_id(self, eclass_id: str, skip_slow_lookup: bool = False) -> Optional[str]:
        """
        Look up unit from eClass property by eClass ID.
        
        When skip_slow_lookup=False: searches library, then eClass XML files (slow),
        then Gemini. When skip_slow_lookup=True (e.g. for target/standard collections):
        only in-memory library; no XML or Gemini, for speed.
        
        Args:
            eclass_id: eClass property ID (e.g., "0173-1#02-AAO740#002")
            skip_slow_lookup: If True, only check library; skip XML and Gemini (faster)
        
        Returns:
            Unit string if found, None otherwise
        """
        # First, search through library entries for matching eclass_id (fast)
        for key, entry in self.eclass.library.items():
            if entry.get("eclass_id") == eclass_id:
                if "unit" in entry and entry["unit"]:
                    unit = entry["unit"].strip()
                    if unit:
                        return unit.split(',')[0].strip()  # Return first unit if multiple
        
        if skip_slow_lookup:
            return None
        
        # Second, try eClass CDP XML API (GET /xmlapi/v2/properties/{irdi}) if configured
        if _get_eclass_cdp_cert_key()[0] or _get_eclass_cdp_api_key():
            prop = _eclass_cdp_get_property_xml(eclass_id)
            if prop and prop.get("unit"):
                return (prop["unit"] or "").strip().split(",")[0].strip() or None
        
        # Third, search eClass XML files directly for the property (slow)
        unit_from_xml = self.eclass._search_property_in_xml(eclass_id, "unit")
        if unit_from_xml:
            return unit_from_xml
        
        # Fourth, use Gemini as fallback
        unit_from_gemini = self._lookup_eclass_unit_with_gemini(eclass_id)
        if unit_from_gemini:
            return unit_from_gemini
        
        return None
    
    def _lookup_eclass_type_by_id(self, eclass_id: str) -> Optional[str]:
        """
        Look up value type from eClass property by eClass ID.
        
        First searches through loaded eClass library entries, then searches
        eClass XML files directly for the property ID, and finally uses Gemini
        as a fallback.
        
        Args:
            eclass_id: eClass property ID (e.g., "0173-1#02-AAO740#002")
        
        Returns:
            Value type string if found, None otherwise
        """
        # First, search through library entries for matching eclass_id
        for key, entry in self.eclass.library.items():
            if entry.get("eclass_id") == eclass_id:
                if "value_type" in entry and entry["value_type"]:
                    return entry["value_type"].strip()
        
        # Second, try eClass CDP XML API (GET /xmlapi/v2/properties/{irdi}) if configured
        if _get_eclass_cdp_cert_key()[0] or _get_eclass_cdp_api_key():
            prop = _eclass_cdp_get_property_xml(eclass_id)
            if prop and prop.get("value_type"):
                return (prop["value_type"] or "").strip() or None
        
        # Third, search eClass XML files directly for the property
        type_from_xml = self.eclass._search_property_in_xml(eclass_id, "value_type")
        if type_from_xml:
            return type_from_xml
        
        # Fourth, use Gemini as fallback
        type_from_gemini = self._lookup_eclass_type_with_gemini(eclass_id)
        if type_from_gemini:
            return type_from_gemini
        
        return None
    
    def _lookup_eclass_unit_with_gemini(self, eclass_id: str) -> Optional[str]:
        """Use Gemini to look up unit for an eClass property ID."""
        if not self.gemini.use_gemini:
            return None
        
        try:
            prompt = f"""What is the standard unit of measurement for the eClass property with ID {eclass_id}?
            
Return only the unit abbreviation (e.g., mm, m, N, Nm, m/s, rpm, °C, etc.) or "N/A" if unknown.
Do not include any explanation, just the unit abbreviation."""
            
            from enrichment_module import GEMINI_CLIENT, GEMINI_MODEL, GEMINI_AVAILABLE
            
            if GEMINI_AVAILABLE:
                text = ""
                if GEMINI_CLIENT:
                    try:
                        model_names = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro", "gemini-1.5-pro"]
                        for model_name in model_names:
                            try:
                                response = GEMINI_CLIENT.models.generate_content(
                                    model=model_name,
                                    contents=prompt
                                )
                                if response.text:
                                    text = response.text.strip()
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass
                
                if not text and GEMINI_MODEL:
                    try:
                        response = GEMINI_MODEL.generate_content(prompt)
                        text = response.text.strip()
                    except Exception:
                        pass
                
                if text and text.upper() != "N/A" and len(text) < 20:  # Unit should be short
                    return text.strip()
        except Exception as e:
            print(f"    [DEBUG] Gemini unit lookup failed for {eclass_id}: {e}")
        
        return None
    
    def _lookup_eclass_type_with_gemini(self, eclass_id: str) -> Optional[str]:
        """Use Gemini to look up value type for an eClass property ID."""
        if not self.gemini.use_gemini:
            return None
        
        try:
            prompt = f"""What is the data type for the eClass property with ID {eclass_id}?
            
Return only the data type (e.g., Float, Real, Integer, String, Boolean) or "N/A" if unknown.
Do not include any explanation, just the data type."""
            
            from enrichment_module import GEMINI_CLIENT, GEMINI_MODEL, GEMINI_AVAILABLE
            
            if GEMINI_AVAILABLE:
                text = ""
                if GEMINI_CLIENT:
                    try:
                        model_names = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro", "gemini-1.5-pro"]
                        for model_name in model_names:
                            try:
                                response = GEMINI_CLIENT.models.generate_content(
                                    model=model_name,
                                    contents=prompt
                                )
                                if response.text:
                                    text = response.text.strip()
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass
                
                if not text and GEMINI_MODEL:
                    try:
                        response = GEMINI_MODEL.generate_content(prompt)
                        text = response.text.strip()
                    except Exception:
                        pass
                
                if text and text.upper() != "N/A":
                    return text.strip()
        except Exception as e:
            print(f"    [DEBUG] Gemini type lookup failed for {eclass_id}: {e}")
        
        return None
    
    def _normalize_eclass_type(self, eclass_type: str) -> str:
        """
        Normalize eClass value type to standard format.
        
        Converts eClass types to our standard type system (xs:float, xs:string, etc.)
        """
        type_lower = eclass_type.lower().strip()
        
        # Map common eClass types to standard types
        type_mapping = {
            'float': 'xs:float',
            'double': 'xs:float',
            'real': 'xs:float',
            'integer': 'xs:integer',
            'int': 'xs:integer',
            'string': 'xs:string',
            'str': 'xs:string',
            'boolean': 'xs:boolean',
            'bool': 'xs:boolean',
            'xs:float': 'xs:float',
            'xs:double': 'xs:float',
            'xs:integer': 'xs:integer',
            'xs:int': 'xs:integer',
            'xs:string': 'xs:string',
            'xs:boolean': 'xs:boolean',
        }
        
        # Check if already in standard format
        if type_lower in type_mapping:
            return type_mapping[type_lower]
        
        # If not found, try to infer from common patterns
        if 'float' in type_lower or 'double' in type_lower or 'real' in type_lower:
            return 'xs:float'
        elif 'int' in type_lower or 'integer' in type_lower:
            return 'xs:integer'
        elif 'string' in type_lower or 'str' in type_lower or 'text' in type_lower:
            return 'xs:string'
        elif 'bool' in type_lower or 'boolean' in type_lower:
            return 'xs:boolean'
        
        # Default to string if unknown
        return 'xs:string'
    
    def enrich_collection(
        self,
        collection: SemanticNodeCollection,
        is_target_collection: bool = False,
        use_llama_unit_for_target: str = "clarification",
    ) -> Dict[str, int]:
        """
        Enrich all nodes in a collection that need enrichment.
        
        IMPORTANT: Normalizes node names FIRST (if not already normalized) to ensure
        abbreviations like "max_V" are expanded to "maximum velocity" before searching
        libraries. This significantly improves match quality.
        
        Unit inference:
        - Source (is_target_collection=False): Use Llama first for missing units (fast);
          then eClass lookup (library + XML) only for nodes with eClass ID still missing unit.
        - Target (is_target_collection=True): Standard files – only fast eClass library lookup,
          no slow XML/API. Use Llama only for "clarification" when use_llama_unit_for_target
          is "clarification"; use "never" to skip unit inference for target.
        
        Args:
            collection: Collection of semantic nodes
            is_target_collection: True when enriching target (standard) collection; skips slow unit search
            use_llama_unit_for_target: "clarification" = use Llama for target nodes missing unit; "never" = skip
        
        Returns:
            Dictionary with enrichment statistics
        """
        # Set collection reference for context gathering
        self.collection = collection
        
        # Normalization is done only in the pipeline (Step 2b), not here. Use existing normalized_name or node.name.
        
        nodes_to_enrich = collection.get_nodes_needing_enrichment()
        
        print(f"Found {len(nodes_to_enrich)} nodes needing enrichment")
        
        if len(nodes_to_enrich) == 0:
            print("  [INFO] All nodes already have descriptions, no enrichment needed")
            return self.enrichment_stats
        
        # Show which nodes will be enriched
        print(f"  Nodes to enrich: {[node.name for node in nodes_to_enrich]}")
        print()
        
        for i, node in enumerate(nodes_to_enrich, 1):
            print(f"  [{i}/{len(nodes_to_enrich)}] Enriching: {node.name}...", end=" ")
            result = self.enrich_node(node)
            if result:
                source = node.enrichment_source if hasattr(node, 'enrichment_source') else 'unknown'
                print(f"[OK] ({source})")
            else:
                print("[X] (not found)")
        
        # Post-processing: Units (ask Ollama first: does this node have a unit? skip search if no)
        import re
        eclass_id_pattern = re.compile(r'0173-1#\d{2}-[A-Z0-9]+#\d{3}')
        nodes_without_unit = [n for n in collection.nodes if not n.unit]
        
        # 0) For nodes without unit: ask Ollama "does this node have a unit?" (e.g. product ID → no; skip search)
        nodes_that_need_unit = list(nodes_without_unit)
        if nodes_without_unit and self.llama.use_llama:
            print(f"\n  Units: Checking which of {len(nodes_without_unit)} nodes have a unit (Ollama yes/no)...")
            needs = []
            for node in nodes_without_unit:
                try:
                    if self.llama.node_needs_unit(node):
                        needs.append(node)
                    else:
                        print(f"    [SKIP] No unit for '{node.name}' (identifier/name/code type)")
                except Exception:
                    needs.append(node)  # on error, assume unit may be needed
            nodes_that_need_unit = needs
            skipped = len(nodes_without_unit) - len(nodes_that_need_unit)
            if skipped:
                print(f"  [OK] Skipped unit search for {skipped} nodes (no unit expected)")
        
        # 1) SOURCE: Use Llama to infer unit only for nodes that need one (fast when not in source file)
        #    TARGET: Only if use_llama_unit_for_target == "clarification"
        run_llama_first = self.llama.use_llama and nodes_that_need_unit
        if is_target_collection:
            run_llama_first = run_llama_first and (use_llama_unit_for_target == "clarification")
        if run_llama_first:
            print(f"\n  Units: Inferring with Llama for {len(nodes_that_need_unit)} nodes (name + description)...")
            for node in nodes_that_need_unit:
                try:
                    suggested = self.llama.generate_unit(node)
                    if suggested:
                        node.unit = suggested
                        print(f"    [INFO] Inferred unit for '{node.name}': {node.unit}")
                except Exception as e:
                    print(f"    [WARNING] Unit inference failed for '{node.name}': {e}")
            inferred = [n for n in nodes_that_need_unit if n.unit]
            if inferred:
                print(f"  [OK] Inferred units for {len(inferred)}/{len(nodes_that_need_unit)} nodes")
        
        # 2) eClass lookup only for nodes that need a unit and still have eClass ID and no unit
        nodes_without_unit_after = [n for n in collection.nodes if not n.unit]
        nodes_with_eclass_ids = []
        for node in nodes_without_unit_after:
            if node not in nodes_that_need_unit:
                continue
            eclass_id = None
            if node.value and isinstance(node.value, str):
                match = eclass_id_pattern.search(str(node.value))
                if match:
                    eclass_id = match.group(0)
            if not eclass_id and node.metadata and node.metadata.get("eclass_id"):
                eclass_id = node.metadata["eclass_id"]
            if eclass_id:
                nodes_with_eclass_ids.append((node, eclass_id))
        skip_slow = is_target_collection  # target = standard: no slow XML/Gemini
        if nodes_with_eclass_ids:
            label = "library only (target=standard)" if skip_slow else "eClass IDs"
            print(f"\n  Units from eClass ({label}) for {len(nodes_with_eclass_ids)} nodes...")
        for node, eclass_id in nodes_with_eclass_ids:
            unit_from_id = self._lookup_eclass_unit_by_id(eclass_id, skip_slow_lookup=skip_slow)
            if unit_from_id:
                node.unit = unit_from_id
                print(f"    [INFO] Unit for '{node.name}' from eClass: {node.unit}")
        if nodes_with_eclass_ids:
            filled = len([n for n, _ in nodes_with_eclass_ids if n.unit])
            print(f"  [OK] Units from eClass for {filled}/{len(nodes_with_eclass_ids)} nodes")
        
        if nodes_without_unit and not run_llama_first and not is_target_collection and not self.llama.use_llama:
            print(f"\n  [INFO] {len(nodes_without_unit)} nodes without units; Llama not available for unit inference")
        if nodes_without_unit and is_target_collection and use_llama_unit_for_target != "clarification":
            print(f"\n  [INFO] Target (standard): skipped unit inference for {len(nodes_without_unit)} nodes; set use_llama_unit_for_target='clarification' to use Ollama")
        
        print()
        return self.enrichment_stats
    
    def enrich_collection_libraries_only(self, collection: SemanticNodeCollection) -> Dict[str, int]:
        """
        Enrich only nodes that still need enrichment using eCl@ss and IEC CDD only.
        Used as fallback after Ollama table: when Ollama failed or left a node incomplete,
        search only in eClass and IEC CDD (no support documents, no Llama/OpenAI/Gemini).
        Does not run Llama unit inference at the end.
        """
        self.collection = collection
        nodes_to_enrich = collection.get_nodes_needing_enrichment()
        if not nodes_to_enrich:
            print("  [INFO] No nodes need enrichment (libraries-only fallback skipped)")
            return self.enrichment_stats
        print(f"  [INFO] Enriching {len(nodes_to_enrich)} nodes from eCl@ss and IEC CDD only (Ollama fallback)...")
        for i, node in enumerate(nodes_to_enrich, 1):
            print(f"  [{i}/{len(nodes_to_enrich)}] {node.name}...", end=" ")
            result = self.enrich_node(node, libraries_only=True)
            if result:
                src = getattr(node, 'enrichment_source', None) or 'unknown'
                print(f"[OK] ({src})")
            else:
                print("[X] (not found)")
        # Extract units from eClass IDs where available (no Llama unit inference)
        for node in collection.nodes:
            eclass_id = None
            if node.value and isinstance(node.value, str):
                import re
                match = re.search(r'0173-1#\d{2}-[A-Z0-9]+#\d{3}', str(node.value))
                if match:
                    eclass_id = match.group(0)
            elif node.metadata and node.metadata.get("eclass_id"):
                eclass_id = node.metadata["eclass_id"]
            if eclass_id and not node.unit:
                u = self._lookup_eclass_unit_by_id(eclass_id)
                if u:
                    node.unit = u
        return self.enrichment_stats
    
    def get_statistics(self) -> Dict[str, int]:
        """Get enrichment statistics."""
        return self.enrichment_stats.copy()


# Example usage
if __name__ == "__main__":
    from semantic_node_enhanced import SemanticNode, SemanticNodeCollection
    
    print("=== Semantic Node Enrichment Module ===\n")
    
    # Create enricher
    enricher = SemanticNodeEnricher()
    
    # Create collection with incomplete nodes
    collection = SemanticNodeCollection()
    
    # Node 1: Temperature without description
    temp_node = SemanticNode(
        name="Temperature",
        value=180.0,
        value_type="Float",
        unit="°C",
        source_file="process_data.json"
    )
    collection.add_node(temp_node)
    
    # Node 2: Pressure without description
    pressure_node = SemanticNode(
        name="Pressure",
        value=5.2,
        value_type="Float",
        unit="bar"
    )
    collection.add_node(pressure_node)
    
    # Node 3: Manufacturer with description (no enrichment needed)
    mfg_node = SemanticNode(
        name="ManufacturerName",
        conceptual_definition="Name of the manufacturer",
        usage_of_data="Product identification and procurement",
        value="ACME Corp",
        value_type="String"
    )
    collection.add_node(mfg_node)
    
    print("Before enrichment:")
    print(f"  Total nodes: {len(collection)}")
    print(f"  Needs enrichment: {len(collection.get_nodes_needing_enrichment())}")
    
    # Enrich collection
    print("\nEnriching nodes...")
    stats = enricher.enrich_collection(collection)
    
    print("\nEnrichment Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nAfter enrichment:")
    print(f"  Needs enrichment: {len(collection.get_nodes_needing_enrichment())}")
    
    print("\nEnriched Nodes:")
    for node in collection:
        if node.enriched:
            print(f"\n  {node.name}:")
            print(f"    Definition: {node.conceptual_definition}")
            print(f"    Usage: {node.usage_of_data}")
            print(f"    Source: {node.enrichment_source}")
