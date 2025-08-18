"""
Setup Admin User and Permissions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

def setup_admin():
    print("🔧 Setting up admin user and permissions...")
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='Kojo_360',
        defaults={
            'email': 'admin@filemanager.com',
            'first_name': 'Kojo',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    if created:
        admin_user.set_password('Beast360@fma')
        admin_user.save()
        print(f"✅ Created admin user: {admin_user.username}")
    else:
        # Update password if user exists
        admin_user.set_password('Beast360@fma')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print(f"✅ Updated admin user: {admin_user.username}")

    # Create user groups
    admin_group, created = Group.objects.get_or_create(name='Administrators')
    regular_group, created = Group.objects.get_or_create(name='Regular Users')

    # Add admin to admin group
    admin_user.groups.add(admin_group)

    # Give admin group all permissions
    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)
    print(f"✅ Admin group has {all_permissions.count()} permissions")

    # Give regular users only specific permissions
    from ocr.models import ScannedFile, ProcessingStatistics
    
    scanned_ct = ContentType.objects.get_for_model(ScannedFile)
    stats_ct = ContentType.objects.get_for_model(ProcessingStatistics)
    
    # Regular users can only view documents
    regular_permissions = Permission.objects.filter(
        content_type__in=[scanned_ct, stats_ct],
        codename__in=['view_scannedfile', 'view_processingstatistics']
    )
    
    regular_group.permissions.set(regular_permissions)
    print(f"✅ Regular users group has {regular_permissions.count()} permissions")

    print("\n🎯 Admin Setup Complete!")
    print(f"👤 Admin Username: Kojo_360")
    print(f"🔑 Admin Password: Beast360@fma")
    print(f"🌐 Login URL: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    setup_admin()
