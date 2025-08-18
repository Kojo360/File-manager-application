"""
Create a regular test user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User, Group

def create_regular_user():
    print("🔧 Creating regular test user...")
    
    # Create regular user
    regular_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'testuser@filemanager.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True
        }
    )
    
    if created:
        regular_user.set_password('testpass123')
        regular_user.save()
        print(f"✅ Created regular user: {regular_user.username}")
    else:
        regular_user.set_password('testpass123')
        regular_user.is_staff = False
        regular_user.is_superuser = False
        regular_user.save()
        print(f"✅ Updated regular user: {regular_user.username}")

    # Add to regular users group
    regular_group, created = Group.objects.get_or_create(name='Regular Users')
    regular_user.groups.add(regular_group)

    print("\n🎯 Regular User Setup Complete!")
    print(f"👤 Username: testuser")
    print(f"🔑 Password: testpass123")
    print(f"🌐 Login URL: http://127.0.0.1:8000/auth/login/")

if __name__ == "__main__":
    create_regular_user()
