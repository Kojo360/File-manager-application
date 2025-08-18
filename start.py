#!/usr/bin/env python
import os
import subprocess
import sys

def main():
    # Get PORT from environment, Railway typically uses ports like 8080, 3000, etc.
    port = os.environ.get('PORT', '8000')
    
    print(f"=== Railway Django Startup ===")
    print(f"All environment variables containing 'PORT':")
    for key, value in os.environ.items():
        if 'PORT' in key.upper():
            print(f"  {key} = {value}")
    
    print(f"Using port: {port}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    
    try:
        # Run migrations
        print("=== Running Django migrations ===")
        subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], 
                      check=True)
        print("✅ Migrations completed successfully")
        
        # Create admin user
        print("=== Creating admin user ===")
        subprocess.run([sys.executable, 'manage.py', 'create_admin'], 
                      check=True)
        print("✅ Admin user created successfully")
        
        # Start gunicorn
        print(f"=== Starting gunicorn on 0.0.0.0:{port} ===")
        
        # Use os.execvp to replace the current process
        os.execvp('gunicorn', [
            'gunicorn',
            'backend.wsgi:application',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '2',
            '--timeout', '120',
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--log-level', 'info',
            '--preload'
        ])
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during startup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
