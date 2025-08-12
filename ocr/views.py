from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils.encoding import smart_str
from .forms import FileUploadForm
from .utils import log_file_processing, get_processing_statistics, get_file_size_formatted
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../core/ocr')))
from watcher import route_file
from .models import ScannedFile, FileProcessingLog, ProcessingStatistics
from django.db.models import Q
import os


def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():

            # Save to top-level incoming-scan directory
            incoming_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../incoming-scan'))
            os.makedirs(incoming_dir, exist_ok=True)

            uploaded_files = request.FILES.getlist('files')
            
            # Limit to 100 files
            if len(uploaded_files) > 100:
                messages.error(request, "You can upload a maximum of 100 files at once.")
                return redirect('upload_file')

            processed_files = []
            failed_files = []

            for uploaded_file in uploaded_files:
                incoming_path = os.path.join(incoming_dir, uploaded_file.name)
                
                # Get file size
                file_size = uploaded_file.size

                # Save the uploaded file
                with open(incoming_path, 'wb+') as dest:
                    for chunk in uploaded_file.chunks():
                        dest.write(chunk)

                # Log the upload
                log_file_processing(
                    original_filename=uploaded_file.name,
                    status='uploaded',
                    file_size=file_size
                )

                # Process it immediately
                try:
                    dest_path = route_file(incoming_path)
                    
                    # Determine processing status based on destination
                    if 'fully_indexed' in dest_path:
                        status = 'fully_indexed'
                    elif 'partially_indexed' in dest_path:
                        status = 'partially_indexed'
                    else:
                        status = 'failed'
                    
                    # Log the processing result
                    final_filename = os.path.basename(dest_path) if dest_path else None
                    log_file_processing(
                        original_filename=uploaded_file.name,
                        status=status,
                        final_filename=final_filename,
                        file_path=dest_path,
                        file_size=file_size
                    )
                    
                    processed_files.append(f"{uploaded_file.name} → {final_filename}")
                except Exception as e:
                    # Log the failure
                    log_file_processing(
                        original_filename=uploaded_file.name,
                        status='failed',
                        error_message=str(e),
                        file_size=file_size
                    )
                    failed_files.append(f"{uploaded_file.name}: {e}")

            # Show summary message
            if processed_files:
                messages.success(request, f"Successfully processed {len(processed_files)} files.")
            if failed_files:
                messages.error(request, f"Failed to process {len(failed_files)} files: {', '.join(failed_files[:5])}")

            return redirect('upload_file')
    else:
        form = FileUploadForm()

    return render(request, 'ocr/upload.html', {'form': form})

def search_files(request):
    query = request.GET.get('q', '').strip()
    
    # Get the absolute paths to the three directories
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    FULLY_INDEXED_DIR = os.path.join(BASE_DIR, "fully_indexed")
    PARTIAL_INDEXED_DIR = os.path.join(BASE_DIR, "partially_indexed")
    FAILED_DIR = os.path.join(BASE_DIR, "failed")
    
    # Ensure directories exist
    for directory in [FULLY_INDEXED_DIR, PARTIAL_INDEXED_DIR, FAILED_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    def get_files_from_directory(directory_path, status):
        """Get all files from a directory and return them with their status"""
        files = []
        if os.path.exists(directory_path):
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    # Only include files that match the search query if provided
                    if not query or query.lower() in filename.lower():
                        file_info = {
                            'name': filename,
                            'path': file_path,
                            'status': status,
                            'size': os.path.getsize(file_path),
                            'modified': os.path.getmtime(file_path)
                        }
                        files.append(file_info)
        return files
    
    # Get files from all directories
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
        'has_query': bool(query)
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

def statistics_view(request):
    """Detailed statistics view"""
    processing_stats = get_processing_statistics()
    
    # Get daily statistics for the last 30 days
    from datetime import timedelta
    from django.utils import timezone
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    daily_stats = ProcessingStatistics.objects.filter(
        date__gte=thirty_days_ago
    ).order_by('-date')
    
    # Get recent activity
    recent_activity = FileProcessingLog.objects.order_by('-processed_at')[:50]
    
    # Calculate success rates
    if processing_stats['overall'].get('total_processed', 0) > 0:
        success_rate = round(
            ((processing_stats['overall'].get('total_fully_indexed', 0) + 
              processing_stats['overall'].get('total_partially_indexed', 0)) / 
             processing_stats['overall'].get('total_processed', 1)) * 100, 1
        )
    else:
        success_rate = 0
    
    return render(request, 'ocr/statistics.html', {
        'processing_stats': processing_stats,
        'daily_stats': daily_stats,
        'recent_activity': recent_activity,
        'success_rate': success_rate,
        'total_size_formatted': get_file_size_formatted(
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