"""
Test Authentication System
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

def test_authentication():
    print("🔧 Testing Authentication System...")
    
    # Create test client
    client = Client()
    
    # Test 1: Unauthenticated access
    print("\n📋 Test 1: Unauthenticated Access")
    response = client.get('/')
    print(f"   Home redirect status: {response.status_code}")
    
    # Test 2: Admin login
    print("\n📋 Test 2: Admin Authentication")
    admin_user = User.objects.get(username='Kojo_360')
    login_success = client.login(username='Kojo_360', password='Beast360@fma')
    print(f"   Admin login success: {login_success}")
    
    if login_success:
        # Test admin access to upload
        response = client.get('/upload/')
        print(f"   Admin upload access: {response.status_code}")
        
        # Test admin access to analytics
        response = client.get('/analytics/')
        print(f"   Admin analytics access: {response.status_code}")
    
    client.logout()
    
    # Test 3: Regular user login
    print("\n📋 Test 3: Regular User Authentication")
    regular_user = User.objects.get(username='testuser')
    login_success = client.login(username='testuser', password='testpass123')
    print(f"   Regular user login success: {login_success}")
    
    if login_success:
        # Test regular user access to search
        response = client.get('/search/')
        print(f"   Regular user search access: {response.status_code}")
        
        # Test regular user blocked from upload
        response = client.get('/upload/')
        print(f"   Regular user upload blocked: {response.status_code} (should be redirect)")
        
        # Test regular user blocked from analytics
        response = client.get('/analytics/')
        print(f"   Regular user analytics blocked: {response.status_code} (should be redirect)")
    
    print("\n✅ Authentication testing complete!")
    print("\n📌 URL Structure:")
    print("   🏠 Home: http://127.0.0.1:8000/")
    print("   🔐 Login: http://127.0.0.1:8000/auth/login/")
    print("   📤 Upload (Admin): http://127.0.0.1:8000/upload/")
    print("   🔍 Search (All): http://127.0.0.1:8000/search/")
    print("   📊 Analytics (Admin): http://127.0.0.1:8000/analytics/")

if __name__ == "__main__":
    test_authentication()
