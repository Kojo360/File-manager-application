"""Simple test to check URLs"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

try:
    from django.urls import reverse
    print("Django URLs import successful")
    
    # Test a few basic URLs (cleaned up)
    test_urls = ['ocr:search_files']
    for url_name in test_urls:
        try:
            url = reverse(url_name)
            print(f"✓ {url_name} resolves to: {url}")
        except Exception as e:
            print(f"✗ {url_name} failed: {e}")
            
except Exception as e:
    print(f"Django setup failed: {e}")
