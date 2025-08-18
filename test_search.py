#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import RequestFactory
from ocr.views import search_files

def test_search_functionality():
    """Test the search functionality directly"""
    print("=== Testing Search Functionality ===")
    
    # Create a mock request
    factory = RequestFactory()
    
    # Test 1: Search without query (should return all files)
    print("\n1. Testing search without query...")
    request = factory.get('/search/')
    response = search_files(request)
    print(f"Response status: {response.status_code}")
    
    # Test 2: Search with query
    print("\n2. Testing search with query 'KOJO'...")
    request = factory.get('/search/?q=KOJO')
    response = search_files(request)
    print(f"Response status: {response.status_code}")
    
    # Test 3: Check files in directories directly
    print("\n3. Checking directories directly...")
    base_dir = os.path.abspath(os.path.dirname(__file__))
    fully_indexed_dir = os.path.join(base_dir, "fully_indexed")
    
    if os.path.exists(fully_indexed_dir):
        files = os.listdir(fully_indexed_dir)
        print(f"Files in fully_indexed: {len(files)}")
        for file in files[:3]:  # Show first 3 files
            print(f"  - {file}")
    else:
        print("fully_indexed directory doesn't exist!")

if __name__ == "__main__":
    test_search_functionality()
