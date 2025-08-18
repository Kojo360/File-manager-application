#!/usr/bin/env python
"""
Test script to validate all URL patterns work correctly
"""
import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.urls import reverse
from django.core.exceptions import NoReverseMatch

# List of URLs to test (cleaned up - removed deleted apps)
test_urls = [
    'ocr:search_files',
    'ocr:upload_file',
    'core:login',
    'admin:index',
]

print("Testing URL patterns...")
print("=" * 50)

for url_name in test_urls:
    try:
        url = reverse(url_name)
        print(f"✓ {url_name} -> {url}")
    except NoReverseMatch as e:
        print(f"✗ {url_name} -> ERROR: {e}")
    except Exception as e:
        print(f"? {url_name} -> UNEXPECTED ERROR: {e}")

print("=" * 50)
print("URL testing complete!")
