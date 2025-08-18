#!/usr/bin/env python
"""
Check database content for search debugging
"""
import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from ocr.models import ScannedFile, FileProcessingLog
from django.db.models import Q

print("=== DATABASE CONTENT CHECK ===")
print()

print("FileProcessingLog entries:")
logs = FileProcessingLog.objects.all()
print(f"Total: {logs.count()}")
for log in logs[:10]:  # Show first 10
    print(f"  - {log.original_filename} | Status: {log.status} | Date: {log.processed_at}")

print()
print("ScannedFile entries:")
files = ScannedFile.objects.all()
print(f"Total: {files.count()}")
for file in files[:10]:  # Show first 10
    print(f"  - {file.original_name} | Renamed: {file.renamed_file} | Date: {file.uploaded_at}")

print()
print("=== SEARCH TEST ===")
test_query = "test"
print(f"Searching for '{test_query}' in FileProcessingLog...")
search_results = FileProcessingLog.objects.filter(
    Q(original_filename__icontains=test_query) | 
    Q(final_filename__icontains=test_query) |
    Q(extracted_name__icontains=test_query) |
    Q(extracted_account__icontains=test_query)
)
print(f"Found {search_results.count()} results")
for result in search_results:
    print(f"  - {result.original_filename} ({result.status})")

print()
print("Searching in ScannedFile...")
scanned_results = ScannedFile.objects.filter(
    Q(original_name__icontains=test_query) | 
    Q(renamed_file__icontains=test_query) |
    Q(extracted_text__icontains=test_query)
)
print(f"Found {scanned_results.count()} results")
for result in scanned_results:
    print(f"  - {result.original_name}")
