"""
REST API Views for File Manager Application
Provides programmatic access to file management operations
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.utils.decorators import method_decorator
from django.views import View
import json
import os
from .models import FileProcessingLog, ProcessingStatistics
from .utils import get_processing_statistics, log_file_processing

@api_view(['GET'])
def api_status(request):
    """API health check endpoint"""
    return Response({
        'status': 'operational',
        'version': '2.0.0',
        'features': [
            'file_upload',
            'bulk_operations',
            'search',
            'statistics',
            'preview'
        ]
    })

@api_view(['GET'])
def api_statistics(request):
    """Get comprehensive file processing statistics"""
    try:
        stats = get_processing_statistics()
        
        # Get recent activity
        recent_activity = FileProcessingLog.objects.order_by('-processed_at')[:20]
        activity_data = []
        
        for activity in recent_activity:
            activity_data.append({
                'id': activity.id,
                'original_filename': activity.original_filename,
                'status': activity.status,
                'file_size': activity.file_size,
                'processed_at': activity.processed_at.isoformat(),
                'extracted_name': activity.extracted_name,
                'extracted_account': activity.extracted_account
            })
        
        return Response({
            'global_statistics': stats,
            'recent_activity': activity_data,
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def api_files_list(request):
    """List all files with filtering and pagination"""
    try:
        # Get query parameters
        query = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Get base directories
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        directories = {
            'fully_indexed': os.path.join(BASE_DIR, "fully_indexed"),
            'partially_indexed': os.path.join(BASE_DIR, "partially_indexed"),
            'failed': os.path.join(BASE_DIR, "failed")
        }
        
        files_data = []
        
        for status_type, directory in directories.items():
            if status_filter and status_filter != status_type:
                continue
                
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        # Apply search filter
                        if query and query.lower() not in filename.lower():
                            continue
                        
                        file_stat = os.stat(file_path)
                        files_data.append({
                            'name': filename,
                            'status': status_type,
                            'size': file_stat.st_size,
                            'modified': file_stat.st_mtime,
                            'download_url': f'/api/files/download/{status_type}/{filename}/'
                        })
        
        # Sort by modification time
        files_data.sort(key=lambda x: x['modified'], reverse=True)
        
        # Pagination
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_files = files_data[start_index:end_index]
        
        return Response({
            'files': paginated_files,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(files_data),
                'pages': (len(files_data) + per_page - 1) // per_page
            },
            'filters': {
                'query': query,
                'status': status_filter
            }
        })
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@csrf_exempt
def api_bulk_operations(request):
    """Handle bulk operations on files"""
    try:
        data = json.loads(request.body)
        operation = data.get('operation')
        file_list = data.get('files', [])
        
        if not operation or not file_list:
            return Response({
                'error': 'Operation and files list are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        results = []
        
        for file_info in file_list:
            filename = file_info.get('name')
            file_status = file_info.get('status')
            
            if not filename or not file_status:
                results.append({
                    'file': filename,
                    'success': False,
                    'error': 'Invalid file information'
                })
                continue
            
            directory = os.path.join(BASE_DIR, file_status)
            file_path = os.path.join(directory, filename)
            
            try:
                if operation == 'delete':
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        results.append({
                            'file': filename,
                            'success': True,
                            'operation': 'deleted'
                        })
                    else:
                        results.append({
                            'file': filename,
                            'success': False,
                            'error': 'File not found'
                        })
                
                elif operation == 'reprocess':
                    # Move file back to incoming-scan for reprocessing
                    incoming_dir = os.path.join(BASE_DIR, 'incoming-scan')
                    os.makedirs(incoming_dir, exist_ok=True)
                    
                    new_path = os.path.join(incoming_dir, filename)
                    if os.path.exists(file_path):
                        import shutil
                        shutil.move(file_path, new_path)
                        results.append({
                            'file': filename,
                            'success': True,
                            'operation': 'queued_for_reprocessing'
                        })
                    else:
                        results.append({
                            'file': filename,
                            'success': False,
                            'error': 'File not found'
                        })
                
                else:
                    results.append({
                        'file': filename,
                        'success': False,
                        'error': f'Unknown operation: {operation}'
                    })
            
            except Exception as e:
                results.append({
                    'file': filename,
                    'success': False,
                    'error': str(e)
                })
        
        return Response({
            'operation': operation,
            'results': results,
            'summary': {
                'total': len(file_list),
                'successful': len([r for r in results if r['success']]),
                'failed': len([r for r in results if not r['success']])
            }
        })
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def api_file_preview(request, status_type, filename):
    """Get file preview information and metadata"""
    try:
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        directory = os.path.join(BASE_DIR, status_type)
        file_path = os.path.join(directory, filename)
        
        if not os.path.exists(file_path):
            return Response({
                'error': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        file_stat = os.stat(file_path)
        
        # Get processing log information
        log_entry = FileProcessingLog.objects.filter(
            original_filename=filename
        ).first()
        
        # Basic file information
        file_info = {
            'name': filename,
            'status': status_type,
            'size': file_stat.st_size,
            'size_formatted': _format_file_size(file_stat.st_size),
            'modified': file_stat.st_mtime,
            'path': file_path,
            'extension': os.path.splitext(filename)[1].lower()
        }
        
        # Add extracted information if available
        if log_entry:
            file_info.update({
                'extracted_name': log_entry.extracted_name,
                'extracted_account': log_entry.extracted_account,
                'processing_date': log_entry.processed_at.isoformat(),
                'error_message': log_entry.error_message
            })
        
        # Add preview capabilities based on file type
        if file_info['extension'] in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            file_info['preview_type'] = 'image'
            file_info['can_preview'] = True
        elif file_info['extension'] == '.pdf':
            file_info['preview_type'] = 'pdf'
            file_info['can_preview'] = True
        else:
            file_info['preview_type'] = 'unknown'
            file_info['can_preview'] = False
        
        return Response(file_info)
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

# Django timezone import for API views
from django.utils import timezone
