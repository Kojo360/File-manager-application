# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from ocr.models import ScannedFile, FileProcessingLog
from django.db.models import Q
from .auth_decorators import admin_required, regular_user_allowed
import os
from datetime import datetime

def landing_page(request):
    """Landing page with search functionality for non-authenticated users"""
    return render(request, 'core/landing.html')

def search_results(request):
    """Search results page - accessible to everyone"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        print(f"=== CORE SEARCH DEBUG ===")
        print(f"Search query: '{query}'")
        
        # Get the absolute paths to the directories
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        FULLY_INDEXED_DIR = os.path.join(BASE_DIR, "fully_indexed")
        PARTIAL_INDEXED_DIR = os.path.join(BASE_DIR, "partially_indexed")
        
        print(f"Searching in: {FULLY_INDEXED_DIR}")
        print(f"Directory exists: {os.path.exists(FULLY_INDEXED_DIR)}")
        
        def get_files_from_directory(directory_path, status):
            """Get all files from a directory that match the search query"""
            files = []
            if os.path.exists(directory_path):
                all_files = os.listdir(directory_path)
                print(f"Found {len(all_files)} files in {status} directory")
                
                for filename in all_files:
                    file_path = os.path.join(directory_path, filename)
                    if os.path.isfile(file_path):
                        # Check if query matches filename (case-insensitive)
                        if query.lower() in filename.lower():
                            print(f"Match found: {filename}")
                            file_size = os.path.getsize(file_path)
                            file_modified = os.path.getmtime(file_path)
                            
                            # Try to get additional info from database
                            extracted_name = ""
                            extracted_account = ""
                            try:
                                log_entry = FileProcessingLog.objects.filter(
                                    Q(original_filename=filename) | Q(final_filename=filename)
                                ).first()
                                if log_entry:
                                    extracted_name = log_entry.extracted_name or ""
                                    extracted_account = log_entry.extracted_account or ""
                            except Exception as e:
                                print(f"Database query error: {e}")
                            
                            file_info = {
                                'filename': filename,
                                'original_filename': filename,
                                'file_path': file_path,
                                'status': status,
                                'file_size': file_size,
                                'processed_at': datetime.fromtimestamp(file_modified),
                                'extracted_name': extracted_name,
                                'extracted_account': extracted_account
                            }
                            
                            # Add status display method
                            file_info['get_status_display'] = lambda s=status: s.replace('_', ' ').title()
                            
                            files.append(file_info)
                        else:
                            print(f"No match: {filename} (looking for '{query}')")
            else:
                print(f"Directory does not exist: {directory_path}")
            return files
        
        # Search in fully indexed files (priority)
        results.extend(get_files_from_directory(FULLY_INDEXED_DIR, 'fully_indexed'))
        
        # Also search in partially indexed files
        results.extend(get_files_from_directory(PARTIAL_INDEXED_DIR, 'partially_indexed'))
        
        print(f"Total results found: {len(results)}")
        
        # Sort by modification time (newest first)
        results.sort(key=lambda x: x['processed_at'], reverse=True)
        
        # Limit results
        results = results[:50]
    
    context = {
        'search_results': results,
        'query': query,
        'results_count': len(results)
    }
    return render(request, 'core/landing.html', context)

@admin_required
def upload_file(request):
    """Upload functionality - Admin only"""
    return redirect('ocr:upload_file')

@regular_user_allowed
def search_files(request):
    """Search functionality for all authenticated users"""
    return redirect('ocr:search_files')
