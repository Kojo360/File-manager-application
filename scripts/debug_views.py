import os
import sys
import traceback

# Ensure project root is on sys.path so imports like 'backend' and 'ocr' work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from importlib import import_module

rf = RequestFactory()
# SessionMiddleware requires a get_response callable; provide a simple lambda
mw = SessionMiddleware(get_response=lambda req: None)

views_to_test = [
    ('test_view', 'ocr.views', rf.get('/test/')),
    ('upload_file', 'ocr.views', rf.get('/')),
    ('search_files', 'ocr.views', rf.get('/search/?q=test')),
    ('fully_indexed_files', 'ocr.views', rf.get('/fully-indexed/')),
    ('partially_indexed_files', 'ocr.views', rf.get('/partially-indexed/')),
    ('failed_files', 'ocr.views', rf.get('/failed/')),
    ('statistics_view', 'ocr.views', rf.get('/statistics/')),
]

for name, module_name, req in views_to_test:
    print('\n=== VIEW:', name, '===')
    try:
        mod = import_module(module_name)
        view = getattr(mod, name)

        # Ensure session is available on the request
        mw.process_request(req)
        req.session.save()

        # Call view
        resp = view(req)

        # Print response status and a snippet of content
        try:
            status = getattr(resp, 'status_code', 'N/A')
            content = getattr(resp, 'content', b'')
            print('STATUS:', status)
            print(content.decode('utf-8', 'replace')[:2000])
        except Exception as e:
            print('Response returned but could not decode content:', e)

    except Exception:
        print('EXCEPTION in', name)
        print(traceback.format_exc())

# Special-case serve_processed_file which requires a file_path arg
print('\n=== VIEW: serve_processed_file ===')
try:
    mod = import_module('ocr.views')
    view = getattr(mod, 'serve_processed_file')
    req = rf.get('/file/somefile.pdf')
    mw.process_request(req)
    req.session.save()
    resp = view(req, 'nonexistent.pdf')
    print('STATUS:', getattr(resp, 'status_code', 'N/A'))
    print(getattr(resp, 'content', b'')[:2000])
except Exception:
    print('EXCEPTION in serve_processed_file')
    print(traceback.format_exc())
