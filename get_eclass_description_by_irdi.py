#!/usr/bin/env python3
"""
Get description (definition, unit, value type) for eClass parameters by IRDI.
Set ECLASS_CDP_KEY (or ECLASS_CDP_API_KEY), then:

  # One or more IRDIs as arguments
  python get_eclass_description_by_irdi.py 0173-1#02-AAY070#001
  python get_eclass_description_by_irdi.py 0173-1-02-AAR710-003 0173-1#02-AAY070#001

  # Interactive: enter IRDIs one by one (empty line to quit)
  python get_eclass_description_by_irdi.py
"""

import sys
import os

if not os.path.isfile("enrichment_module.py"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir or ".")


def lookup_and_print(irdi: str, fetch):
    """Look up one IRDI and print result. Returns True if found."""
    irdi = irdi.strip()
    if not irdi:
        return False
    result = fetch(irdi)
    print(f"  IRDI: {irdi}")
    if not result:
        print("  -> No result (invalid IRDI or API error)")
        return False
    if result.get("definition"):
        print("  Description:", result["definition"])
    if result.get("usage"):
        print("  Usage:", result["usage"])
    if result.get("unit"):
        print("  Unit:", result["unit"])
    if result.get("value_type"):
        print("  Value type:", result["value_type"])
    print("  -> OK")
    return True


def main():
    try:
        from enrichment_module import get_eclass_description_by_irdi
    except ImportError as e:
        print(f"Error: {e}")
        print("Run from project root (e.g. d:\\Thesis\\template)")
        return 1

    # IRDIs from command line
    args = [a.strip() for a in sys.argv[1:] if a.strip()]

    if args:
        # One or more IRDIs as arguments
        print("eClass description lookup")
        print("-" * 50)
        for i, irdi in enumerate(args, 1):
            if len(args) > 1:
                print(f"\n[{i}/{len(args)}] {irdi}")
            lookup_and_print(irdi, get_eclass_description_by_irdi)
        return 0

    # Interactive: prompt for IRDIs
    print("eClass description lookup (interactive)")
    print("-" * 50)
    print("Enter an IRDI and press Enter to look up description.")
    print("Examples: 0173-1#02-AAY070#001   or  0173-1-02-AAR710-003")
    print("Empty line to quit.")
    print()
    while True:
        try:
            irdi = input("IRDI> ").strip()
        except EOFError:
            break
        if not irdi:
            print("Done.")
            break
        print()
        lookup_and_print(irdi, get_eclass_description_by_irdi)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
