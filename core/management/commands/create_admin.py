from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create admin user for production deployment'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Admin username')
        parser.add_argument('--password', type=str, default='admin123', help='Admin password')
        parser.add_argument('--email', type=str, default='admin@example.com', help='Admin email')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        
        self.stdout.write(f"🔧 Creating admin user: {username}")
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.email = email
            user.save()
            self.stdout.write(
                self.style.WARNING(f"⚠️  Updated existing user: {username}")
            )
        else:
            # Create new superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            user.is_active = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Created new admin user: {username}")
            )
        
        self.stdout.write("\n🎯 Admin User Ready!")
        self.stdout.write(f"👤 Username: {username}")
        self.stdout.write(f"🔑 Password: {password}")
        self.stdout.write("🌐 Login at: /admin/")
        self.stdout.write("\n⚠️  IMPORTANT: Change password after first login!")
