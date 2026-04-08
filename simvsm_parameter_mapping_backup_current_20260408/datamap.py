#!/usr/bin/env python3
"""
DataMapper Script for Semantic Node Extraction

This script processes JSON, XML, AML, and EXM files containing Asset Administration Shell (AAS) data
and extracts semantic node information according to the specified mapping:

- Name: idShort/Name from source files
- Conceptual definition: description in English from source files
- Usage of data: (blank - not in source files)
- Value: value from source files (if none, keep blank)
- Value type: valueType/dataType from source files (if none, keep blank)
- Unit: unit from source files (if none, keep blank)
- Source description: (blank column)

AAS hierarchy-aware extraction (default for AAS JSON):
- Extracts by structure: Submodel -> SubmodelElement -> Type (template) -> Properties/Collections.
- One node per submodel, per top-level submodel element, per type (e.g. Process__00__), and per
  direct child (properties and one node per nested collection without recursing).
- Stores derivation and relationship in _metadata: aas_path, parent_id, role (submodel |
  submodel_element | type | property | collection), source_file.
- Node count varies by number of files and structure size (no fixed cap).

Supported file formats:
- JSON: AAS JSON format
- XML: AAS XML format
- AML: AutomationML format
- EXM: EXM format (treated as XML)
- SIMVSM: SIMVSM format (treated as XML)
"""

import json
import csv
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any


def _is_aas_json(data: Dict) -> bool:
    """Return True if the JSON is an AAS structure (has submodels and submodelElements)."""
    if not isinstance(data, dict):
        return False
    submodels = data.get("submodels", [])
    if not submodels or not isinstance(submodels, list):
        return False
    for sm in submodels:
        if isinstance(sm, dict) and "submodelElements" in sm:
            return True
    return False


def _is_project_json(data: Dict) -> bool:
    """Return True if the JSON is a project/GraphLinksModel (SIMVSM-style) with alternatives and nodeDataArray."""
    if not isinstance(data, dict):
        return False
    alternatives = data.get("alternatives", [])
    if not alternatives or not isinstance(alternatives, list):
        return False
    first = alternatives[0]
    if not isinstance(first, dict):
        return False
    model = first.get("model", {})
    if not isinstance(model, dict):
        return False
    return "nodeDataArray" in model and isinstance(model.get("nodeDataArray"), list)


# No built-in glossary: extraction only. Descriptions/units come from support files or enrichment.


def _simvsm_param_extract_only(param_class: str, param_type: str) -> Dict[str, str]:
    """Return empty definition/usage/unit for a SimvSM parameter. Extract nodes only; support files/enrichment fill details."""
    return {
        "conceptual_definition": "",
        "usage_of_data": "",
        "unit": "",
        "source_description": "",
    }


class SemanticNodeExtractor:
    """Extracts semantic node information from AAS JSON, XML, AML, EXM, and SIMVSM files."""
    
    def __init__(self, data_folder: str = "data", aas_hierarchy_aware: bool = True):
        self.data_folder = data_folder
        self.semantic_nodes = []
        self.instance_values = {}  # Store separate parameter values for each node instance
        # When True, AAS JSON is extracted by submodel → submodel element → type → elements (cap ~100 nodes)
        self.aas_hierarchy_aware = aas_hierarchy_aware
    
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
    
    def extract_value_from_element(self, element: Dict) -> str:
        """Extract value from different types of elements."""
        # For Property elements
        if "value" in element and element.get("modelType") == "Property":
            value = element["value"]
            if isinstance(value, str):
                return value
            elif isinstance(value, (int, float)):
                return str(value)
            else:
                return str(value)
        
        # For MultiLanguageProperty elements
        if "value" in element and element.get("modelType") == "MultiLanguageProperty":
            if isinstance(element["value"], list):
                for val in element["value"]:
                    if val.get("language") == "en":
                        return val.get("text", "")
                # If no English found, return first available
                if element["value"]:
                    return element["value"][0].get("text", "")
            return str(element["value"])
        
        # For File elements
        if element.get("modelType") == "File":
            return element.get("value", "")
        
        # Check for value in qualifiers (some values might be in qualifiers)
        qualifiers = element.get("qualifiers", [])
        for qualifier in qualifiers:
            if qualifier.get("type") == "SMT/Cardinality" and "value" in qualifier:
                return qualifier["value"]
        
        return ""
    
    def extract_value_type(self, element: Dict) -> str:
        """Extract value type from element."""
        return element.get("valueType", "")
    
    def extract_unit(self, element: Dict) -> str:
        """Extract unit from element."""
        return element.get("unit", "")
    
    def _aas_node(
        self,
        name: str,
        description: str,
        parent_path: str,
        role: str,
        source_file: str,
        value: str = "",
        value_type: str = "",
        unit: str = "",
        parent_id: str = "",
    ) -> Dict:
        """Build one semantic node dict with AAS hierarchy metadata for mapping."""
        node = {
            "Name": name,
            "Conceptual definition": description,
            "Usage of data": "",
            "Value": value,
            "Value type": value_type or "",
            "Unit": unit,
            "Source description": "",
        }
        meta = {
            "aas_path": parent_path,
            "role": role,
            "source_file": source_file,
        }
        if parent_id:
            meta["parent_id"] = parent_id
        node["_metadata"] = meta
        if source_file:
            node["Source file"] = source_file
        return node

    def _build_concept_definition_map(self, data: Dict) -> Dict[str, str]:
        """Build idShort/id -> definition map from conceptDescriptions (embeddedDataSpecifications.definition)."""
        out = {}
        for concept in data.get("conceptDescriptions") or []:
            if not isinstance(concept, dict):
                continue
            definition = ""
            for spec in concept.get("embeddedDataSpecifications") or []:
                if not isinstance(spec, dict):
                    continue
                content = spec.get("dataSpecificationContent") or {}
                for def_item in (content.get("definition") or []):
                    if isinstance(def_item, dict) and (def_item.get("language") or "").strip().lower() in ("en", "en-us"):
                        definition = (def_item.get("text") or "").strip()
                        break
                if definition:
                    break
            if not definition:
                definition = self.extract_english_description(concept.get("description", []))
            if not definition:
                continue
            id_short = (concept.get("idShort") or "").strip()
            concept_id = (concept.get("id") or "").strip()
            if id_short:
                out[id_short] = definition
            if concept_id:
                out[concept_id] = definition
                # also key by base URL without version suffix so semanticId "https://.../workstationid/1/0" matches concept id "https://.../workstationid"
                if "/" in concept_id:
                    out[concept_id.rstrip("/")] = definition
        return out

    def _process_aas_json_full_hierarchy(self, data: Dict, file_path: str) -> None:
        """
        Extract all nodes from one AAS JSON using full recursion (same as aas_hierarchy_extract).
        Ensures files like QualityControlForMachining yield ~185 nodes, not just top-level 7.
        Uses conceptDescriptions for definition when the element has no inline description (e.g. WorkstationId).
        """
        try:
            from aas_hierarchy_extract import extract_from_json
        except ImportError:
            self._process_aas_json_hierarchy_one_file(data, file_path)
            return
        file_basename = os.path.basename(file_path)
        rows, _ = extract_from_json(data, expand_first_only=True)
        concept_definitions = self._build_concept_definition_map(data)
        for row in rows:
            parent = (row.get("Parent Path") or "").strip()
            id_short = (row.get("idShort") or "").strip()
            model_type = (row.get("ModelType") or "").strip()
            semantic_id = (row.get("SemanticID") or "").strip()
            value = (row.get("Value") or "").strip()
            value_type = (row.get("ValueType") or "").strip()
            if not parent and not id_short and not model_type:
                continue
            name = id_short if id_short else (parent.split(" > ")[-1] if parent else "Unnamed")
            if not name:
                name = "Unnamed"
            # Use description from element, then from same file's conceptDescriptions (definitions in the file are read by default).
            # Set USE_CONCEPT_DESCRIPTIONS_FROM_SOURCE=0 to leave conceptual definition for support files/Llama only.
            description = (row.get("Description") or "").strip()
            use_concept_from_source = os.environ.get("USE_CONCEPT_DESCRIPTIONS_FROM_SOURCE", "1").strip().lower() in ("1", "true", "yes")
            if not description and use_concept_from_source and concept_definitions:
                description = (
                    concept_definitions.get(id_short)
                    or concept_definitions.get(semantic_id)
                    or concept_definitions.get(semantic_id.rstrip("/"))
                    or (concept_definitions.get(semantic_id.rsplit("/", 1)[0]) if "/" in semantic_id else None)
                ) or ""
            if not description:
                description = f"{parent} | {model_type}".strip() or model_type
                if semantic_id:
                    description = f"{description} | {semantic_id}"
            role = model_type or "property"
            parent_id = parent.split(" > ")[-1] if parent else ""
            node = self._aas_node(
                name=name,
                description=description,
                parent_path=parent or name,
                role=role,
                source_file=file_basename,
                parent_id=parent_id,
                value=value,
                value_type=value_type or "String",
                unit="",
            )
            self.semantic_nodes.append(node)

    def _process_aas_json_hierarchy_one_file(self, data: Dict, file_path: str) -> None:
        """
        Extract nodes from one AAS JSON file using hierarchy: Submodel → SubmodelElement → Type → elements.
        Does not recurse into every nested SMC; one node per submodel, per top-level element, per type, per property/collection.
        Node count depends on file structure (no fixed cap).
        (Used as fallback if aas_hierarchy_extract is not available.)
        """
        file_basename = os.path.basename(file_path)
        submodels = data.get("submodels", [])
        for submodel in submodels:
            if not isinstance(submodel, dict):
                continue
            sm_id = submodel.get("idShort", "")
            if not sm_id:
                continue
            sm_desc = self.extract_english_description(submodel.get("description", []))
            sm_path = sm_id
            node = self._aas_node(
                name=sm_id,
                description=sm_desc,
                parent_path=sm_path,
                role="submodel",
                source_file=file_basename,
                parent_id="",
            )
            self.semantic_nodes.append(node)

            elements = submodel.get("submodelElements", [])
            for elem in elements:
                if not isinstance(elem, dict):
                    continue
                elem_id = elem.get("idShort", "")
                if not elem_id:
                    continue
                elem_desc = self.extract_english_description(elem.get("description", []))
                elem_path = f"{sm_path}.{elem_id}"
                node = self._aas_node(
                    name=elem_id,
                    description=elem_desc,
                    parent_path=elem_path,
                    role="submodel_element",
                    source_file=file_basename,
                    parent_id=sm_id,
                )
                self.semantic_nodes.append(node)

                model_type = elem.get("modelType", "")
                value_list = elem.get("value", []) if isinstance(elem.get("value"), list) else []
                # SubmodelElementCollection with a single template (type) in value, e.g. Process__00__
                if model_type == "SubmodelElementCollection" and len(value_list) == 1:
                    template = value_list[0]
                    if not isinstance(template, dict):
                        continue
                    type_id = template.get("idShort", "")
                    if not type_id:
                        continue
                    type_desc = self.extract_english_description(
                        template.get("description", [])
                    )
                    type_path = f"{elem_path}.{type_id}"
                    type_node = self._aas_node(
                        name=type_id,
                        description=type_desc,
                        parent_path=type_path,
                        role="type",
                        source_file=file_basename,
                        parent_id=elem_id,
                    )
                    self.semantic_nodes.append(type_node)

                    children = template.get("value", [])
                    if not isinstance(children, list):
                        children = []
                    for child in children:
                        if not isinstance(child, dict):
                            continue
                        child_id = child.get("idShort", "")
                        if not child_id:
                            continue
                        child_desc = self.extract_english_description(
                            child.get("description", [])
                        )
                        child_path = f"{type_path}.{child_id}"
                        child_model = child.get("modelType", "")
                        if child_model in ("Property", "MultiLanguageProperty"):
                            node = self._aas_node(
                                name=child_id,
                                description=child_desc,
                                parent_path=child_path,
                                role="property",
                                source_file=file_basename,
                                parent_id=type_id,
                                value=self.extract_value_from_element(child),
                                value_type=self.extract_value_type(child),
                                unit=self.extract_unit(child),
                            )
                            self.semantic_nodes.append(node)
                        elif child_model == "SubmodelElementCollection":
                            node = self._aas_node(
                                name=child_id,
                                description=child_desc,
                                parent_path=child_path,
                                role="collection",
                                source_file=file_basename,
                                parent_id=type_id,
                            )
                            self.semantic_nodes.append(node)
                        # else: other types (Reference, etc.) can be added as one node if needed

    def _project_value_to_str(self, val: Any) -> str:
        """Convert a parameter value to string for semantic node Value field."""
        if val is None:
            return ""
        if isinstance(val, (str, int, float)):
            return str(val)
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, dict):
            return json.dumps(val, ensure_ascii=False)
        if isinstance(val, list):
            return json.dumps(val, ensure_ascii=False)
        return str(val)

    def _process_project_json_one_file(self, data: Dict, file_path: str) -> None:
        """
        Extract properties and metadata from project/GraphLinksModel JSON (e.g. SIMVSM value-stream).
        Produces semantic nodes for mapping to target: one node per process (node), one per parameter
        with Name, Value, Value type, and _metadata (parent_id, role, source_file, project_path).
        """
        file_basename = os.path.basename(file_path)
        project_name = data.get("name", "") or "Project"
        project_desc = (data.get("description") or "").strip()
        # Project-level node: extract only; support files/enrichment fill description
        proj_node = {
            "Name": project_name,
            "Conceptual definition": project_desc,
            "Usage of data": "",
            "Value": "",
            "Value type": "",
            "Unit": "",
            "Source description": "",
            "Source file": file_basename,
            "_metadata": {
                "aas_path": project_name,
                "role": "project",
                "source_file": file_basename,
                "parent_id": "",
            },
        }
        self.semantic_nodes.append(proj_node)

        alternatives = data.get("alternatives", [])
        if not isinstance(alternatives, list):
            return
        for alt_idx, alt in enumerate(alternatives):
            if not isinstance(alt, dict):
                continue
            alt_name = alt.get("name", "") or f"Alternative_{alt_idx}"
            model = alt.get("model", {})
            if not isinstance(model, dict):
                continue
            node_data_array = model.get("nodeDataArray", [])
            if not isinstance(node_data_array, list):
                continue
            for node in node_data_array:
                if not isinstance(node, dict):
                    continue
                node_key = node.get("key", "")
                node_name = node.get("nodeName", "") or node.get("class", "") or f"Node_{node_key}"
                node_class = node.get("class", "")
                category = node.get("category", "")
                loc = node.get("loc", "")
                path = f"{project_name}.{alt_name}.{node_name}"

                node_meta = {
                    "aas_path": path,
                    "role": "process",
                    "source_file": file_basename,
                    "parent_id": project_name,
                    "class": node_class,
                    "category": category,
                    "key": node_key,
                    "loc": loc,
                }
                node_semantic = {
                    "Name": node_name,
                    "Conceptual definition": "",
                    "Usage of data": "",
                    "Value": "",
                    "Value type": "process",
                    "Unit": "",
                    "Source description": "",
                    "Source file": file_basename,
                    "_metadata": node_meta,
                }
                self.semantic_nodes.append(node_semantic)

                parameters = node.get("parameters", [])
                if not isinstance(parameters, list):
                    continue
                for param in parameters:
                    if not isinstance(param, dict):
                        continue
                    param_class = param.get("class", "") or "Parameter"
                    param_type = param.get("type", "string")
                    param_value = param.get("value")
                    value_str = self._project_value_to_str(param_value)
                    param_path = f"{path}.{param_class}"
                    simvsm_info = _simvsm_param_extract_only(param_class, param_type)
                    
                    # Store instance-specific parameter value
                    instance_id_key = f"{node_class}_{node_key}"
                    if instance_id_key not in self.instance_values:
                        self.instance_values[instance_id_key] = {
                            "class": node_class,
                            "key": node_key,
                            "name": node_name,
                            "parameters": {}
                        }
                    self.instance_values[instance_id_key]["parameters"][param_class] = value_str

                    param_meta = {
                        "aas_path": param_path,
                        "role": "property",
                        "source_file": file_basename,
                        "parent_id": node_name,
                        "parameter_class": param_class,
                        "parameter_type": param_type,
                    }
                    param_semantic = {
                        "Name": param_class,
                        "Conceptual definition": simvsm_info["conceptual_definition"],
                        "Usage of data": simvsm_info["usage_of_data"],
                        "Value": value_str,
                        "Value type": param_type,
                        "Unit": simvsm_info["unit"],
                        "Source description": simvsm_info["source_description"],
                        "Source file": file_basename,
                        "_metadata": param_meta,
                    }
                    self.semantic_nodes.append(param_semantic)

    def process_submodel_elements(self, elements: List[Dict], parent_path: str = "") -> None:
        """Recursively process submodel elements to extract semantic nodes."""
        for element in elements:
            if not isinstance(element, dict):
                continue
            
            element_id = element.get("idShort", "")
            if not element_id:
                continue
            
            # Create full path for nested elements
            current_path = f"{parent_path}.{element_id}" if parent_path else element_id
            
            # Extract semantic node information
            semantic_node = {
                "Name": element_id,
                "Conceptual definition": self.extract_english_description(element.get("description", [])),
                "Usage of data": "",  # Always blank as per requirements
                "Value": self.extract_value_from_element(element),
                "Value type": self.extract_value_type(element),
                "Unit": self.extract_unit(element),
                "Source description": ""  # Always blank as per requirements
            }
            
            self.semantic_nodes.append(semantic_node)
            
            # Process nested elements recursively
            if "value" in element and isinstance(element["value"], list):
                self.process_submodel_elements(element["value"], current_path)
            
            # Process submodelElements if present
            if "submodelElements" in element:
                self.process_submodel_elements(element["submodelElements"], current_path)
            
            # Process value list elements (for SubmodelElementList)
            if element.get("modelType") == "SubmodelElementList" and "value" in element:
                if isinstance(element["value"], list):
                    self.process_submodel_elements(element["value"], current_path)
    
    def process_concept_descriptions(self, concept_descriptions: List[Dict]) -> None:
        """Process concept descriptions to extract additional semantic information."""
        for concept in concept_descriptions:
            if not isinstance(concept, dict):
                continue
            
            concept_id = concept.get("idShort", "")
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
                definition = self.extract_english_description(concept.get("description", []))
            
            # Create semantic node for concept description
            semantic_node = {
                "Name": concept_id,
                "Conceptual definition": definition,
                "Usage of data": "",  # Always blank as per requirements
                "Value": "",  # Concept descriptions typically don't have values
                "Value type": value_type,  # Extract from embedded specs
                "Unit": unit,  # Extract from embedded specs
                "Source description": ""  # Always blank as per requirements
            }
            
            self.semantic_nodes.append(semantic_node)
    
    def extract_xml_text_content(self, element: ET.Element) -> str:
        """Extract text content from XML element, handling nested elements."""
        if element is None:
            return ""
        
        # Get direct text content
        text = element.text or ""
        
        # Get text from all child elements
        for child in element:
            child_text = self.extract_xml_text_content(child)
            if child_text:
                text += " " + child_text
        
        return text.strip()
    
    def extract_xml_description(self, element: ET.Element, namespace: str = None) -> str:
        """Extract description from XML element, looking for English descriptions."""
        if namespace is None:
            # Try both AAS 2.0 and 3.0
            namespaces = [
                "http://www.admin-shell.io/aas/2/0",
                "https://admin-shell.io/aas/3/0"
            ]
        else:
            namespaces = [namespace]
        
        for ns in namespaces:
            # Look for description elements
            description_elem = element.find(f".//{{{ns}}}description")
            if description_elem is not None:
                # AAS 3.0: description can be direct text or langString
                if ns == "https://admin-shell.io/aas/3/0":
                    # Try langString first (if it exists)
                    lang_elem = description_elem.find(f".//{{{ns}}}langString[@language='en']")
                    if lang_elem is not None:
                        return self.extract_xml_text_content(lang_elem)
                    # Try any langString
                    lang_elem = description_elem.find(f".//{{{ns}}}langString")
                    if lang_elem is not None:
                        return self.extract_xml_text_content(lang_elem)
                    # Direct text content (AAS 3.0 can have direct text)
                    if description_elem.text:
                        return description_elem.text.strip()
                    # Try extracting all text content
                    text = self.extract_xml_text_content(description_elem)
                    if text:
                        return text
                else:
                    # AAS 2.0: Look for English language description
                    lang_elem = description_elem.find(".//{http://www.admin-shell.io/aas_common/2/0}langString[@language='en']")
                    if lang_elem is not None:
                        return self.extract_xml_text_content(lang_elem)
                    
                    # If no English found, get first available description
                    lang_elem = description_elem.find(".//{http://www.admin-shell.io/aas_common/2/0}langString")
                    if lang_elem is not None:
                        return self.extract_xml_text_content(lang_elem)
        
        return ""
    
    def extract_xml_value(self, element: ET.Element, namespace: str = None) -> str:
        """Extract value from XML element."""
        if namespace is None:
            namespaces = [
                "http://www.admin-shell.io/aas/2/0",
                "https://admin-shell.io/aas/3/0"
            ]
        else:
            namespaces = [namespace]
        
        for ns in namespaces:
            # Look for value element
            value_elem = element.find(f".//{{{ns}}}value")
            if value_elem is not None:
                return self.extract_xml_text_content(value_elem)
            
            # Look for value in qualifiers (AAS 2.0)
            if ns == "http://www.admin-shell.io/aas/2/0":
                qualifier_elem = element.find(f".//{{{ns}}}qualifier")
                if qualifier_elem is not None:
                    value_elem = qualifier_elem.find(f".//{{{ns}}}value")
                    if value_elem is not None:
                        return self.extract_xml_text_content(value_elem)
        
        return ""
    
    def extract_xml_value_type(self, element: ET.Element, namespace: str = None) -> str:
        """Extract value type from XML element."""
        if namespace is None:
            namespaces = [
                "http://www.admin-shell.io/aas/2/0",
                "https://admin-shell.io/aas/3/0"
            ]
        else:
            namespaces = [namespace]
        
        for ns in namespaces:
            value_type_elem = element.find(f".//{{{ns}}}valueType")
            if value_type_elem is not None:
                return self.extract_xml_text_content(value_type_elem)
        return ""
    
    def extract_xml_unit(self, element: ET.Element, namespace: str = None) -> str:
        """Extract unit from XML element."""
        if namespace is None:
            namespaces = [
                "http://www.admin-shell.io/aas/2/0",
                "https://admin-shell.io/aas/3/0"
            ]
        else:
            namespaces = [namespace]
        
        # First, try iterating through direct children (most reliable)
        for child in element:
            # Check if this child is a unit element (handle both with and without namespace)
            tag = child.tag
            if tag.endswith('}unit') or tag == 'unit' or 'unit' in tag.lower():
                # Extract namespace from tag if present
                if '}' in tag:
                    ns_from_tag = tag.split('}')[0][1:]  # Remove leading {
                    if ns_from_tag in namespaces or namespace is None:
                        return self.extract_xml_text_content(child)
                else:
                    # No namespace, try to match
                    return self.extract_xml_text_content(child)
        
        # Fallback: try namespace-based search
        for ns in namespaces:
            # Try direct child first (most common case)
            unit_elem = element.find(f"{{{ns}}}unit")
            if unit_elem is not None:
                return self.extract_xml_text_content(unit_elem)
            # Try descendant search as fallback
            unit_elem = element.find(f".//{{{ns}}}unit")
            if unit_elem is not None:
                return self.extract_xml_text_content(unit_elem)
        return ""
    
    def process_xml_property_aas3(self, prop: ET.Element, namespace: str, asset_id_short: str = "", submodel_id_short: str = "") -> None:
        """Process AAS 3.0 property element. Optionally pass asset and submodel context for accurate enrichment."""
        if prop is None:
            return
        
        # Get idShort
        id_short_elem = prop.find(f".//{{{namespace}}}idShort")
        if id_short_elem is None:
            return
        
        element_id = self.extract_xml_text_content(id_short_elem)
        if not element_id:
            return
        
        # Extract semanticId (eClass ID) if present
        semantic_id = ""
        semantic_id_elem = prop.find(f".//{{{namespace}}}semanticId")
        if semantic_id_elem is not None:
            value_elem = semantic_id_elem.find(f".//{{{namespace}}}value")
            if value_elem is not None:
                semantic_id = self.extract_xml_text_content(value_elem)
        
        # Extract semantic node information
        semantic_node = {
            "Name": element_id,
            "Conceptual definition": self.extract_xml_description(prop, namespace),
            "Usage of data": "",  # Always blank as per requirements
            "Value": self.extract_xml_value(prop, namespace) or semantic_id,  # Use semanticId as value if no value
            "Value type": self.extract_xml_value_type(prop, namespace),
            "Unit": self.extract_xml_unit(prop, namespace),
            "Source description": ""  # Always blank as per requirements
        }
        # Store asset/submodel context so enrichment (OpenAI, eClass, support docs) can use it
        if asset_id_short:
            semantic_node["Source asset"] = asset_id_short
        if submodel_id_short:
            semantic_node["Source submodel"] = submodel_id_short
        
        # Store eClass ID and context in metadata if present
        meta = {}
        if semantic_id:
            meta["eclass_id"] = semantic_id
        if asset_id_short:
            meta["source_asset"] = asset_id_short
        if submodel_id_short:
            meta["source_submodel"] = submodel_id_short
        if meta:
            semantic_node["_metadata"] = meta
        
        self.semantic_nodes.append(semantic_node)
    
    def _process_opcua_file(self, root: ET.Element, file_path: str) -> None:
        """Extract semantic nodes from OPC UA UANodeSet XML (UAVariable)."""
        def local_tag(elem):
            return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        count = 0
        for elem in root.iter():
            if local_tag(elem) != "UAVariable":
                continue
            # BrowseName: e.g. "1:NominalVoltage" -> use "NominalVoltage"
            name = ""
            for child in elem:
                if local_tag(child) == "BrowseName":
                    name = (child.text or "").strip()
                    break
            if not name and elem.get("BrowseName"):
                name = elem.get("BrowseName", "")
            if not name:
                continue
            if ":" in name:
                name = name.split(":", 1)[-1].strip()
            # DisplayName
            display_name = ""
            for child in elem:
                if local_tag(child) == "DisplayName":
                    display_name = (child.text or "").strip()
                    break
            # Description
            desc = ""
            for child in elem:
                if local_tag(child) == "Description":
                    desc = (child.text or "").strip()
                    break
            # Value: <Value><uax:Float>24.0</uax:Float></Value>
            value = ""
            for child in elem:
                if local_tag(child) == "Value":
                    for vchild in child:
                        value = (vchild.text or "").strip()
                        if value:
                            break
                    if not value and child.text:
                        value = (child.text or "").strip()
                    break
            # DataType attribute
            value_type = elem.get("DataType", "Float")
            if value_type and "=" in str(value_type):
                value_type = str(value_type).split("=")[-1].strip()
            semantic_node = {
                "Name": name,
                "Conceptual definition": desc,
                "Usage of data": "",
                "Value": value,
                "Value type": value_type or "String",
                "Unit": "",
                "Source description": display_name or ""
            }
            self.semantic_nodes.append(semantic_node)
            count += 1
        if count > 0:
            print(f"  [OK] Extracted {count} node(s) from OPC UA (UAVariable)")
    
    def process_xml_submodel_elements(self, elements: List[ET.Element], namespace: str = "http://www.admin-shell.io/aas/2/0", parent_path: str = "") -> None:
        """Recursively process XML submodel elements to extract semantic nodes."""
        for element in elements:
            if element is None:
                continue
            
            # Get element name (idShort)
            id_short_elem = element.find(f".//{{{namespace}}}idShort")
            if id_short_elem is None:
                continue
            
            element_id = self.extract_xml_text_content(id_short_elem)
            if not element_id:
                continue
            
            # Create full path for nested elements
            current_path = f"{parent_path}.{element_id}" if parent_path else element_id
            
            # Extract semantic node information
            semantic_node = {
                "Name": element_id,
                "Conceptual definition": self.extract_xml_description(element, namespace),
                "Usage of data": "",  # Always blank as per requirements
                "Value": self.extract_xml_value(element, namespace),
                "Value type": self.extract_xml_value_type(element, namespace),
                "Unit": self.extract_xml_unit(element, namespace),
                "Source description": ""  # Always blank as per requirements
            }
            
            self.semantic_nodes.append(semantic_node)
            
            # Process nested elements recursively
            submodel_elements = element.findall(f".//{{{namespace}}}submodelElement")
            if submodel_elements:
                self.process_xml_submodel_elements(submodel_elements, namespace, current_path)
    
    def process_xml_concept_descriptions(self, concept_descriptions: List[ET.Element], namespace: str = "http://www.admin-shell.io/aas/2/0") -> None:
        """Process XML concept descriptions to extract additional semantic information."""
        for concept in concept_descriptions:
            if concept is None:
                continue
            
            # Get concept ID
            id_short_elem = concept.find(f".//{{{namespace}}}idShort")
            if id_short_elem is None:
                continue
            
            concept_id = self.extract_xml_text_content(id_short_elem)
            if not concept_id:
                continue
            
            # Extract definition from embedded data specifications
            definition = self.extract_xml_description(concept, namespace)
            value_type = ""
            unit = ""
            
            # Look for embedded data specifications
            embedded_specs = concept.findall(f".//{{{namespace}}}embeddedDataSpecification")
            for spec in embedded_specs:
                data_spec_content = spec.find(f".//{{{namespace}}}dataSpecificationContent")
                if data_spec_content is not None:
                    # Extract value type
                    data_type_elem = data_spec_content.find(f".//{{{namespace}}}dataType")
                    if data_type_elem is not None:
                        value_type = self.extract_xml_text_content(data_type_elem)
                    
                    # Extract unit
                    unit_elem = data_spec_content.find(f".//{{{namespace}}}unit")
                    if unit_elem is not None:
                        unit = self.extract_xml_text_content(unit_elem)
            
            # Create semantic node for concept description
            semantic_node = {
                "Name": concept_id,
                "Conceptual definition": definition,
                "Usage of data": "",  # Always blank as per requirements
                "Value": "",  # Concept descriptions typically don't have values
                "Value type": value_type,
                "Unit": unit,
                "Source description": ""  # Always blank as per requirements
            }
            
            self.semantic_nodes.append(semantic_node)
    
    def process_xml_file(self, file_path: str) -> None:
        """Process a single XML file and extract semantic nodes (AAS or OPC UA)."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            print(f"Processing XML file: {os.path.basename(file_path)}")
            
            # Detect OPC UA (UANodeSet)
            tag_lower = root.tag.lower() if isinstance(root.tag, str) else ""
            if "uanodeset" in tag_lower or "opcfoundation" in tag_lower:
                self._process_opcua_file(root, file_path)
                return
            
            # Detect namespace from root element (AAS)
            # AAS 2.0: http://www.admin-shell.io/aas/2/0
            # AAS 3.0: https://admin-shell.io/aas/3/0
            namespace = None
            if root.tag.startswith("{http://www.admin-shell.io/aas/2/0}"):
                namespace = "http://www.admin-shell.io/aas/2/0"
            elif root.tag.startswith("{https://admin-shell.io/aas/3/0}"):
                namespace = "https://admin-shell.io/aas/3/0"
            else:
                # Try to extract namespace from root
                if "{" in root.tag and "}" in root.tag:
                    namespace = root.tag.split("{")[1].split("}")[0]
            
            if namespace is None:
                print(f"  Warning: Could not detect AAS namespace, trying both versions")
                # Try AAS 2.0 first
                namespace = "http://www.admin-shell.io/aas/2/0"
            
            # Process AAS 3.0 structure: assetAdministrationShell -> submodels -> submodel -> submodelElements -> property
            # Extract asset and submodel context so enrichment (OpenAI, eClass) can use it for accurate descriptions
            if namespace == "https://admin-shell.io/aas/3/0":
                shells = root.findall(f".//{{{namespace}}}assetAdministrationShell")
                if not shells:
                    shells = [root]  # fallback: treat root as single shell
                for shell_elem in shells:
                    asset_id_short = ""
                    id_short_elem = shell_elem.find(f".//{{{namespace}}}idShort")
                    if id_short_elem is not None:
                        asset_id_short = self.extract_xml_text_content(id_short_elem) or ""
                    submodels = shell_elem.findall(f".//{{{namespace}}}submodel")
                    for submodel in submodels:
                        submodel_id_short = ""
                        sm_id_short = submodel.find(f".//{{{namespace}}}idShort")
                        if sm_id_short is not None:
                            submodel_id_short = self.extract_xml_text_content(sm_id_short) or ""
                        submodel_elements_container = submodel.find(f".//{{{namespace}}}submodelElements")
                        if submodel_elements_container is not None:
                            properties = submodel_elements_container.findall(f".//{{{namespace}}}property")
                            for prop in properties:
                                self.process_xml_property_aas3(prop, namespace, asset_id_short, submodel_id_short)
            else:
                # Process AAS 2.0 structure
                submodels = root.findall(f".//{{{namespace}}}submodel")
                for submodel in submodels:
                    submodel_elements = submodel.findall(f".//{{{namespace}}}submodelElement")
                    self.process_xml_submodel_elements(submodel_elements, namespace)
                
                # Process concept descriptions
                concept_descriptions = root.findall(f".//{{{namespace}}}conceptDescription")
                self.process_xml_concept_descriptions(concept_descriptions, namespace)
            
        except Exception as e:
            print(f"Error processing XML file {file_path}: {str(e)}")
    
    def extract_aml_text_content(self, element: ET.Element) -> str:
        """Extract text content from AML element."""
        if element is None:
            return ""
        
        # Get direct text content
        text = element.text or ""
        
        # Get text from all child elements
        for child in element:
            child_text = self.extract_aml_text_content(child)
            if child_text:
                text += " " + child_text
        
        return text.strip()
    
    def extract_aml_description(self, element: ET.Element) -> str:
        """Extract description from AML element."""
        description_elem = element.find(".//Description")
        if description_elem is not None:
            return self.extract_aml_text_content(description_elem)
        return ""
    
    def extract_aml_value(self, element: ET.Element) -> str:
        """Extract value from AML element."""
        # Look for Value element
        value_elem = element.find(".//Value")
        if value_elem is not None:
            return self.extract_aml_text_content(value_elem)
        
        # Look for DefaultValue element
        default_value_elem = element.find(".//DefaultValue")
        if default_value_elem is not None:
            return self.extract_aml_text_content(default_value_elem)
        
        return ""
    
    def extract_aml_data_type(self, element: ET.Element) -> str:
        """Extract data type from AML element."""
        data_type_elem = element.find(".//AttributeDataType")
        if data_type_elem is not None:
            return self.extract_aml_text_content(data_type_elem)
        return ""
    
    def process_aml_interface_classes(self, interface_classes: List[ET.Element], parent_path: str = "") -> None:
        """Recursively process AML interface classes to extract semantic nodes."""
        for interface_class in interface_classes:
            if interface_class is None:
                continue
            
            # Get interface class name
            name_elem = interface_class.find(".//Name")
            if name_elem is None:
                continue
            
            class_name = self.extract_aml_text_content(name_elem)
            if not class_name:
                continue
            
            # Create full path for nested elements
            current_path = f"{parent_path}.{class_name}" if parent_path else class_name
            
            # Extract semantic node information
            semantic_node = {
                "Name": class_name,
                "Conceptual definition": self.extract_aml_description(interface_class),
                "Usage of data": "",  # Always blank as per requirements
                "Value": self.extract_aml_value(interface_class),
                "Value type": self.extract_aml_data_type(interface_class),
                "Unit": "",  # AML doesn't typically have units in interface classes
                "Source description": ""  # Always blank as per requirements
            }
            
            self.semantic_nodes.append(semantic_node)
            
            # Process nested interface classes
            nested_classes = interface_class.findall(".//InterfaceClass")
            if nested_classes:
                self.process_aml_interface_classes(nested_classes, current_path)
            
            # Process attributes
            attributes = interface_class.findall(".//Attribute")
            for attribute in attributes:
                attr_name_elem = attribute.find(".//Name")
                if attr_name_elem is not None:
                    attr_name = self.extract_aml_text_content(attr_name_elem)
                    if attr_name:
                        f"{current_path}.{attr_name}"
                        
                        attr_semantic_node = {
                            "Name": attr_name,
                            "Conceptual definition": self.extract_aml_description(attribute),
                            "Usage of data": "",
                            "Value": self.extract_aml_value(attribute),
                            "Value type": self.extract_aml_data_type(attribute),
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
            
            # Process interface class libraries
            interface_class_libs = root.findall(".//InterfaceClassLib")
            for lib in interface_class_libs:
                interface_classes = lib.findall(".//InterfaceClass")
                self.process_aml_interface_classes(interface_classes)
            
        except Exception as e:
            print(f"Error processing AML file {file_path}: {str(e)}")
    
    def process_json_file(self, file_path: str) -> None:
        """Process a single JSON file and extract semantic nodes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"Processing file: {os.path.basename(file_path)}")
            
            # AAS hierarchy-aware: full recursion so all nodes (e.g. 185 for QualityControlForMachining) are extracted
            if self.aas_hierarchy_aware and _is_aas_json(data):
                self._process_aas_json_full_hierarchy(data, file_path)
                return

            # Project/GraphLinksModel JSON: extract nodes and parameters for mapping to target
            if _is_project_json(data):
                self._process_project_json_one_file(data, file_path)
                return
            
            # Process submodels (flat recursion)
            submodels = data.get("submodels", [])
            for submodel in submodels:
                if isinstance(submodel, dict):
                    submodel_elements = submodel.get("submodelElements", [])
                    self.process_submodel_elements(submodel_elements)
            
            # Process concept descriptions
            concept_descriptions = data.get("conceptDescriptions", [])
            self.process_concept_descriptions(concept_descriptions)
            
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    
    def process_simvsm_file(self, file_path: str) -> None:
        """Process a .simvsm file (treat as ZIP) and extract project.json."""
        try:
            print(f"Processing SIMVSM file (ZIP): {os.path.basename(file_path)}")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Look for project.json in the zip archive
                project_json_path = None
                for member in zip_ref.namelist():
                    if member.endswith('project.json'):
                        project_json_path = member
                        break
                
                if project_json_path:
                    with zip_ref.open(project_json_path) as f:
                        data = json.load(f)
                        if _is_project_json(data):
                            self._process_project_json_one_file(data, file_path)
                        else:
                            print(f"  Warning: {project_json_path} in {file_path} is not a valid project JSON")
                else:
                    print(f"  Warning: No project.json found in {file_path}")
        except zipfile.BadZipFile:
            print(f"  Error: {file_path} is not a valid SIMVSM/ZIP file. Trying to parse as XML fallback.")
            self.process_xml_file(file_path)
        except Exception as e:
            print(f"Error processing SIMVSM file {file_path}: {str(e)}")

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
        
        # Process XML files
        for xml_file in xml_files:
            file_path = os.path.join(self.data_folder, xml_file)
            self.process_xml_file(file_path)
        
        # Process AML files
        for aml_file in aml_files:
            file_path = os.path.join(self.data_folder, aml_file)
            self.process_aml_file(file_path)
        
        # Process EXM files (treat as XML for now)
        for exm_file in exm_files:
            file_path = os.path.join(self.data_folder, exm_file)
            self.process_xml_file(file_path)
        
        # Process SIMVSM files (extract project.json from zip)
        for simvsm_file in simvsm_files:
            file_path = os.path.join(self.data_folder, simvsm_file)
            self.process_simvsm_file(file_path)
        
        print(f"\nExtracted {len(self.semantic_nodes)} semantic nodes total.")
    
    def save_to_csv(self, output_file: str = "semantic_nodes.csv") -> None:
        """Save extracted semantic nodes to CSV file."""
        if not self.semantic_nodes:
            print("No semantic nodes to save!")
            return
        
        fieldnames = [
            "idShort",
            "Name",
            "Normalized Name",
            "Conceptual definition",
            "Usage of data",
            "Value",
            "Value type",
            "Unit",
            "Source description",
            "Source file",
        ]
        # Write only these columns; _metadata and other extras are omitted
        def row_for_csv(node: Dict) -> Dict:
            out = {k: node.get(k, "") for k in fieldnames}
            out["idShort"] = node.get("idShort") or node.get("Name", "")
            out["Normalized Name"] = node.get("Normalized Name") or node.get("normalized_name") or node.get("Name", "")
            return out

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows([row_for_csv(n) for n in self.semantic_nodes])
            
            print(f"Semantic nodes saved to '{output_file}'")
            print(f"Total rows: {len(self.semantic_nodes)}")
            
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")

    def save_instance_values(self, output_file: str = "simvsm_instance_values.json") -> None:
        """Save instance-specific parameter values to JSON."""
        if not self.instance_values:
            print("No instance values to save!")
            return
            
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.instance_values, f, indent=2, ensure_ascii=False)
            print(f"Instance parameter values saved to '{output_file}'")
            print(f"Total instances extracted: {len(self.instance_values)}")
        except Exception as e:
            print(f"Error saving instance values to JSON: {str(e)}")

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
    """Main function to run the semantic node extractor."""
    print("=== Semantic Node DataMapper ===")
    print("Extracting semantic nodes from AAS JSON, XML, AML, EXM, and SIMVSM files...\n")
    
    # Check for custom data folder from command line arguments
    data_folder = "data"
    if len(sys.argv) > 1:
        data_folder = sys.argv[1]
        print(f"Using custom data folder: {data_folder}")
    
    # Initialize extractor
    extractor = SemanticNodeExtractor(data_folder=data_folder)
    
    # Process all supported files
    extractor.process_all_files()
    
    # Print summary
    extractor.print_summary()
    
    # Save to CSV
    extractor.save_to_csv()
    
    # Save instance values to JSON
    extractor.save_instance_values()
    
    print("\n=== Processing Complete ===")


if __name__ == "__main__":
    main()
