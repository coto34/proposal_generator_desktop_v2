#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
Run this to confirm everything is properly installed
"""
import os

def test_imports():
    print("🧪 Testing all imports...")
    results = {}
    
    # Test each import individually
    tests = [
        ("pypdf", "import pypdf"),
        ("python-docx", "from docx import Document"),
        ("pdfminer.six", "from pdfminer.high_level import extract_text"),
        ("docxtpl", "from docxtpl import DocxTemplate"),
        ("openpyxl", "import openpyxl"),
        ("openpyxl.styles", "from openpyxl.styles import Font, Alignment"),
        ("pathlib", "from pathlib import Path"),
        ("typing", "from typing import Optional, Dict, Any"),
        ("json", "import json"),
        ("os", "import os")
    ]
    
    for name, import_statement in tests:
        try:
            exec(import_statement)
            results[name] = "✅ OK"
        except ImportError as e:
            results[name] = f"❌ FAIL: {e}"
        except Exception as e:
            results[name] = f"⚠️  ERROR: {e}"
    
    # Print results
    print("\n📊 Import Test Results:")
    print("-" * 50)
    for name, status in results.items():
        print(f"{name:15} {status}")
    
    # Summary
    failed = [name for name, status in results.items() if "❌" in status or "⚠️" in status]
    
    if not failed:
        print(f"\n🎉 All imports successful! VS Code flags are likely just IDE issues.")
        print("📝 Suggestions:")
        print("   1. Restart VS Code")
        print("   2. Reload window (Ctrl+Shift+P > 'Developer: Reload Window')")
        print("   3. Check Python interpreter is set to your venv")
        return True
    else:
        print(f"\n❌ {len(failed)} imports failed: {', '.join(failed)}")
        return False

def test_document_processor():
    """Test DocumentProcessor functionality"""
    print("\n🧪 Testing DocumentProcessor...")
    
    try:
        from services.document_processor import DocumentProcessor
        
        # Test dependency checking
        deps = DocumentProcessor.check_dependencies()
        print("\n📊 DocumentProcessor Dependency Status:")
        for dep, available in deps.items():
            status = "✅" if available else "❌"
            print(f"  {status} {dep}")
        
        missing = DocumentProcessor.get_missing_dependencies()
        if missing:
            print("\n🔧 Missing dependencies (install commands):")
            for cmd in missing:
                print(f"  {cmd}")
        else:
            print("\n✅ All DocumentProcessor dependencies available!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import DocumentProcessor: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error testing DocumentProcessor: {e}")
        return False

def test_project_structure():
    """Test project structure"""
    print("\n🧪 Testing project structure...")
    
    required_files = [
        "app.py",
        "services/__init__.py",
        "services/llm_providers.py", 
        "services/document_processor.py",
        "services/token_manager.py",
        "ui/wizard.py",
        "ui/components.py",
        "validation/schemas.py",
        "requirements.txt",
        ".env"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"  - {file}")
    else:
        print("✅ All required files present!")
    
    return len(missing_files) == 0

if __name__ == "__main__":
    print("🚀 Proposal Generator - Import & Setup Test")
    print("=" * 50)
    
    # Run all tests
    import_success = test_imports()
    processor_success = test_document_processor()
    structure_success = test_project_structure()
    
    print("\n" + "=" * 50)
    if import_success and processor_success and structure_success:
        print("🎉 ALL TESTS PASSED! Your setup is ready to go!")
        print("\n🚀 You can now run: python app.py")
    else:
        print("⚠️  Some issues found. Check the details above.")
        
    print("=" * 50)