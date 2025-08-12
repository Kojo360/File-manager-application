#!/usr/bin/env python
import os
import subprocess
import sys

def main():
    # Get PORT from environment, default to 8000
    port = os.environ.get('PORT', '8000')
    
    print(f"Starting Django application on port {port}")
    
    # Run migrations
    print("Running migrations...")
    result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
    
    # Start gunicorn
    print(f"Starting gunicorn on 0.0.0.0:{port}")
    cmd = [
        'gunicorn', 
        'backend.wsgi:application',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2'
    ]
    
    # Replace current process with gunicorn
    os.execvp('gunicorn', cmd)

if __name__ == '__main__':
    main()
