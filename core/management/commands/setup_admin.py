from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Setup admin user and user groups with proper permissions'

    def handle(self, *args, **options):
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
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))
        else:
            # Update password if user exists
            admin_user.set_password('Beast360@fma')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated admin user: {admin_user.username}'))

        # Create user groups
        admin_group, created = Group.objects.get_or_create(name='Administrators')
        regular_group, created = Group.objects.get_or_create(name='Regular Users')

        # Add admin to admin group
        admin_user.groups.add(admin_group)

        # Give admin group all permissions
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)

        # Give regular users only specific permissions
        # Get content types for our models
        from ocr.models import OCRDocument, ProcessingSession
        
        ocr_ct = ContentType.objects.get_for_model(OCRDocument)
        session_ct = ContentType.objects.get_for_model(ProcessingSession)
        
        # Regular users can only view and download documents
        regular_permissions = Permission.objects.filter(
            content_type__in=[ocr_ct, session_ct],
            codename__in=['view_ocrdocument', 'view_processingsession']
        )
        
        regular_group.permissions.set(regular_permissions)

        self.stdout.write(self.style.SUCCESS('Successfully set up user groups and permissions'))
        self.stdout.write(self.style.SUCCESS(f'Admin username: Kojo_360'))
        self.stdout.write(self.style.SUCCESS(f'Admin password: Beast360@fma'))
