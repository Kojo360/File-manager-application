from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.utils.encoding import smart_str
from .forms import FileUploadForm
from .utils import log_file_processing, get_processing_statistics, get_file_size_formatted, get_session_statistics, reset_session_statistics
import sys
import os

# Optional import for watcher functionality
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../core/ocr')))
    from watcher import route_file
    WATCHER_AVAILABLE = True
except ImportError:
    WATCHER_AVAILABLE = False
    def route_file(file_path):
        # Fallback function when watcher is not available
        return file_path

from .models import ScannedFile, FileProcessingLog, ProcessingStatistics
from django.db.models import Q
import os

def test_view(request):
    """Simple test view to check if Django is working"""
    return HttpResponse("<h1>Django is working! ✅</h1><p>File Manager App is running on Render</p>")

def debug_ocr(request):
    """Debug OCR installation and capabilities"""
    import subprocess
    import sys
    import shutil
    
    debug_info = []
    
    # Check Python environment
    debug_info.append(f"Python version: {sys.version}")
    debug_info.append(f"Python executable: {sys.executable}")
    
    # Check tesseract installation
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        debug_info.append(f"Tesseract version: {result.stdout.split()[1] if result.stdout else 'Unknown'}")
        debug_info.append(f"Tesseract path: {shutil.which('tesseract')}")
    except Exception as e:
        debug_info.append(f"Tesseract ERROR: {str(e)}")
    
    # Check pytesseract
    try:
        import pytesseract
        debug_info.append(f"pytesseract version: {pytesseract.__version__}")
        debug_info.append(f"pytesseract tesseract_cmd: {pytesseract.pytesseract.tesseract_cmd}")
        
        # Test OCR on a simple image
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create a test image
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Test OCR", fill='black')
        
        # Try OCR
        text = pytesseract.image_to_string(img)
        debug_info.append(f"OCR test result: '{text.strip()}'")
        
    except Exception as e:
        debug_info.append(f"pytesseract ERROR: {str(e)}")
    
    # Check poppler (for PDF processing)
    try:
        from pdf2image import convert_from_path
        debug_info.append("pdf2image import: SUCCESS")
        
        # Check poppler utilities
        for util in ['pdftoppm', 'pdfinfo']:
            path = shutil.which(util)
            debug_info.append(f"{util} path: {path if path else 'NOT FOUND'}")
            
    except Exception as e:
        debug_info.append(f"pdf2image ERROR: {str(e)}")
    
    # Check watcher availability
    debug_info.append(f"Watcher available: {WATCHER_AVAILABLE}")
    
    # Environment variables
    import os
    debug_info.append(f"PATH: {os.environ.get('PATH', 'Not set')}")
    
    html = "<h1>OCR Debug Information</h1>\n"
    html += "<pre>\n" + "\n".join(debug_info) + "\n</pre>\n"
    html += "<p><a href='/'>Back to upload</a></p>"
    
    return HttpResponse(html)


def upload_file(request):
    """Main upload view with full OCR functionality"""
    try:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        
        if request.method == 'POST':
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                # Create a simple uploads directory in the container
                uploads_dir = '/tmp/uploads'
                os.makedirs(uploads_dir, exist_ok=True)

                uploaded_files = request.FILES.getlist('files')
                
                # Limit to 50 files for production
                if len(uploaded_files) > 50:
                    messages.error(request, "You can upload a maximum of 50 files at once.")
                    return redirect('upload_file')

                processed_count = 0
                failed_count = 0
                fully_indexed_count = 0
                partially_indexed_count = 0
                ocr_failed_count = 0

                for uploaded_file in uploaded_files:
                    try:
                        # Save temporarily
                        temp_path = os.path.join(uploads_dir, uploaded_file.name)
                        with open(temp_path, 'wb+') as dest:
                            for chunk in uploaded_file.chunks():
                                dest.write(chunk)

                        # Log the upload
                        log_file_processing(
                            original_filename=uploaded_file.name,
                            status='uploaded',
                            file_size=uploaded_file.size,
                            session_key=session_key
                        )

                        # Process with OCR if available
                        final_status = 'failed'  # Default if something goes wrong
                        if WATCHER_AVAILABLE:
                            try:
                                processed_path = route_file(temp_path)
                                if processed_path:
                                    # Determine status based on which directory the file ended up in
                                    if 'fully_indexed' in processed_path:
                                        final_status = 'fully_indexed'
                                        fully_indexed_count += 1
                                    elif 'partially_indexed' in processed_path:
                                        final_status = 'partially_indexed'
                                        partially_indexed_count += 1
                                    else:
                                        final_status = 'failed'
                                        ocr_failed_count += 1
                                else:
                                    final_status = 'failed'
                                    ocr_failed_count += 1
                            except Exception as ocr_error:
                                # OCR failed, but file was uploaded
                                print(f"OCR processing failed: {ocr_error}")
                                final_status = 'failed'
                                ocr_failed_count += 1
                        else:
                            # No OCR available, consider as failed processing
                            final_status = 'failed'
                            ocr_failed_count += 1

                        # Log final processing status (this updates session statistics correctly)
                        log_file_processing(
                            original_filename=uploaded_file.name,
                            status=final_status,
                            file_size=uploaded_file.size,
                            session_key=session_key
                        )

                        processed_count += 1

                    except Exception as e:
                        log_file_processing(
                            original_filename=uploaded_file.name,
                            status='failed',
                            error_message=str(e),
                            file_size=uploaded_file.size if hasattr(uploaded_file, 'size') else 0,
                            session_key=session_key
                        )
                        failed_count += 1

                # Show results with better messaging
                if processed_count > 0:
                    message_parts = []
                    if fully_indexed_count > 0:
                        message_parts.append(f"{fully_indexed_count} fully indexed")
                    if partially_indexed_count > 0:
                        message_parts.append(f"{partially_indexed_count} partially indexed")
                    if ocr_failed_count > 0:
                        message_parts.append(f"{ocr_failed_count} OCR failed")
                    
                    if message_parts:
                        message = f"Successfully processed {processed_count} files: " + ", ".join(message_parts) + "!"
                        if fully_indexed_count > 0:
                            messages.success(request, message)
                        else:
                            messages.warning(request, message)
                    else:
                        messages.success(request, f"Successfully processed {processed_count} files!")
                        
                if failed_count > 0:
                    messages.error(request, f"Failed to upload {failed_count} files.")

                return redirect('upload_file')
                
        else:
            form = FileUploadForm()

        # Get session-specific statistics
        try:
            statistics = get_session_statistics(session_key)
        except Exception as e:
            statistics = {
                'total_files': 0,
                'fully_indexed': 0,
                'partially_indexed': 0,
                'failed': 0,
                'total_size': 0,
                'average_size': 0,
                'last_upload': None,
                'first_upload': None,
                'success_rate': 0
            }

        return render(request, 'ocr/upload.html', {
            'form': form,
            'statistics': statistics,
            'watcher_available': WATCHER_AVAILABLE,
        })
        
    except Exception as e:
        return HttpResponse(f"<h1>Upload Error</h1><p>{str(e)}</p><p><a href='/test/'>Test page</a> | <a href='/search/'>Search</a></p>")


def search_files(request):
    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', '').strip()
    
    # Advanced filter parameters
    min_size = request.GET.get('min_size', '').strip()
    max_size = request.GET.get('max_size', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    has_name = request.GET.get('has_name', '').strip()
    has_account = request.GET.get('has_account', '').strip()
    
    # Get the absolute paths to the three directories
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    FULLY_INDEXED_DIR = os.path.join(BASE_DIR, "fully_indexed")
    PARTIAL_INDEXED_DIR = os.path.join(BASE_DIR, "partially_indexed")
    FAILED_DIR = os.path.join(BASE_DIR, "failed")
    
    # Ensure directories exist
    for directory in [FULLY_INDEXED_DIR, PARTIAL_INDEXED_DIR, FAILED_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    def should_include_file(filename, file_path, file_size, file_modified):
        """Check if file should be included based on all filters"""
        # Text search filter
        if query and query.lower() not in filename.lower():
            return False
        
        # File type filters
        if filter_type == 'pdf' and not filename.lower().endswith('.pdf'):
            return False
        if filter_type == 'image' and not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']):
            return False
        
        # File size filters
        file_size_kb = file_size / 1024
        if filter_type == 'large' and file_size_kb <= 1024:  # Less than 1MB
            return False
        if filter_type == 'small' and file_size_kb >= 100:  # More than 100KB
            return False
        
        # Advanced size filters
        if min_size and file_size_kb < float(min_size):
            return False
        if max_size and file_size_kb > float(max_size):
            return False
        
        # Date filters
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        file_date = datetime.fromtimestamp(file_modified).date()
        today = timezone.now().date()
        
        if filter_type == 'today' and file_date != today:
            return False
        if filter_type == 'week' and file_date < (today - timedelta(days=7)):
            return False
        if filter_type == 'month' and file_date < (today - timedelta(days=30)):
            return False
        
        # Advanced date filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                if file_date < from_date:
                    return False
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                if file_date > to_date:
                    return False
            except ValueError:
                pass
        
        # Name and account filters (check against database records)
        if has_name or has_account:
            try:
                # Look for processing logs with this filename
                log_entry = FileProcessingLog.objects.filter(
                    Q(original_filename=filename) | Q(final_filename=filename)
                ).first()
                
                if log_entry:
                    if has_name and has_name.lower() not in (log_entry.extracted_name or '').lower():
                        return False
                    if has_account and has_account.lower() not in (log_entry.extracted_account or '').lower():
                        return False
                else:
                    # If no log entry and name/account filters are applied, exclude
                    if has_name or has_account:
                        return False
            except:
                # If database query fails, skip name/account filtering
                pass
        
        return True
    
    def get_files_from_directory(directory_path, status):
        """Get all files from a directory and return them with their status"""
        files = []
        if os.path.exists(directory_path):
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_modified = os.path.getmtime(file_path)
                    
                    # Apply all filters
                    if should_include_file(filename, file_path, file_size, file_modified):
                        file_info = {
                            'name': filename,
                            'path': file_path,
                            'status': status,
                            'size': file_size,
                            'modified': file_modified
                        }
                        files.append(file_info)
        return files
    
    # Get files from directories based on processing status filter
    if filter_type == 'fully_indexed':
        fully_indexed_files = get_files_from_directory(FULLY_INDEXED_DIR, 'fully_indexed')
        partially_indexed_files = []
        failed_files = []
    elif filter_type == 'partially_indexed':
        fully_indexed_files = []
        partially_indexed_files = get_files_from_directory(PARTIAL_INDEXED_DIR, 'partially_indexed')
        failed_files = []
    elif filter_type == 'failed':
        fully_indexed_files = []
        partially_indexed_files = []
        failed_files = get_files_from_directory(FAILED_DIR, 'failed')
    else:  # All other filters or no processing status filter
        fully_indexed_files = get_files_from_directory(FULLY_INDEXED_DIR, 'fully_indexed')
        partially_indexed_files = get_files_from_directory(PARTIAL_INDEXED_DIR, 'partially_indexed')
        failed_files = get_files_from_directory(FAILED_DIR, 'failed')
    
    # Sort files by modification time (newest first)
    for file_list in [fully_indexed_files, partially_indexed_files, failed_files]:
        file_list.sort(key=lambda x: x['modified'], reverse=True)
    
    # Get comprehensive statistics
    processing_stats = get_processing_statistics()
    
    # Calculate statistics for current files
    stats = {
        'fully_indexed_count': len(fully_indexed_files),
        'partially_indexed_count': len(partially_indexed_files),
        'failed_count': len(failed_files),
        'total_count': len(fully_indexed_files) + len(partially_indexed_files) + len(failed_files)
    }
    
    # Calculate total file sizes
    total_size = sum(f['size'] for f in fully_indexed_files + partially_indexed_files + failed_files)
    
    # Get recent activity from database
    recent_activity = FileProcessingLog.objects.order_by('-processed_at')[:10]
    
    # Get daily statistics for the last 7 days
    from datetime import timedelta
    from django.utils import timezone
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    daily_stats = ProcessingStatistics.objects.filter(
        date__gte=seven_days_ago
    ).order_by('-date')
    
    return render(request, 'ocr/search.html', {
        'fully_indexed_files': fully_indexed_files,
        'partially_indexed_files': partially_indexed_files,
        'failed_files': failed_files,
        'stats': stats,
        'processing_stats': processing_stats,
        'recent_activity': recent_activity,
        'daily_stats': daily_stats,
        'total_size_formatted': get_file_size_formatted(total_size),
        'query': query,
        'has_query': bool(query),
        'filter_type': filter_type,
        'has_filter': bool(filter_type or min_size or max_size or date_from or date_to or has_name or has_account),
        'has_advanced_filters': bool(min_size or max_size or date_from or date_to or has_name or has_account),
    })

def serve_processed_file(request, file_path):
    """Serve processed files from the three processing directories"""
    # Decode the file path
    import urllib.parse
    file_path = urllib.parse.unquote(file_path)
    
    # Get the absolute paths to the three directories
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    FULLY_INDEXED_DIR = os.path.join(BASE_DIR, "fully_indexed")
    PARTIAL_INDEXED_DIR = os.path.join(BASE_DIR, "partially_indexed")
    FAILED_DIR = os.path.join(BASE_DIR, "failed")
    
    # Check if the file exists in any of the three directories
    for directory in [FULLY_INDEXED_DIR, PARTIAL_INDEXED_DIR, FAILED_DIR]:
        full_path = os.path.join(directory, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                response = FileResponse(
                    open(full_path, 'rb'), 
                    as_attachment=False,
                    filename=smart_str(os.path.basename(file_path))
                )
                return response
            except IOError:
                raise Http404("File not accessible")
    
    raise Http404("File not found")

def reset_statistics(request):
    """Reset session statistics"""
    try:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        
        if reset_session_statistics(session_key):
            messages.success(request, "Statistics have been reset successfully!")
        else:
            messages.error(request, "Failed to reset statistics.")
            
    except Exception as e:
        messages.error(request, f"Error resetting statistics: {str(e)}")
    
    return redirect('upload_file')


def statistics_view(request):
    """Detailed statistics view with session-based stats"""
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    
    # Get session statistics
    session_stats = get_session_statistics(session_key)
    
    # Get global statistics for comparison
    processing_stats = get_processing_statistics()
    
    # Get daily statistics for the last 30 days
    from datetime import timedelta
    from django.utils import timezone
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    daily_stats = ProcessingStatistics.objects.filter(
        date__gte=thirty_days_ago
    ).order_by('-date')
    
    # Get recent activity for this session
    recent_activity = session_stats.get('recent_activity', [])
    
    return render(request, 'ocr/statistics.html', {
        'session_stats': session_stats,
        'processing_stats': processing_stats,
        'daily_stats': daily_stats,
        'recent_activity': recent_activity,
        'session_total_size_formatted': get_file_size_formatted(session_stats.get('total_size', 0)),
        'global_total_size_formatted': get_file_size_formatted(
            processing_stats['overall'].get('total_size', 0) or 0
        )
    })
def search_view(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                if query.lower() in file.lower():
                    rel_path = os.path.relpath(os.path.join(root, file), settings.MEDIA_ROOT)
                    results.append({
                        'name': file,
                        'path': os.path.join(settings.MEDIA_URL, rel_path).replace('\\', '/')
                    })

    return render(request, 'search.html', {
        'query': query,
        'results': results,
    })

upload_dir = r'D:\File-manager-application\ocr\incoming-scan'
os.makedirs(upload_dir, exist_ok=True)