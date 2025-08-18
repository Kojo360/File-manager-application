"""
Simple URL test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.urls import reverse
from django.test import Client

def test_urls():
    print("🔧 Testing URL patterns...")
    
    try:
        # Test analytics URLs
        analytics_urls = [
            'analytics:executive_dashboard',
            'analytics:analytics_overview',
            'analytics:custom_reports'
        ]
        
        for url_name in analytics_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
        
        # Test AI features URLs
        ai_urls = ['ai_features:dashboard']
        for url_name in ai_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
        
        # Test workflows URLs
        workflow_urls = ['workflows:dashboard']
        for url_name in workflow_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
                
        # Test OCR URLs
        ocr_urls = ['ocr:upload_file', 'ocr:search_files']
        for url_name in ocr_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
                
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    test_urls()
