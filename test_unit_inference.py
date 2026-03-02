#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to verify unit inference is working.
Run this to test if Llama can infer units for your nodes.
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from enrichment_module import LlamaEnricher
from semantic_node_enhanced import SemanticNode

# Initialize Llama enricher
print("Initializing Llama enricher...")
enricher = LlamaEnricher(use_llama=True)

if not enricher.use_llama:
    print("ERROR: Llama is not available. Make sure Ollama is running.")
    print("Start Ollama: ollama serve")
    exit(1)

# Test nodes from your XML
test_nodes = [
    SemanticNode(
        name="Stroke",
        conceptual_definition="The maximum distance of linear travel specified for the simulation",
        value_type="xs:float"
    ),
    SemanticNode(
        name="max_V",
        conceptual_definition="Limit of the translational speed for the component under peak dynamic",
        value_type="xs:float",
        metadata={"source_asset": "Actuator", "source_submodel": "Mechanical/Linear"}
    ),
    SemanticNode(
        name="Max_feed_force_Fx",
        conceptual_definition="The upper bound of linear force exerted by the actuator along its principal axis",
        value_type="xs:float"
    ),
    SemanticNode(
        name="Repetition_accuracy",
        conceptual_definition="Measurement of positional deviation when returning to a previously",
        value_type="xs:float"
    ),
    SemanticNode(
        name="Max_driving_torque",
        conceptual_definition="Highest rotational energy potential generated at the drive interface",
        value_type="xs:float"
    ),
    SemanticNode(
        name="No-load_driving_torque",
        conceptual_definition="The residual friction torque present within the system when rotating",
        value_type="xs:float"
    ),
    SemanticNode(
        name="max_RPM",
        conceptual_definition="The maximum frequency of rotations per minute allowed for the shaft",
        value_type="xs:float"
    ),
]

print("\n" + "="*60)
print("Testing Unit Inference")
print("="*60 + "\n")

for node in test_nodes:
    print(f"Testing: {node.name}")
    print(f"  Description: {node.conceptual_definition[:60]}...")
    
    try:
        unit = enricher.generate_unit(node)
        if unit:
            print(f"  [OK] Unit inferred: {unit}\n")
        else:
            print(f"  [FAIL] No unit inferred (Llama returned None)\n")
    except Exception as e:
        print(f"  [ERROR] Error: {e}\n")

print("="*60)
print("Test complete!")
print("="*60)
