#!/usr/bin/env python3
"""
Example Analysis Script for Semantic Nodes DataFrame

This script demonstrates various ways to analyze and work with the semantic nodes DataFrame.
"""

from dataframe import SemanticNodeDataFrame


def main():
    """Demonstrate various DataFrame analysis techniques."""
    print("=== Semantic Nodes DataFrame Analysis Examples ===\n")
    
    # Load the DataFrame
    converter = SemanticNodeDataFrame()
    df = converter.get_dataframe()
    
    print("1. BASIC DATAFRAME INFO")
    print("-" * 30)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Data types:\n{df.dtypes}")
    
    print("\n2. NODES WITH ACTUAL VALUES")
    print("-" * 30)
    nodes_with_values = df[df["Value"].notna() & (df["Value"] != "")]
    print(f"Found {len(nodes_with_values)} nodes with actual values:")
    print(nodes_with_values[["Name", "Value", "Value type"]].head(10).to_string(index=False))
    
    print("\n3. VALUE TYPE ANALYSIS")
    print("-" * 30)
    value_type_counts = df["Value type"].value_counts()
    print("Value type distribution:")
    for value_type, count in value_type_counts.items():
        print(f"  {value_type}: {count}")
    
    print("\n4. SEARCH EXAMPLES")
    print("-" * 30)
    
    # Search for nodes containing "Process"
    process_nodes = df[df["Name"].str.contains("Process", case=False, na=False)]
    print(f"Nodes containing 'Process': {len(process_nodes)}")
    print(process_nodes[["Name", "Conceptual definition"]].head(5).to_string(index=False))
    
    # Search for nodes containing "Manufacturer"
    manufacturer_nodes = df[df["Name"].str.contains("Manufacturer", case=False, na=False)]
    print(f"\nNodes containing 'Manufacturer': {len(manufacturer_nodes)}")
    print(manufacturer_nodes[["Name", "Value", "Value type"]].to_string(index=False))
    
    print("\n5. FILTERING EXAMPLES")
    print("-" * 30)
    
    # Filter by value type
    string_nodes = df[df["Value type"] == "xs:string"]
    print(f"Nodes with 'xs:string' type: {len(string_nodes)}")
    
    # Filter nodes with descriptions
    described_nodes = df[df["Conceptual definition"].notna() & (df["Conceptual definition"] != "")]
    print(f"Nodes with descriptions: {len(described_nodes)}")
    
    print("\n6. STATISTICAL ANALYSIS")
    print("-" * 30)
    
    # Calculate completeness
    total_nodes = len(df)
    completeness = {
        "Has Value": (df["Value"].notna() & (df["Value"] != "")).sum() / total_nodes * 100,
        "Has Description": (df["Conceptual definition"].notna() & (df["Conceptual definition"] != "")).sum() / total_nodes * 100,
        "Has Value Type": (df["Value type"].notna() & (df["Value type"] != "")).sum() / total_nodes * 100,
        "Has Unit": (df["Unit"].notna() & (df["Unit"] != "")).sum() / total_nodes * 100
    }
    
    print("Data completeness percentages:")
    for field, percentage in completeness.items():
        print(f"  {field}: {percentage:.1f}%")
    
    print("\n7. EXPORT EXAMPLES")
    print("-" * 30)
    
    # Export to Excel
    try:
        converter.export_to_excel("semantic_nodes_analysis.xlsx")
        print("✓ Exported to Excel: semantic_nodes_analysis.xlsx")
    except Exception as e:
        print(f"✗ Excel export failed: {e}")
    
    # Export to JSON
    try:
        converter.export_to_json("semantic_nodes_analysis.json")
        print("✓ Exported to JSON: semantic_nodes_analysis.json")
    except Exception as e:
        print(f"✗ JSON export failed: {e}")
    
    print("\n8. CUSTOM ANALYSIS")
    print("-" * 30)
    
    # Find nodes with both value and description
    complete_nodes = df[
        (df["Value"].notna() & (df["Value"] != "")) & 
        (df["Conceptual definition"].notna() & (df["Conceptual definition"] != ""))
    ]
    print(f"Nodes with both value and description: {len(complete_nodes)}")
    
    # Find nodes with specific patterns
    url_nodes = df[df["Value"].str.contains("http", case=False, na=False)]
    print(f"Nodes with URL values: {len(url_nodes)}")
    
    print("\n=== Analysis Complete ===")
    print("The DataFrame is ready for further analysis and manipulation!")


if __name__ == "__main__":
    main()
