#!/usr/bin/env python3
"""
Enhanced DataMapper Script with Llama Integration for Semantic Node Extraction

This script processes JSON, XML, AML, and EXM files containing Asset Administration Shell (AAS) data
and uses Llama to intelligently identify semantic node names from different file formats.

The Llama model analyzes file structures to determine which tags/attributes contain:
- Name: Semantic node name (e.g., "idShort" in JSON, "Name" in AML)
- Conceptual definition: Description/definition of the node
- Value: Actual data value
- Value type: Data type information
- Unit: Measurement unit

Supported file formats:
- JSON: AAS JSON format
- XML: AAS XML format
- AML: AutomationML format
- EXM: EXM format (treated as XML)
"""

import json
import csv
import os
import pickle
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

# Llama setup for local reasoning (replaces Gemini)
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

# Try transformers (Hugging Face) as fallback
if not LLAMA_AVAILABLE:
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        try:
            import torch
        except ImportError:
            torch = None
        LLAMA_BACKEND = 'transformers'
        llama_model_name = os.getenv("LLAMA_MODEL_NAME", "google/gemma-2-2b-it")
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


class LlamaTagIdentifier:
    """Uses Llama to identify semantic node tags in different file formats."""
    
    def __init__(self, use_llama: bool = True):
        self.use_llama = use_llama and LLAMA_AVAILABLE
        self.tag_cache = {}  # Cache Llama responses for similar file structures
    
    def identify_semantic_node_tags_json(self, sample_data: Dict, file_path: str) -> Dict[str, str]:
        """
        Use Gemini to identify which tags contain semantic node information in JSON files.
        
        Returns a mapping of semantic node attributes to JSON tags.
        """
        if not self.use_llama:
            # Fallback to known patterns
            return {
                "name": "idShort",
                "conceptual_definition": "description",
                "value": "value",
                "value_type": "valueType",
                "unit": "unit"
            }
        
        # Check cache first
        cache_key = f"json_{file_path}"
        if cache_key in self.tag_cache:
            return self.tag_cache[cache_key]
        
        # Create a sample snippet for Llama analysis (limit size)
        sample_snippet = json.dumps(sample_data, indent=2)[:2000]  # First 2000 chars
        
        prompt = f"""Analyze this JSON file structure and identify which tags/keys contain semantic node information.

File path: {file_path}
Sample structure:
{sample_snippet}

Based on the Asset Administration Shell (AAS) semantic node schema, identify which JSON keys contain:
1. Name: The semantic node name (typically "idShort" in AAS JSON)
2. Conceptual definition: Description/definition (typically in "description" array with language "en")
3. Value: The actual data value (typically "value")
4. Value type: Data type information (typically "valueType" or "dataType")
5. Unit: Measurement unit (typically "unit")

Respond in JSON format with this structure:
{{
    "name": "idShort",
    "conceptual_definition": "description",
    "value": "value",
    "value_type": "valueType",
    "unit": "unit"
}}

Only respond with the JSON object, no additional text."""

        try:
            # Use Llama instead of Gemini
            text = ""
            
            # Try Ollama backend
            if LLAMA_BACKEND == 'ollama':
                import requests
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                model_name = os.getenv("LLAMA_MODEL_NAME", "gemma3:4b")
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "max_tokens": 200
                        }
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "").strip()
            
            # Try llama-cpp-python backend
            elif LLAMA_BACKEND == 'llama_cpp' and LLAMA_MODEL:
                response = LLAMA_MODEL(
                    prompt,
                    max_tokens=200,
                    temperature=0.1,
                    stop=["\n\n"],
                    echo=False
                )
                if response and 'choices' in response and len(response['choices']) > 0:
                    text = response['choices'][0]['text'].strip()
                elif isinstance(response, str):
                    text = response.strip()
            
            # Try transformers backend
            elif LLAMA_BACKEND == 'transformers' and LLAMA_MODEL:
                import torch
                tokenizer = LLAMA_MODEL.get("tokenizer")
                model = LLAMA_MODEL.get("model")
                if tokenizer and model and torch:
                    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=200,
                            temperature=0.1,
                            do_sample=True,
                            pad_token_id=tokenizer.eos_token_id
                        )
                    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    if prompt in text:
                        text = text.split(prompt, 1)[1].strip()
            
            result_text = text.strip()
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            tag_mapping = json.loads(result_text)
            self.tag_cache[cache_key] = tag_mapping
            return tag_mapping
            
        except Exception as e:
            print(f"Warning: Llama tag identification failed: {e}")
            print("Falling back to default tag mapping for JSON files.")
            # Fallback to known patterns
            return {
                "name": "idShort",
                "conceptual_definition": "description",
                "value": "value",
                "value_type": "valueType",
                "unit": "unit"
            }
    
    def identify_semantic_node_tags_aml(self, sample_xml: str, file_path: str) -> Dict[str, str]:
        """
        Use Llama to identify which XML elements/attributes contain semantic node information in AML files.
        
        Returns a mapping of semantic node attributes to XML paths.
        """
        if not self.use_llama:
            # Fallback to known patterns
            return {
                "name": "Attribute[@Name]",
                "conceptual_definition": "Description",
                "value": "Value",
                "value_type": "AttributeDataType",
                "unit": ""
            }
        
        # Check cache first
        cache_key = f"aml_{file_path}"
        if cache_key in self.tag_cache:
            return self.tag_cache[cache_key]
        
        # Create a sample snippet for Llama analysis
        sample_snippet = sample_xml[:2000]  # First 2000 chars
        
        prompt = f"""Analyze this AutomationML (AML) XML file structure and identify which XML elements/attributes contain semantic node information.

File path: {file_path}
Sample structure:
{sample_snippet}

Based on the Asset Administration Shell (AAS) semantic node schema, identify which XML elements/attributes contain:
1. Name: The semantic node name (typically in Attribute[@Name] or RoleClass[@Name])
2. Conceptual definition: Description/definition (typically in Description element)
3. Value: The actual data value (typically in Value or DefaultValue element)
4. Value type: Data type information (typically in AttributeDataType attribute)
5. Unit: Measurement unit (may be in unit element or attribute)

Respond in JSON format with this structure:
{{
    "name": "Attribute[@Name]",
    "conceptual_definition": "Description",
    "value": "Value",
    "value_type": "AttributeDataType",
    "unit": "unit"
}}

Use XPath-like notation. Only respond with the JSON object, no additional text."""

        try:
            # Use Llama instead of Gemini
            text = ""
            
            # Try Ollama backend
            if LLAMA_BACKEND == 'ollama':
                import requests
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                model_name = os.getenv("LLAMA_MODEL_NAME", "gemma3:4b")
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "max_tokens": 200
                        }
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "").strip()
            
            # Try llama-cpp-python backend
            elif LLAMA_BACKEND == 'llama_cpp' and LLAMA_MODEL:
                response = LLAMA_MODEL(
                    prompt,
                    max_tokens=200,
                    temperature=0.1,
                    stop=["\n\n"],
                    echo=False
                )
                if response and 'choices' in response and len(response['choices']) > 0:
                    text = response['choices'][0]['text'].strip()
                elif isinstance(response, str):
                    text = response.strip()
            
            # Try transformers backend
            elif LLAMA_BACKEND == 'transformers' and LLAMA_MODEL:
                import torch
                tokenizer = LLAMA_MODEL.get("tokenizer")
                model = LLAMA_MODEL.get("model")
                if tokenizer and model and torch:
                    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=200,
                            temperature=0.1,
                            do_sample=True,
                            pad_token_id=tokenizer.eos_token_id
                        )
                    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    if prompt in text:
                        text = text.split(prompt, 1)[1].strip()
            
            result_text = text.strip()
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            tag_mapping = json.loads(result_text)
            self.tag_cache[cache_key] = tag_mapping
            return tag_mapping
            
        except Exception as e:
            print(f"Warning: Llama tag identification failed: {e}")
            print("Falling back to default tag mapping for AML files.")
            # Fallback to known patterns
            return {
                "name": "Attribute[@Name]",
                "conceptual_definition": "Description",
                "value": "Value",
                "value_type": "AttributeDataType",
                "unit": ""
            }


class EClassDescriptionLookup:
    """Loads and provides descriptions from ECLASS dictionary files."""
    
    def __init__(self, eclass_folder: str = "EClass"):
        self.eclass_folder = eclass_folder
        self.description_map: Dict[str, str] = {}
        self.loaded = False
        self.not_found_message = "No description found in ECLASS"
    
    def _get_cache_path(self) -> str:
        """Get the path to the cache file for the ECLASS folder."""
        folder_hash = hashlib.md5(self.eclass_folder.encode()).hexdigest()[:8]
        cache_dir = os.path.join(os.path.dirname(self.eclass_folder) if self.eclass_folder != "EClass" else ".", ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"eclass_descriptions_{folder_hash}.pkl")
    
    def _get_source_files_mtime(self) -> float:
        """Get the maximum modification time of all XML dictionary files."""
        if not os.path.exists(self.eclass_folder):
            return 0
        
        max_mtime = 0
        for root, _, files in os.walk(self.eclass_folder):
            if "dictionary" not in root.lower():
                continue
            for file_name in files:
                if file_name.lower().endswith(".xml"):
                    filepath = os.path.join(root, file_name)
                    try:
                        mtime = os.path.getmtime(filepath)
                        max_mtime = max(max_mtime, mtime)
                    except OSError:
                        pass
        return max_mtime
    
    def _load_from_cache(self, cache_path: str) -> Optional[Dict[str, str]]:
        """Load description map from cache if it exists and is valid."""
        if not os.path.exists(cache_path):
            return None
        
        try:
            # Load from cache without checking modification time
            # Cache is always used if it exists (user preference for performance)
            with open(cache_path, 'rb') as f:
                cached_map = pickle.load(f)
                print(f"Loaded ECLASS descriptions from cache ({len(cached_map)} entries)")
                return cached_map
        except Exception as e:
            print(f"Warning: Could not load ECLASS description cache: {e}")
            return None
    
    def _save_to_cache(self, cache_path: str, description_map: Dict[str, str]):
        """Save description map to cache."""
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(description_map, f)
            print(f"Saved ECLASS descriptions to cache ({len(description_map)} entries)")
        except Exception as e:
            print(f"Warning: Could not save ECLASS description cache: {e}")
    
    def _normalize(self, text: str) -> str:
        return "".join(ch.lower() for ch in text if ch.isalnum())
    
    def _local_name(self, tag: str) -> str:
        return tag.split('}')[-1] if '}' in tag else tag
    
    def _is_english(self, attrs: Dict[str, Any]) -> bool:
        language_code = attrs.get("language_code") or attrs.get("language") or ""
        return not language_code or language_code.lower().startswith("en")
    
    def _extract_label(self, parent: ET.Element) -> str:
        for child in parent:
            if self._local_name(child.tag) == "label" and self._is_english(child.attrib):
                text = (child.text or "").strip()
                if text:
                    return text
        return ""
    
    def _extract_all_labels(self, parent: ET.Element) -> List[str]:
        labels = []
        for child in parent:
            if self._local_name(child.tag) == "label" and self._is_english(child.attrib):
                text = (child.text or "").strip()
                if text:
                    labels.append(text)
        return labels
    
    def _extract_definition(self, elem: ET.Element) -> str:
        for child in elem:
            if self._local_name(child.tag) == "definition":
                for def_child in child:
                    if self._local_name(def_child.tag) == "text" and self._is_english(def_child.attrib):
                        text = (def_child.text or "").strip()
                        if text:
                            return text
        return ""
    
    def _process_property(self, property_elem: ET.Element) -> None:
        definition = self._extract_definition(property_elem)
        if not definition:
            return
        
        names = []
        for child in property_elem:
            local = self._local_name(child.tag)
            if local in {"preferred_name", "short_name"}:
                label = self._extract_label(child)
                if label:
                    names.append(label)
            elif local == "synonymous_names":
                names.extend(self._extract_all_labels(child))
        
        for name in names:
            normalized = self._normalize(name)
            if normalized and normalized not in self.description_map:
                self.description_map[normalized] = definition
    
    def _parse_dictionary_file(self, file_path: str) -> None:
        try:
            for _, elem in ET.iterparse(file_path, events=("end",)):
                if self._local_name(elem.tag) == "property":
                    self._process_property(elem)
                    elem.clear()
        except Exception as e:
            print(f"Warning: Failed to parse ECLASS file '{file_path}': {e}")
    
    def load_descriptions(self) -> None:
        if self.loaded:
            return
        
        if not os.path.exists(self.eclass_folder):
            print(f"ECLASS folder '{self.eclass_folder}' not found. Skipping ECLASS lookup.")
            self.loaded = True
            return
        
        # Try to load from cache first
        cache_path = self._get_cache_path()
        cached_map = self._load_from_cache(cache_path)
        
        if cached_map is not None:
            self.description_map = cached_map
            self.loaded = True
            return
        
        # Cache miss or invalid - load from XML files
        dictionary_files = []
        for root, _, files in os.walk(self.eclass_folder):
            if "dictionary" not in root.lower():
                continue
            for file_name in files:
                if file_name.lower().endswith(".xml"):
                    dictionary_files.append(os.path.join(root, file_name))
        
        if dictionary_files:
            print(f"Loading ECLASS descriptions from {len(dictionary_files)} XML file(s) (this may take a while)...")
            for file_path in dictionary_files:
                self._parse_dictionary_file(file_path)
            
            # Save to cache
            if self.description_map:
                self._save_to_cache(cache_path, self.description_map)
        
        self.loaded = True
    
    def get_description(self, node_name: str) -> str:
        if not node_name:
            return self.not_found_message
        
        normalized = self._normalize(node_name)
        if not normalized:
            return self.not_found_message
        
        if not self.loaded:
            self.load_descriptions()
        
        return self.description_map.get(normalized, self.not_found_message)


class SemanticNodeExtractorLlama:
    """Enhanced extractor with Llama-powered tag identification."""
    
    def __init__(self, data_folder: str = "Data", use_llama: bool = True):
        """
        Initialize the Llama-enhanced semantic node extractor.
        
        Args:
            data_folder: Path to folder containing source files (default: "Data")
            use_llama: Whether to use Llama for tag identification (default: True)
        """
        self.data_folder = data_folder
        self.semantic_nodes = []
        self.llama_identifier = LlamaTagIdentifier(use_llama=use_llama)
        self.eclass_lookup = EClassDescriptionLookup()
        self.json_tag_mapping = {}
        self.aml_tag_mapping = {}
    
    def extract_english_description(self, description_list: List[Dict]) -> str:
        """Extract English description from description list."""
        if not description_list:
            return ""
        
        for desc in description_list:
            if desc.get("language") == "en":
                return desc.get("text", "")
        
        # If no English found, return first available description
        if description_list:
            return description_list[0].get("text", "")
        
        return ""
    
    def apply_eclass_fallback(self, node_name: str, description: str) -> str:
        """Return existing description or fetch from ECLASS if missing."""
        if description:
            return description
        return self.eclass_lookup.get_description(node_name)
    
    def extract_value_from_element(self, element: Dict, tag_mapping: Dict) -> str:
        """Extract value from element using tag mapping."""
        value_key = tag_mapping.get("value", "value")
        
        # For Property elements
        if value_key in element and element.get("modelType") == "Property":
            value = element[value_key]
            if isinstance(value, str):
                return value
            elif isinstance(value, (int, float)):
                return str(value)
            else:
                return str(value)
        
        # For MultiLanguageProperty elements
        if value_key in element and element.get("modelType") == "MultiLanguageProperty":
            if isinstance(element[value_key], list):
                for val in element[value_key]:
                    if val.get("language") == "en":
                        return val.get("text", "")
                # If no English found, return first available
                if element[value_key]:
                    return element[value_key][0].get("text", "")
            return str(element[value_key])
        
        # For File elements
        if element.get("modelType") == "File":
            return element.get(value_key, "")
        
        # Check for value in qualifiers
        qualifiers = element.get("qualifiers", [])
        for qualifier in qualifiers:
            if qualifier.get("type") == "SMT/Cardinality" and "value" in qualifier:
                return qualifier["value"]
        
        return ""
    
    def extract_value_type(self, element: Dict, tag_mapping: Dict) -> str:
        """Extract value type using tag mapping."""
        value_type_key = tag_mapping.get("value_type", "valueType")
        return element.get(value_type_key, "")
    
    def extract_unit(self, element: Dict, tag_mapping: Dict) -> str:
        """Extract unit using tag mapping."""
        unit_key = tag_mapping.get("unit", "unit")
        if unit_key:
            return element.get(unit_key, "")
        return ""
    
    def extract_name_from_element(self, element: Dict, tag_mapping: Dict) -> str:
        """Extract semantic node name using tag mapping."""
        name_key = tag_mapping.get("name", "idShort")
        return element.get(name_key, "")
    
    def process_submodel_elements(self, elements: List[Dict], tag_mapping: Dict, parent_path: str = "") -> None:
        """Recursively process submodel elements to extract semantic nodes."""
        for element in elements:
            if not isinstance(element, dict):
                continue
            
            element_id = self.extract_name_from_element(element, tag_mapping)
            if not element_id:
                continue
            
            # Create full path for nested elements
            current_path = f"{parent_path}.{element_id}" if parent_path else element_id
            
            concept_key = tag_mapping.get("conceptual_definition", "description")
            raw_definition = self.extract_english_description(
                element.get(concept_key, [])
            )
            definition = self.apply_eclass_fallback(element_id, raw_definition)
            
            # Extract semantic node information
            semantic_node = {
                "Name": element_id,
                "Conceptual definition": definition,
                "Usage of data": "",
                "Value": self.extract_value_from_element(element, tag_mapping),
                "Value type": self.extract_value_type(element, tag_mapping),
                "Unit": self.extract_unit(element, tag_mapping),
                "Source description": ""
            }
            
            self.semantic_nodes.append(semantic_node)
            
            # Process nested elements recursively
            if "value" in element and isinstance(element["value"], list):
                self.process_submodel_elements(element["value"], tag_mapping, current_path)
            
            # Process submodelElements if present
            if "submodelElements" in element:
                self.process_submodel_elements(element["submodelElements"], tag_mapping, current_path)
            
            # Process value list elements (for SubmodelElementList)
            if element.get("modelType") == "SubmodelElementList" and "value" in element:
                if isinstance(element["value"], list):
                    self.process_submodel_elements(element["value"], tag_mapping, current_path)
    
    def process_concept_descriptions(self, concept_descriptions: List[Dict], tag_mapping: Dict) -> None:
        """Process concept descriptions to extract additional semantic information."""
        for concept in concept_descriptions:
            if not isinstance(concept, dict):
                continue
            
            concept_id = self.extract_name_from_element(concept, tag_mapping)
            if not concept_id:
                continue
            
            # Extract definition from embedded data specifications
            definition = ""
            value_type = ""
            unit = ""
            embedded_specs = concept.get("embeddedDataSpecifications", [])
            for spec in embedded_specs:
                if isinstance(spec, dict) and "dataSpecificationContent" in spec:
                    content = spec["dataSpecificationContent"]
                    if "definition" in content and isinstance(content["definition"], list):
                        for def_item in content["definition"]:
                            if def_item.get("language") == "en":
                                definition = def_item.get("text", "")
                                break
                    
                    # Extract value type from embedded specs
                    if "dataType" in content:
                        value_type = content["dataType"]
                    
                    # Extract unit from embedded specs
                    if "unit" in content:
                        unit = content["unit"]
            
            # If no definition found in embedded specs, use description
            if not definition:
                definition = self.extract_english_description(
                    concept.get(tag_mapping.get("conceptual_definition", "description"), [])
                )
            
            definition = self.apply_eclass_fallback(concept_id, definition)
            
            # Create semantic node for concept description
            semantic_node = {
                "Name": concept_id,
                "Conceptual definition": definition,
                "Usage of data": "",
                "Value": "",
                "Value type": value_type,
                "Unit": unit,
                "Source description": ""
            }
            
            self.semantic_nodes.append(semantic_node)
    
    def extract_aml_text_content(self, element: ET.Element) -> str:
        """Extract text content from AML element."""
        if element is None:
            return ""
        
        text = element.text or ""
        for child in element:
            child_text = self.extract_aml_text_content(child)
            if child_text:
                text += " " + child_text
        
        return text.strip()
    
    def extract_aml_value(self, element: ET.Element, tag_mapping: Dict) -> str:
        """Extract value from AML element using tag mapping."""
        value_path = tag_mapping.get("value", "Value")
        
        # Try Value element first
        value_elem = element.find(f".//{value_path}")
        if value_elem is not None:
            return self.extract_aml_text_content(value_elem)
        
        # Try DefaultValue element
        default_value_elem = element.find(".//DefaultValue")
        if default_value_elem is not None:
            return self.extract_aml_text_content(default_value_elem)
        
        return ""
    
    def extract_aml_data_type(self, element: ET.Element, tag_mapping: Dict) -> str:
        """Extract data type from AML element using tag mapping."""
        data_type_path = tag_mapping.get("value_type", "AttributeDataType")
        data_type_elem = element.find(f".//{data_type_path}")
        if data_type_elem is not None:
            return self.extract_aml_text_content(data_type_elem)
        return ""
    
    def extract_aml_name(self, element: ET.Element, tag_mapping: Dict) -> str:
        """Extract name from AML element using tag mapping."""
        name_path = tag_mapping.get("name", "Name")
        
        # Handle attribute notation like "Attribute[@Name]"
        if "@" in name_path:
            attr_name = name_path.split("@")[1].replace("]", "").replace("[", "")
            return element.get(attr_name, "")
        
        # Handle element notation
        name_elem = element.find(f".//{name_path}")
        if name_elem is not None:
            return self.extract_aml_text_content(name_elem)
        
        # Fallback to Name element
        name_elem = element.find(".//Name")
        if name_elem is not None:
            return self.extract_aml_text_content(name_elem)
        
        return ""
    
    def extract_aml_description(self, element: ET.Element, tag_mapping: Dict) -> str:
        """Extract description from AML element using tag mapping."""
        desc_path = tag_mapping.get("conceptual_definition", "Description")
        description_elem = element.find(f".//{desc_path}")
        if description_elem is not None:
            return self.extract_aml_text_content(description_elem)
        return ""
    
    def process_aml_interface_classes(self, interface_classes: List[ET.Element], tag_mapping: Dict, parent_path: str = "") -> None:
        """Recursively process AML interface classes to extract semantic nodes."""
        for interface_class in interface_classes:
            if interface_class is None:
                continue
            
            class_name = self.extract_aml_name(interface_class, tag_mapping)
            if not class_name:
                continue
            
            # Create full path for nested elements
            current_path = f"{parent_path}.{class_name}" if parent_path else class_name
            
            definition = self.apply_eclass_fallback(
                class_name,
                self.extract_aml_description(interface_class, tag_mapping)
            )
            
            # Extract semantic node information
            semantic_node = {
                "Name": class_name,
                "Conceptual definition": definition,
                "Usage of data": "",
                "Value": self.extract_aml_value(interface_class, tag_mapping),
                "Value type": self.extract_aml_data_type(interface_class, tag_mapping),
                "Unit": "",
                "Source description": ""
            }
            
            self.semantic_nodes.append(semantic_node)
            
            # Process nested interface classes
            nested_classes = interface_class.findall(".//InterfaceClass")
            if nested_classes:
                self.process_aml_interface_classes(nested_classes, tag_mapping, current_path)
            
            # Process attributes
            attributes = interface_class.findall(".//Attribute")
            for attribute in attributes:
                attr_name = self.extract_aml_name(attribute, tag_mapping)
                if attr_name:
                    attr_definition = self.apply_eclass_fallback(
                        attr_name,
                        self.extract_aml_description(attribute, tag_mapping)
                    )
                    attr_semantic_node = {
                        "Name": attr_name,
                        "Conceptual definition": attr_definition,
                        "Usage of data": "",
                        "Value": self.extract_aml_value(attribute, tag_mapping),
                        "Value type": self.extract_aml_data_type(attribute, tag_mapping),
                        "Unit": "",
                        "Source description": ""
                    }
                    
                    self.semantic_nodes.append(attr_semantic_node)
    
    def process_aml_file(self, file_path: str) -> None:
        """Process a single AML file and extract semantic nodes."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            print(f"Processing AML file: {os.path.basename(file_path)}")
            
            # Get tag mapping using Gemini
            sample_xml = ET.tostring(root, encoding='unicode')[:2000]
            tag_mapping = self.llama_identifier.identify_semantic_node_tags_aml(sample_xml, file_path)
            self.aml_tag_mapping = tag_mapping
            
            print(f"  Identified tag mapping: {tag_mapping}")
            
            # Process interface class libraries
            interface_class_libs = root.findall(".//InterfaceClassLib")
            for lib in interface_class_libs:
                interface_classes = lib.findall(".//InterfaceClass")
                self.process_aml_interface_classes(interface_classes, tag_mapping)
            
        except Exception as e:
            print(f"Error processing AML file {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def process_json_file(self, file_path: str) -> None:
        """Process a single JSON file and extract semantic nodes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"Processing JSON file: {os.path.basename(file_path)}")
            
            # Get tag mapping using Gemini
            tag_mapping = self.llama_identifier.identify_semantic_node_tags_json(data, file_path)
            self.json_tag_mapping = tag_mapping
            
            print(f"  Identified tag mapping: {tag_mapping}")
            
            # Process submodels
            submodels = data.get("submodels", [])
            for submodel in submodels:
                if isinstance(submodel, dict):
                    submodel_elements = submodel.get("submodelElements", [])
                    self.process_submodel_elements(submodel_elements, tag_mapping)
            
            # Process concept descriptions
            concept_descriptions = data.get("conceptDescriptions", [])
            self.process_concept_descriptions(concept_descriptions, tag_mapping)
            
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def process_all_files(self) -> None:
        """Process all supported files (JSON, XML, AML) in the data folder."""
        if not os.path.exists(self.data_folder):
            print(f"Data folder '{self.data_folder}' not found!")
            return
        
        # Find all supported file types
        json_files = [f for f in os.listdir(self.data_folder) if f.endswith('.json')]
        xml_files = [f for f in os.listdir(self.data_folder) if f.endswith('.xml')]
        aml_files = [f for f in os.listdir(self.data_folder) if f.endswith('.aml')]
        exm_files = [f for f in os.listdir(self.data_folder) if f.endswith('.exm')]
        simvsm_files = [f for f in os.listdir(self.data_folder) if f.endswith('.simvsm')]
        
        total_files = len(json_files) + len(xml_files) + len(aml_files) + len(exm_files) + len(simvsm_files)
        
        if total_files == 0:
            print(f"No supported files (JSON, XML, AML, EXM, SIMVSM) found in '{self.data_folder}' folder!")
            return
        
        print(f"Found {total_files} files to process:")
        if json_files:
            print(f"  JSON files ({len(json_files)}):")
            for file in json_files:
                print(f"    - {file}")
        if xml_files:
            print(f"  XML files ({len(xml_files)}):")
            for file in xml_files:
                print(f"    - {file}")
        if aml_files:
            print(f"  AML files ({len(aml_files)}):")
            for file in aml_files:
                print(f"    - {file}")
        if exm_files:
            print(f"  EXM files ({len(exm_files)}):")
            for file in exm_files:
                print(f"    - {file}")
        if simvsm_files:
            print(f"  SIMVSM files ({len(simvsm_files)}):")
            for file in simvsm_files:
                print(f"    - {file}")
        
        print("\nProcessing files...")
        
        # Process JSON files
        for json_file in json_files:
            file_path = os.path.join(self.data_folder, json_file)
            self.process_json_file(file_path)
        
        # Process AML files
        for aml_file in aml_files:
            file_path = os.path.join(self.data_folder, aml_file)
            self.process_aml_file(file_path)
        
        # Process XML files (if process_xml_file method exists)
        for xml_file in xml_files:
            file_path = os.path.join(self.data_folder, xml_file)
            if hasattr(self, 'process_xml_file'):
                self.process_xml_file(file_path)
        
        # Process EXM files (treat as XML)
        for exm_file in exm_files:
            file_path = os.path.join(self.data_folder, exm_file)
            if hasattr(self, 'process_xml_file'):
                self.process_xml_file(file_path)
        
        # Process SIMVSM files (treat as XML)
        for simvsm_file in simvsm_files:
            file_path = os.path.join(self.data_folder, simvsm_file)
            if hasattr(self, 'process_xml_file'):
                self.process_xml_file(file_path)
        
        print(f"\nExtracted {len(self.semantic_nodes)} semantic nodes total.")
    
    def save_to_csv(self, output_file: str = "semantic_nodes.csv") -> None:
        """Save extracted semantic nodes to CSV file."""
        if not self.semantic_nodes:
            print("No semantic nodes to save!")
            return
        
        fieldnames = [
            "Name", 
            "Conceptual definition", 
            "Usage of data", 
            "Value", 
            "Value type", 
            "Unit", 
            "Source description"
        ]
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.semantic_nodes)
            
            print(f"Semantic nodes saved to '{output_file}'")
            print(f"Total rows: {len(self.semantic_nodes)}")
            
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
    
    def print_summary(self) -> None:
        """Print a summary of extracted semantic nodes."""
        if not self.semantic_nodes:
            print("No semantic nodes extracted!")
            return
        
        print(f"\n=== SEMANTIC NODES SUMMARY ===")
        print(f"Total semantic nodes: {len(self.semantic_nodes)}")
        
        # Count nodes with values
        nodes_with_values = sum(1 for node in self.semantic_nodes if node["Value"])
        print(f"Nodes with values: {nodes_with_values}")
        
        # Count nodes with value types
        nodes_with_value_types = sum(1 for node in self.semantic_nodes if node["Value type"])
        print(f"Nodes with value types: {nodes_with_value_types}")
        
        # Count nodes with units
        nodes_with_units = sum(1 for node in self.semantic_nodes if node["Unit"])
        print(f"Nodes with units: {nodes_with_units}")
        
        print(f"\n=== SAMPLE SEMANTIC NODES ===")
        for i, node in enumerate(self.semantic_nodes[:5]):  # Show first 5 nodes
            print(f"\nNode {i+1}:")
            for key, value in node.items():
                if value:  # Only show non-empty values
                    print(f"  {key}: {value}")


def main():
    """Main function to run the semantic node extractor with Llama."""
    print("=== Semantic Node DataMapper with Llama Integration ===")
    print("Extracting semantic nodes from AAS files using Llama for tag identification...\n")
    
    # Check if Llama is available
    if not LLAMA_AVAILABLE:
        print("Warning: Llama not configured. Running in fallback mode without LLM assistance.")
        print("To enable Llama features, install Ollama or set LLAMA_MODEL_PATH.")
        print()
    
    # Initialize extractor
    extractor = SemanticNodeExtractorLlama(data_folder="Data", use_llama=LLAMA_AVAILABLE)
    
    # Process all supported files
    extractor.process_all_files()
    
    # Print summary
    extractor.print_summary()
    
    # Save to CSV
    extractor.save_to_csv()
    
    print("\n=== Processing Complete ===")


if __name__ == "__main__":
    main()

