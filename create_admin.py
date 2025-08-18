#!/usr/bin/env python
"""
Simple Admin User Creator for Production Deployment
Run this after deployment to create an admin user
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_production')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    print("🔧 Creating admin user for production...")
    
    # Check if admin already exists
    if User.objects.filter(username='admin').exists():
        print("⚠️  Admin user already exists!")
        user = User.objects.get(username='admin')
        # Reset password
        user.set_password('admin123')
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        print("✅ Updated existing admin user")
    else:
        # Create new admin user
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        user.is_active = True
        user.save()
        print("✅ Created new admin user")
    
    print("\n🎯 Admin User Ready!")
    print("👤 Username: admin")
    print("🔑 Password: admin123")
    print("🌐 Login at: /admin/")
    print("\n⚠️  IMPORTANT: Change this password after first login!")

if __name__ == "__main__":
    create_admin_user()
