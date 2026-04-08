#!/usr/bin/env python3
"""
DataFrame Converter for Semantic Nodes

This script converts the semantic_nodes.csv file to a pandas DataFrame
for easier data manipulation and analysis.
"""

import pandas as pd
import os
import sys
from typing import Optional, Dict, Any


class SemanticNodeDataFrame:
    """Converts semantic nodes CSV to pandas DataFrame with analysis capabilities."""
    
    def __init__(self, csv_file: str = "semantic_nodes.csv"):
        self.csv_file = csv_file
        self.df = None
        self.load_data()
    
    def load_data(self) -> None:
        """Load semantic nodes data from CSV file."""
        if not os.path.exists(self.csv_file):
            print(f"Error: CSV file '{self.csv_file}' not found!")
            print("Please run datamap.py first to generate the semantic nodes CSV.")
            sys.exit(1)
        
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"Successfully loaded {len(self.df)} semantic nodes from '{self.csv_file}'")
        except Exception as e:
            print(f"Error loading CSV file: {str(e)}")
            sys.exit(1)
    
    def get_dataframe(self) -> pd.DataFrame:
        """Return the pandas DataFrame."""
        return self.df
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the semantic nodes."""
        if self.df is None:
            return {}
        
        summary = {
            "total_nodes": len(self.df),
            "nodes_with_values": len(self.df[self.df["Value"].notna() & (self.df["Value"] != "")]),
            "nodes_with_value_types": len(self.df[self.df["Value type"].notna() & (self.df["Value type"] != "")]),
            "nodes_with_units": len(self.df[self.df["Unit"].notna() & (self.df["Unit"] != "")]),
            "nodes_with_descriptions": len(self.df[self.df["Conceptual definition"].notna() & (self.df["Conceptual definition"] != "")]),
            "unique_value_types": self.df["Value type"].dropna().nunique() if "Value type" in self.df.columns else 0,
            "unique_units": self.df["Unit"].dropna().nunique() if "Unit" in self.df.columns else 0
        }
        
        return summary
    
    def print_summary(self) -> None:
        """Print a detailed summary of the semantic nodes."""
        if self.df is None:
            print("No data loaded!")
            return
        
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("SEMANTIC NODES DATAFRAME SUMMARY")
        print("="*50)
        print(f"Total semantic nodes: {summary['total_nodes']}")
        print(f"Nodes with values: {summary['nodes_with_values']}")
        print(f"Nodes with value types: {summary['nodes_with_value_types']}")
        print(f"Nodes with units: {summary['nodes_with_units']}")
        print(f"Nodes with descriptions: {summary['nodes_with_descriptions']}")
        print(f"Unique value types: {summary['unique_value_types']}")
        print(f"Unique units: {summary['unique_units']}")
        
        # Show value type distribution
        if summary['unique_value_types'] > 0:
            print(f"\nValue Type Distribution:")
            value_type_counts = self.df["Value type"].value_counts()
            for value_type, count in value_type_counts.head(10).items():
                print(f"  {value_type}: {count}")
        
        # Show sample data
        print(f"\nSample Data (first 5 rows):")
        print("-" * 50)
        sample_cols = ["Name", "Conceptual definition", "Value", "Value type", "Unit"]
        available_cols = [col for col in sample_cols if col in self.df.columns]
        print(self.df[available_cols].head().to_string(index=False))
    
    def filter_by_value_type(self, value_type: str) -> pd.DataFrame:
        """Filter nodes by value type."""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df["Value type"] == value_type]
    
    def filter_by_has_value(self) -> pd.DataFrame:
        """Filter nodes that have actual values."""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df["Value"].notna() & (self.df["Value"] != "")]
    
    def filter_by_has_description(self) -> pd.DataFrame:
        """Filter nodes that have conceptual definitions."""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df["Conceptual definition"].notna() & (self.df["Conceptual definition"] != "")]
    
    def get_value_type_analysis(self) -> pd.DataFrame:
        """Get analysis of value types."""
        if self.df is None:
            return pd.DataFrame()
        
        value_type_analysis = self.df.groupby("Value type").agg({
            "Name": "count",
            "Value": lambda x: (x.notna() & (x != "")).sum()
        }).rename(columns={"Name": "Total_Nodes", "Value": "Nodes_With_Values"})
        
        return value_type_analysis
    
    def search_by_name(self, search_term: str) -> pd.DataFrame:
        """Search nodes by name (case-insensitive)."""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df["Name"].str.contains(search_term, case=False, na=False)]
    
    def search_by_description(self, search_term: str) -> pd.DataFrame:
        """Search nodes by conceptual definition (case-insensitive)."""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df["Conceptual definition"].str.contains(search_term, case=False, na=False)]
    
    def export_to_excel(self, output_file: str = "semantic_nodes.xlsx") -> None:
        """Export DataFrame to Excel file."""
        if self.df is None:
            print("No data to export!")
            return
        
        try:
            self.df.to_excel(output_file, index=False)
            print(f"DataFrame exported to '{output_file}'")
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
    
    def export_to_json(self, output_file: str = "semantic_nodes.json") -> None:
        """Export DataFrame to JSON file."""
        if self.df is None:
            print("No data to export!")
            return
        
        try:
            self.df.to_json(output_file, orient="records", indent=2)
            print(f"DataFrame exported to '{output_file}'")
        except Exception as e:
            print(f"Error exporting to JSON: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the semantic nodes."""
        if self.df is None:
            return {}
        
        stats = {
            "dataframe_info": {
                "shape": self.df.shape,
                "columns": list(self.df.columns),
                "dtypes": self.df.dtypes.to_dict()
            },
            "missing_values": self.df.isnull().sum().to_dict(),
            "value_type_distribution": self.df["Value type"].value_counts().to_dict() if "Value type" in self.df.columns else {},
            "unit_distribution": self.df["Unit"].value_counts().to_dict() if "Unit" in self.df.columns else {},
            "nodes_with_data": {
                "has_value": (self.df["Value"].notna() & (self.df["Value"] != "")).sum(),
                "has_description": (self.df["Conceptual definition"].notna() & (self.df["Conceptual definition"] != "")).sum(),
                "has_value_type": (self.df["Value type"].notna() & (self.df["Value type"] != "")).sum(),
                "has_unit": (self.df["Unit"].notna() & (self.df["Unit"] != "")).sum()
            }
        }
        
        return stats
    
    def print_dataframe(self, rows: int = 10, columns: Optional[list] = None) -> None:
        """Print the DataFrame with specified number of rows and columns."""
        if self.df is None:
            print("No data loaded!")
            return
        
        print(f"\n" + "="*80)
        print(f"SEMANTIC NODES DATAFRAME (showing first {rows} rows)")
        print("="*80)
        
        # Select columns to display
        if columns is None:
            display_df = self.df.head(rows)
        else:
            available_cols = [col for col in columns if col in self.df.columns]
            if not available_cols:
                print(f"Warning: None of the specified columns {columns} found in DataFrame")
                display_df = self.df.head(rows)
            else:
                display_df = self.df[available_cols].head(rows)
        
        # Print DataFrame with proper formatting
        print(display_df.to_string(index=True, max_cols=None, max_colwidth=50))
        
        print(f"\nDataFrame Info:")
        print(f"  Total rows: {len(self.df)}")
        print(f"  Total columns: {len(self.df.columns)}")
        print(f"  Columns: {', '.join(self.df.columns)}")
    
    def print_full_dataframe(self) -> None:
        """Print the complete DataFrame."""
        if self.df is None:
            print("No data loaded!")
            return
        
        print(f"\n" + "="*100)
        print("COMPLETE SEMANTIC NODES DATAFRAME")
        print("="*100)
        
        # Print with all rows and columns
        print(self.df.to_string(index=True, max_cols=None, max_colwidth=60))
        
        print(f"\nDataFrame Shape: {self.df.shape}")
    
    def print_dataframe_by_type(self, value_type: str, rows: int = 10) -> None:
        """Print DataFrame filtered by value type."""
        if self.df is None:
            print("No data loaded!")
            return
        
        filtered_df = self.df[self.df["Value type"] == value_type]
        
        print(f"\n" + "="*80)
        print(f"DATAFRAME FILTERED BY VALUE TYPE: {value_type}")
        print(f"Found {len(filtered_df)} nodes with value type '{value_type}'")
        print("="*80)
        
        if len(filtered_df) > 0:
            print(filtered_df.head(rows).to_string(index=True, max_cols=None, max_colwidth=50))
        else:
            print("No nodes found with this value type.")
    
    def print_dataframe_with_values(self, rows: int = 15) -> None:
        """Print DataFrame showing only nodes that have actual values."""
        if self.df is None:
            print("No data loaded!")
            return
        
        nodes_with_values = self.df[self.df["Value"].notna() & (self.df["Value"] != "")]
        
        print(f"\n" + "="*80)
        print(f"DATAFRAME - NODES WITH ACTUAL VALUES")
        print(f"Found {len(nodes_with_values)} nodes with values (showing first {rows})")
        print("="*80)
        
        if len(nodes_with_values) > 0:
            # Show most relevant columns for nodes with values
            relevant_cols = ["Name", "Conceptual definition", "Value", "Value type", "Unit"]
            available_cols = [col for col in relevant_cols if col in nodes_with_values.columns]
            print(nodes_with_values[available_cols].head(rows).to_string(index=True, max_cols=None, max_colwidth=50))
        else:
            print("No nodes found with actual values.")
    
    def print_detailed_analysis(self) -> None:
        """Print detailed analysis of the semantic nodes."""
        if self.df is None:
            print("No data loaded!")
            return
        
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("DETAILED SEMANTIC NODES ANALYSIS")
        print("="*60)
        
        print(f"\nDataFrame Shape: {stats['dataframe_info']['shape']}")
        print(f"Columns: {', '.join(stats['dataframe_info']['columns'])}")
        
        print(f"\nMissing Values:")
        for col, missing_count in stats['missing_values'].items():
            if missing_count > 0:
                print(f"  {col}: {missing_count}")
        
        print(f"\nData Availability:")
        for key, count in stats['nodes_with_data'].items():
            print(f"  {key.replace('_', ' ').title()}: {count}")
        
        if stats['value_type_distribution']:
            print(f"\nValue Type Distribution:")
            for value_type, count in sorted(stats['value_type_distribution'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {value_type}: {count}")
        
        if stats['unit_distribution']:
            print(f"\nUnit Distribution:")
            for unit, count in sorted(stats['unit_distribution'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {unit}: {count}")


def main():
    """Main function to demonstrate DataFrame usage."""
    print("=== Semantic Nodes DataFrame Converter ===")
    print("Converting semantic_nodes.csv to pandas DataFrame...\n")
    
    # Initialize DataFrame converter
    converter = SemanticNodeDataFrame()
    
    # Print the DataFrame
    print("1. DATAFRAME OVERVIEW")
    converter.print_dataframe(rows=10)
    
    # Print nodes with actual values
    print("\n2. NODES WITH ACTUAL VALUES")
    converter.print_dataframe_with_values(rows=15)
    
    # Print summary
    print("\n3. SUMMARY STATISTICS")
    converter.print_summary()
    
    # Print detailed analysis
    print("\n4. DETAILED ANALYSIS")
    converter.print_detailed_analysis()
    
    # Demonstrate filtering by value type
    print(f"\n5. FILTERING BY VALUE TYPE")
    print("-" * 40)
    converter.print_dataframe_by_type("xs:string", rows=10)
    
    # Demonstrate some filtering operations
    print(f"\n6. FILTERING EXAMPLES")
    print("-" * 40)
    
    # Filter nodes with values
    nodes_with_values = converter.filter_by_has_value()
    print(f"\nNodes with actual values: {len(nodes_with_values)}")
    
    # Filter by value type
    string_nodes = converter.filter_by_value_type("xs:string")
    print(f"Nodes with 'xs:string' value type: {len(string_nodes)}")
    
    # Search examples
    print(f"\nSearch examples:")
    search_results = converter.search_by_name("Process")
    print(f"Nodes containing 'Process' in name: {len(search_results)}")
    
    # Show complete DataFrame option
    print(f"\n7. COMPLETE DATAFRAME OPTION")
    print("-" * 40)
    print("To see the complete DataFrame, use:")
    print("  converter.print_full_dataframe()")
    print("  converter.print_dataframe(rows=50)  # Show first 50 rows")
    print("  converter.print_dataframe(columns=['Name', 'Value'])  # Show specific columns")
    
    # Export options
    print(f"\n8. EXPORT OPTIONS")
    print("-" * 40)
    print("Available export methods:")
    print("  - converter.export_to_excel('semantic_nodes.xlsx')")
    print("  - converter.export_to_json('semantic_nodes.json')")
    print("  - converter.get_dataframe()  # Returns pandas DataFrame")
    
    print(f"\n=== DataFrame Conversion Complete ===")
    print(f"DataFrame is ready for analysis and manipulation!")


if __name__ == "__main__":
    main()
