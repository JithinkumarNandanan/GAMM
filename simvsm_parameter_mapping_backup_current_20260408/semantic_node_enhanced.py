#!/usr/bin/env python3
"""
Enhanced Semantic Node Structure

This module defines the complete semantic node structure according to thesis requirements:
- Name: Concise and specific title
- Conceptual definition: What the semantic node represents
- Usage of data (Affordance): Potential usage and application
- Value: The actual data
- Value type: Data type (String by default)
- Unit: Measurement unit (if applicable)
- Source description: Extended explanation situating the node in context
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import json


@dataclass
class SemanticNode:
    """
    Enhanced Semantic Node structure with all required fields.
    
    Attributes:
        name: A concise and specific title for the semantic node
        conceptual_definition: A definition of what the semantic node represents
        usage_of_data: Describes the potential usage and application (Affordance)
        value: The actual data described by the semantic node
        value_type: The type of data (default: String)
        unit: The measurement unit associated with the value (if applicable)
        source_description: Extended explanation situating the node in its source context
        source_file: Original file where this node was extracted from
        enriched: Whether description was enriched from eCl@ss or IEC CDD
        enrichment_source: Source of enrichment (eclass, ieccdd, or None)
    """
    name: str
    conceptual_definition: str = ""
    usage_of_data: str = ""  # Affordance
    value: Any = ""
    value_type: str = "String"
    unit: str = ""
    source_description: str = ""
    source_file: str = ""
    enriched: bool = False
    enrichment_source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert semantic node to dictionary."""
        meta = self.metadata or {}
        id_short = (
            meta.get("id_short")
            or meta.get("idShort")
            or getattr(self, "id_short", "")
            or self.name
        )
        normalized_name = meta.get("normalized_name") or self.name
        return {
            "idShort": id_short,
            "Name": self.name,
            "Normalized Name": normalized_name,
            "Conceptual definition": self.conceptual_definition,
            "Usage of data (Affordance)": self.usage_of_data,
            "Value": str(self.value) if self.value else "",
            "Value type": self.value_type,
            "Unit": self.unit,
            "Source description": self.source_description,
            "Source file": self.source_file,
            "Enriched": self.enriched,
            "Enrichment source": self.enrichment_source or ""
        }
    
    def is_complete(self) -> bool:
        """Check if semantic node has all required information."""
        return bool(
            self.name and 
            self.conceptual_definition and
            self.value_type
        )
    
    def needs_enrichment(self) -> bool:
        """Check if semantic node needs enrichment from external sources."""
        return not bool(self.conceptual_definition) or not bool(self.usage_of_data)
    
    def get_enrichment_key(self) -> str:
        """Get key for searching in eCl@ss or IEC CDD."""
        # Combine name, unit, and value_type for better matching
        parts = [self.name]
        if self.unit:
            parts.append(self.unit)
        if self.value_type and self.value_type != "String":
            parts.append(self.value_type)
        return "_".join(parts).lower().replace(" ", "_")
    
    def __repr__(self) -> str:
        """String representation of semantic node."""
        return f"SemanticNode(name='{self.name}', value='{self.value}', type='{self.value_type}')"


class SemanticNodeCollection:
    """Collection of semantic nodes with utility methods."""
    
    def __init__(self):
        self.nodes: List[SemanticNode] = []
    
    def add_node(self, node: SemanticNode) -> None:
        """Add a semantic node to the collection."""
        self.nodes.append(node)
    
    def get_by_name(self, name: str) -> Optional[SemanticNode]:
        """Get semantic node by name."""
        for node in self.nodes:
            if node.name == name:
                return node
        return None
    
    def get_incomplete_nodes(self) -> List[SemanticNode]:
        """Get all nodes that are not complete."""
        return [node for node in self.nodes if not node.is_complete()]
    
    def get_nodes_needing_enrichment(self) -> List[SemanticNode]:
        """Get all nodes that need enrichment."""
        return [node for node in self.nodes if node.needs_enrichment()]
    
    def get_by_value_type(self, value_type: str) -> List[SemanticNode]:
        """Get all nodes with specific value type."""
        return [node for node in self.nodes if node.value_type == value_type]
    
    def get_by_unit(self, unit: str) -> List[SemanticNode]:
        """Get all nodes with specific unit."""
        return [node for node in self.nodes if node.unit == unit]
    
    def to_list_of_dicts(self) -> List[Dict[str, Any]]:
        """Convert all nodes to list of dictionaries."""
        return [node.to_dict() for node in self.nodes]
    
    def to_json(self, filepath: str) -> None:
        """Save collection to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_list_of_dicts(), f, indent=2, ensure_ascii=False)
    
    def statistics(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        total = len(self.nodes)
        return {
            "total_nodes": total,
            "complete_nodes": len([n for n in self.nodes if n.is_complete()]),
            "incomplete_nodes": len([n for n in self.nodes if not n.is_complete()]),
            "needs_enrichment": len(self.get_nodes_needing_enrichment()),
            "enriched_nodes": len([n for n in self.nodes if n.enriched]),
            "with_values": len([n for n in self.nodes if n.value]),
            "with_units": len([n for n in self.nodes if n.unit]),
            "unique_value_types": len(set(n.value_type for n in self.nodes)),
            "unique_units": len(set(n.unit for n in self.nodes if n.unit))
        }
    
    def __len__(self) -> int:
        """Get number of nodes in collection."""
        return len(self.nodes)
    
    def __iter__(self):
        """Iterate over nodes."""
        return iter(self.nodes)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"SemanticNodeCollection({len(self.nodes)} nodes)"


def create_semantic_node_from_extraction(
    name: str,
    description: str = "",
    value: Any = "",
    value_type: str = "String",
    unit: str = "",
    source_file: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> SemanticNode:
    """
    Factory function to create semantic node from extracted data.
    
    Args:
        name: Node name (idShort from AAS)
        description: Conceptual definition
        value: The actual data value
        value_type: Data type
        unit: Measurement unit
        source_file: Source file name
        metadata: Optional dict (e.g. source_asset, source_submodel, eclass_id for enrichment context)
        **kwargs: Additional fields merged into metadata if metadata is None
    
    Returns:
        SemanticNode instance
    """
    meta = dict(metadata) if metadata is not None else dict(kwargs)
    return SemanticNode(
        name=name,
        conceptual_definition=description,
        value=value,
        value_type=value_type,
        unit=unit,
        source_file=source_file,
        metadata=meta
    )


# Example usage
if __name__ == "__main__":
    print("=== Enhanced Semantic Node Structure ===\n")
    
    # Create a semantic node
    node = SemanticNode(
        name="ProcessTemperature",
        conceptual_definition="The temperature at which the process operates",
        usage_of_data="Used for monitoring and controlling process conditions",
        value=180.0,
        value_type="Float",
        unit="°C",
        source_description="Extracted from AAS submodel for process parameters",
        source_file="process_data.json"
    )
    
    print("Created Semantic Node:")
    print(f"  Name: {node.name}")
    print(f"  Definition: {node.conceptual_definition}")
    print(f"  Usage: {node.usage_of_data}")
    print(f"  Value: {node.value} {node.unit}")
    print(f"  Type: {node.value_type}")
    print(f"  Complete: {node.is_complete()}")
    print(f"  Needs Enrichment: {node.needs_enrichment()}")
    
    print("\nNode as Dictionary:")
    print(json.dumps(node.to_dict(), indent=2))
    
    # Create a collection
    collection = SemanticNodeCollection()
    collection.add_node(node)
    
    # Add node needing enrichment
    incomplete_node = SemanticNode(
        name="Pressure",
        value=5.2,
        value_type="Float",
        unit="bar"
    )
    collection.add_node(incomplete_node)
    
    print(f"\n=== Collection Statistics ===")
    stats = collection.statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nNodes needing enrichment: {len(collection.get_nodes_needing_enrichment())}")
    for node in collection.get_nodes_needing_enrichment():
        print(f"  - {node.name} (key: {node.get_enrichment_key()})")
