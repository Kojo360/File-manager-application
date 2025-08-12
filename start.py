#!/usr/bin/env python
import os
import subprocess
import sys

def main():
    # Get PORT from environment, default to 8000 (Railway usually provides this)
    port = os.environ.get('PORT', '8000')
    
    print(f"=== Railway Django Startup ===")
    print(f"PORT environment variable: {repr(os.environ.get('PORT'))}")
    print(f"Using port: {port}")
    print(f"Python executable: {sys.executable}")
    
    try:
        # Run migrations
        print("Running Django migrations...")
        result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], 
                              check=True, capture_output=True, text=True)
        print("Migrations completed successfully")
        
        # Start gunicorn with more verbose output
        print(f"Starting gunicorn on 0.0.0.0:{port} with 2 workers")
        cmd = [
            'gunicorn', 
            'backend.wsgi:application',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '2',
            '--timeout', '120',
            '--access-logfile', '-',  # Log to stdout
            '--error-logfile', '-',   # Log errors to stderr
            '--log-level', 'info'
        ]
        
        print(f"Gunicorn command: {' '.join(cmd)}")
        
        # Replace current process with gunicorn
        os.execvp('gunicorn', cmd)
        
    except subprocess.CalledProcessError as e:
        print(f"Error during startup: {e}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
