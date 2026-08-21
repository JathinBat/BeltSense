#!/usr/bin/env python3
"""
Quick test to validate that the real-time scraper dependencies and configuration are working
"""

import sys
import importlib
import os
from pathlib import Path

def test_dependencies():
    """Test if all required dependencies are available"""
    required_modules = [
        'requests', 'PIL', 'tkinter', 'threading', 
        'random', 'hashlib', 'json', 'pathlib', 'time'
    ]
    
    print("🔍 Testing dependencies...")
    missing_modules = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} - OK")
        except ImportError:
            print(f"❌ {module} - MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️  Missing modules: {', '.join(missing_modules)}")
        return False
    else:
        print("\n✅ All dependencies are available!")
        return True

def test_folder_structure():
    """Test if the folder structure is correct"""
    print("\n📁 Testing folder structure...")
    base_path = Path("Manually classified")
    
    required_folders = [
        "Wearing Seatbelt",
        "Not Wearing Seatbelt", 
        "Unclassified",
        "Invalid-Unclear"
    ]
    
    # Create base folder if it doesn't exist
    base_path.mkdir(exist_ok=True)
    
    all_good = True
    for folder in required_folders:
        folder_path = base_path / folder
        if folder_path.exists():
            print(f"✅ {folder_path} - OK")
        else:
            print(f"❌ {folder_path} - MISSING")
            folder_path.mkdir(exist_ok=True)
            print(f"  📂 Created {folder_path}")
            all_good = False
    
    return all_good

def test_scraper_file():
    """Test if the scraper file exists and has basic structure"""
    print("\n📄 Testing scraper file...")
    scraper_file = Path("real_time_scraper.py")
    
    if not scraper_file.exists():
        print("❌ real_time_scraper.py - MISSING")
        return False
    
    print("✅ real_time_scraper.py - EXISTS")
    
    # Check for key methods/classes
    content = scraper_file.read_text(encoding='utf-8')
    required_elements = [
        'class RealTimeAnnotator',
        'def scrape_pixabay_api',
        'def manual_next_image',
        'def classify_image',
        'def load_next_image'
    ]
    
    all_good = True
    for element in required_elements:
        if element in content:
            print(f"✅ {element} - OK")
        else:
            print(f"❌ {element} - MISSING")
            all_good = False
    
    return all_good

def main():
    """Main test function"""
    print("🧪 Real-Time Scraper Configuration Test")
    print("=" * 50)
    
    # Run all tests
    deps_ok = test_dependencies()
    folders_ok = test_folder_structure()
    scraper_ok = test_scraper_file()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"Folder Structure: {'✅ PASS' if folders_ok else '❌ FAIL'}")  
    print(f"Scraper File: {'✅ PASS' if scraper_ok else '❌ FAIL'}")
    
    if deps_ok and folders_ok and scraper_ok:
        print("\n🎉 ALL TESTS PASSED! The scraper should work correctly.")
        print("💡 Run 'python real_time_scraper.py' to start the application.")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
    
    return deps_ok and folders_ok and scraper_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)