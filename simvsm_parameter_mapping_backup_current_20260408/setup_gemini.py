#!/usr/bin/env python3
"""
Gemini API Setup and Test Script

This script helps you:
1. Set up and test Gemini API connection
2. Verify your GOOGLE_API_KEY is working
3. Test Gemini description generation

Run this BEFORE running integrated_pipeline.py to ensure Gemini is properly configured.
"""

import os
import sys

def test_gemini_setup():
    """Test Gemini API setup and connection."""
    print("="*70)
    print("GEMINI API SETUP AND TEST")
    print("="*70)
    print()
    
    # Check for API key (new package uses GEMINI_API_KEY, but also check GOOGLE_API_KEY for compatibility)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set!")
        print()
        print("To set it:")
        print("  Windows PowerShell:")
        print('    $env:GEMINI_API_KEY="your-api-key-here"')
        print('    # Or: $env:GOOGLE_API_KEY="your-api-key-here"')
        print()
        print("  Windows CMD:")
        print('    set GEMINI_API_KEY=your-api-key-here')
        print('    # Or: set GOOGLE_API_KEY=your-api-key-here')
        print()
        print("  Linux/Mac:")
        print('    export GEMINI_API_KEY="your-api-key-here"')
        print('    # Or: export GOOGLE_API_KEY="your-api-key-here"')
        print()
        print("  Get your API key from: https://makersuite.google.com/app/apikey")
        print()
        return False
    
    env_var_name = "GEMINI_API_KEY" if os.getenv("GEMINI_API_KEY") else "GOOGLE_API_KEY"
    print(f"✅ {env_var_name} found: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # Try to import and initialize Gemini
    print("Testing Gemini API initialization...")
    print()
    
    try:
        # Import enrichment module which initializes Gemini
        from enrichment_module import GEMINI_AVAILABLE, GEMINI_CLIENT, GEMINI_MODEL
        
        if not GEMINI_AVAILABLE:
            print("❌ ERROR: Gemini API is not available!")
            print()
            print("Possible issues:")
            print("  1. google-genai or google-generativeai package not installed")
            print("     Install with: pip install google-genai")
            print("     Or legacy: pip install google-generativeai")
            print()
            print("  2. Invalid API key")
            print("     Get your API key from: https://makersuite.google.com/app/apikey")
            print()
            return False
        
        print("✅ Gemini API initialized successfully!")
        if GEMINI_CLIENT:
            print("   Using: google.genai package (new)")
        elif GEMINI_MODEL:
            print("   Using: google.generativeai package (legacy)")
        print()
        
        # Test a simple generation
        print("Testing Gemini description generation...")
        print()
        
        from enrichment_module import GeminiEnricher
        from semantic_node_enhanced import SemanticNode
        
        enricher = GeminiEnricher(use_gemini=True)
        
        # Create a test node
        test_node = SemanticNode(
            name="Temperature",
            value=25.0,
            value_type="Float",
            unit="°C"
        )
        
        print("Attempting to generate test description...")
        print("(Check DEBUG messages above if you see errors)")
        print()
        
        result = enricher.generate_description(test_node)
        
        if result:
            print("✅ Gemini test successful!")
            print()
            print("Generated description:")
            print(f"  Definition: {result.get('definition', 'N/A')[:100]}...")
            print(f"  Usage: {result.get('usage', 'N/A')[:100]}...")
            print()
            print("="*70)
            print("✅ GEMINI IS READY TO USE!")
            print("="*70)
            print()
            print("You can now run:")
            print("  python integrated_pipeline.py --source Data/source --target Data/target")
            print()
            return True
        else:
            print("⚠️  WARNING: Gemini API initialized but test generation failed.")
            print()
            print("Common issues and solutions:")
            print()
            print("  1. 401 or API_KEY_INVALID:")
            print("     → Re-generate your key at https://makersuite.google.com/app/apikey")
            print("     → Ensure no extra spaces when setting the env var")
            print()
            print("  2. 429 or RESOURCE_EXHAUSTED:")
            print("     → You hit the rate limit (free tier)")
            print("     → Wait a minute and try again")
            print()
            print("  3. 404 or NOT_FOUND (Model Name):")
            print("     → Update package: pip install -U google-generativeai")
            print()
            print("  4. User location is not supported:")
            print("     → Gemini API may not be available in your region")
            print("     → Check if VPN is needed")
            print()
            print("  5. AttributeError: 'Client' object has no attribute 'models':")
            print("     → SDK mismatch - ensure you're using the latest version")
            print("     → Try: pip install -U google-generativeai")
            print()
            print("Look for 'DEBUG:' messages above for specific error details.")
            print()
            print("You can still run the pipeline, but Gemini enrichment may not work.")
            print("Use --no-gemini flag to disable Gemini:")
            print("  python integrated_pipeline.py --source Data/source --target Data/target --no-gemini")
            print()
            return False
            
    except ImportError as e:
        print(f"❌ ERROR: Could not import required modules: {e}")
        print()
        print("Make sure all required files are in the same directory:")
        print("  - enrichment_module.py")
        print("  - semantic_node_enhanced.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        return False


if __name__ == "__main__":
    success = test_gemini_setup()
    sys.exit(0 if success else 1)

