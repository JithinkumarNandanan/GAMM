#!/usr/bin/env python3
"""
Interactive DataFrame Viewer for Semantic Nodes

This script provides an interactive way to view and explore the semantic nodes DataFrame.
"""

from dataframe import SemanticNodeDataFrame


def show_menu():
    """Display the main menu options."""
    print("\n" + "="*60)
    print("SEMANTIC NODES DATAFRAME VIEWER")
    print("="*60)
    print("1. Show DataFrame overview (first 10 rows)")
    print("2. Show nodes with actual values")
    print("3. Show complete DataFrame")
    print("4. Show DataFrame filtered by value type")
    print("5. Show specific columns only")
    print("6. Show summary statistics")
    print("7. Search nodes by name")
    print("8. Search nodes by description")
    print("9. Show detailed analysis")
    print("10. Export options")
    print("0. Exit")
    print("="*60)


def main():
    """Interactive DataFrame viewer."""
    print("Loading semantic nodes DataFrame...")
    
    try:
        converter = SemanticNodeDataFrame()
        print("✓ DataFrame loaded successfully!")
    except Exception as e:
        print(f"✗ Error loading DataFrame: {e}")
        return
    
    while True:
        show_menu()
        
        try:
            choice = input("\nEnter your choice (0-10): ").strip()
            
            if choice == "0":
                print("Goodbye!")
                break
            elif choice == "1":
                print("\n" + "="*60)
                print("DATAFRAME OVERVIEW")
                print("="*60)
                converter.print_dataframe(rows=10)
                
            elif choice == "2":
                print("\n" + "="*60)
                print("NODES WITH ACTUAL VALUES")
                print("="*60)
                converter.print_dataframe_with_values(rows=20)
                
            elif choice == "3":
                print("\n" + "="*60)
                print("COMPLETE DATAFRAME")
                print("="*60)
                converter.print_full_dataframe()
                
            elif choice == "4":
                print("\nAvailable value types:")
                df = converter.get_dataframe()
                value_types = df["Value type"].dropna().unique()
                for i, vt in enumerate(value_types, 1):
                    print(f"  {i}. {vt}")
                
                try:
                    vt_choice = input("\nEnter value type number or type the value type: ").strip()
                    
                    # Try to parse as number first
                    try:
                        vt_index = int(vt_choice) - 1
                        if 0 <= vt_index < len(value_types):
                            selected_type = value_types[vt_index]
                        else:
                            print("Invalid number!")
                            continue
                    except ValueError:
                        # Treat as direct input
                        selected_type = vt_choice
                    
                    converter.print_dataframe_by_type(selected_type, rows=15)
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif choice == "5":
                print("\nAvailable columns:")
                df = converter.get_dataframe()
                for i, col in enumerate(df.columns, 1):
                    print(f"  {i}. {col}")
                
                try:
                    col_input = input("\nEnter column numbers (comma-separated) or column names: ").strip()
                    
                    if col_input:
                        # Try to parse as numbers first
                        try:
                            col_indices = [int(x.strip()) - 1 for x in col_input.split(",")]
                            selected_cols = [df.columns[i] for i in col_indices if 0 <= i < len(df.columns)]
                        except ValueError:
                            # Treat as column names
                            selected_cols = [x.strip() for x in col_input.split(",")]
                        
                        converter.print_dataframe(rows=15, columns=selected_cols)
                    else:
                        print("No columns selected!")
                        
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif choice == "6":
                converter.print_summary()
                
            elif choice == "7":
                search_term = input("\nEnter search term for node names: ").strip()
                if search_term:
                    results = converter.search_by_name(search_term)
                    print(f"\nFound {len(results)} nodes containing '{search_term}':")
                    if len(results) > 0:
                        print(results[["Name", "Conceptual definition", "Value", "Value type"]].to_string(index=True))
                    else:
                        print("No nodes found!")
                else:
                    print("No search term provided!")
                    
            elif choice == "8":
                search_term = input("\nEnter search term for descriptions: ").strip()
                if search_term:
                    results = converter.search_by_description(search_term)
                    print(f"\nFound {len(results)} nodes with descriptions containing '{search_term}':")
                    if len(results) > 0:
                        print(results[["Name", "Conceptual definition", "Value", "Value type"]].to_string(index=True))
                    else:
                        print("No nodes found!")
                else:
                    print("No search term provided!")
                    
            elif choice == "9":
                converter.print_detailed_analysis()
                
            elif choice == "10":
                print("\n" + "="*60)
                print("EXPORT OPTIONS")
                print("="*60)
                print("1. Export to Excel")
                print("2. Export to JSON")
                print("3. Show DataFrame info")
                
                export_choice = input("\nEnter export choice (1-3): ").strip()
                
                if export_choice == "1":
                    filename = input("Enter Excel filename (default: semantic_nodes.xlsx): ").strip()
                    if not filename:
                        filename = "semantic_nodes.xlsx"
                    converter.export_to_excel(filename)
                    
                elif export_choice == "2":
                    filename = input("Enter JSON filename (default: semantic_nodes.json): ").strip()
                    if not filename:
                        filename = "semantic_nodes.json"
                    converter.export_to_json(filename)
                    
                elif export_choice == "3":
                    df = converter.get_dataframe()
                    print(f"\nDataFrame Info:")
                    print(f"  Shape: {df.shape}")
                    print(f"  Columns: {list(df.columns)}")
                    print(f"  Data types:\n{df.dtypes}")
                    
            else:
                print("Invalid choice! Please enter a number between 0-10.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
