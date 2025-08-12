"""
Utility functions for tracking file processing statistics
"""
from django.utils import timezone
from django.db.models import F, Count, Sum, Q
from .models import FileProcessingLog, ProcessingStatistics, SessionStatistics
import os


def log_file_processing(original_filename, status, final_filename=None, file_size=0, 
                       extracted_name=None, extracted_account=None, file_path=None, 
                       error_message=None, session_key=None):
    """
    Log file processing activity with session tracking
    """
    try:
        # Create processing log entry
        FileProcessingLog.objects.create(
            original_filename=original_filename,
            final_filename=final_filename,
            file_size=file_size,
            status=status,
            extracted_name=extracted_name,
            extracted_account=extracted_account,
            file_path=file_path,
            error_message=error_message
        )
        
        # Update daily statistics
        today = timezone.now().date()
        stats, created = ProcessingStatistics.objects.get_or_create(
            date=today,
            defaults={
                'total_uploaded': 0,
                'fully_indexed': 0,
                'partially_indexed': 0,
                'failed': 0,
                'total_file_size': 0
            }
        )
        
        # Update session statistics if session_key provided
        if session_key:
            session_stats, created = SessionStatistics.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'total_uploaded': 0,
                    'fully_indexed': 0,
                    'partially_indexed': 0,
                    'failed': 0,
                    'total_file_size': 0,
                    'first_upload': timezone.now(),
                    'last_upload': timezone.now()
                }
            )
            
            # Update session counters
            now = timezone.now()
            session_stats.last_upload = now
            if session_stats.first_upload is None:
                session_stats.first_upload = now
                
            if status == 'uploaded':
                session_stats.total_uploaded = F('total_uploaded') + 1
                session_stats.total_file_size = F('total_file_size') + file_size
            elif status == 'fully_indexed':
                session_stats.fully_indexed = F('fully_indexed') + 1
            elif status == 'partially_indexed':
                session_stats.partially_indexed = F('partially_indexed') + 1
            elif status == 'failed':
                session_stats.failed = F('failed') + 1
                
            session_stats.save()
        
        # Update daily counters
        if status == 'uploaded':
            stats.total_uploaded = F('total_uploaded') + 1
            stats.total_file_size = F('total_file_size') + file_size
        elif status == 'fully_indexed':
            stats.fully_indexed = F('fully_indexed') + 1
        elif status == 'partially_indexed':
            stats.partially_indexed = F('partially_indexed') + 1
        elif status == 'failed':
            stats.failed = F('failed') + 1
            
        stats.save()
        
    except Exception as e:
        print(f"Error logging file processing: {e}")


def get_session_statistics(session_key):
    """
    Get session-specific statistics
    """
    try:
        session_stats, created = SessionStatistics.objects.get_or_create(
            session_key=session_key,
            defaults={
                'total_uploaded': 0,
                'fully_indexed': 0,
                'partially_indexed': 0,
                'failed': 0,
                'total_file_size': 0
            }
        )
        
        # Get recent activity for this session
        recent_activity = FileProcessingLog.objects.filter(
            processed_at__gte=session_stats.created_at
        ).order_by('-processed_at')[:10]
        
        return {
            'session': session_stats,
            'recent_activity': recent_activity,
            'total_files': session_stats.total_uploaded,
            'fully_indexed': session_stats.fully_indexed,
            'partially_indexed': session_stats.partially_indexed,
            'failed': session_stats.failed,
            'total_size': session_stats.total_file_size,
            'average_size': session_stats.total_file_size / max(session_stats.total_uploaded, 1),
            'last_upload': session_stats.last_upload,
            'first_upload': session_stats.first_upload,
            'success_rate': session_stats.success_rate
        }
        
    except Exception as e:
        print(f"Error getting session statistics: {e}")
        return {
            'session': None,
            'recent_activity': [],
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


def reset_session_statistics(session_key):
    """
    Reset statistics for a specific session
    """
    try:
        SessionStatistics.objects.filter(session_key=session_key).delete()
        return True
    except Exception as e:
        print(f"Error resetting session statistics: {e}")
        return False


def get_processing_statistics():
    """
    Get comprehensive processing statistics (legacy function for compatibility)
    """
    try:
        # Get overall statistics
        overall_stats = FileProcessingLog.objects.aggregate(
            total_processed=Count('id'),
            total_uploaded=Count('id', filter=Q(status='uploaded')),
            total_fully_indexed=Count('id', filter=Q(status='fully_indexed')),
            total_partially_indexed=Count('id', filter=Q(status='partially_indexed')),
            total_failed=Count('id', filter=Q(status='failed')),
            total_size=Sum('file_size')
        )
        
        # Get daily statistics for the last 30 days
        from datetime import timedelta
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        daily_stats = ProcessingStatistics.objects.filter(
            date__gte=thirty_days_ago
        ).order_by('-date')[:30]
        
        # Get recent processing activity
        recent_activity = FileProcessingLog.objects.select_related().order_by('-processed_at')[:20]
        
        return {
            'overall': overall_stats,
            'daily': daily_stats,
            'recent_activity': recent_activity
        }
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {
            'overall': {},
            'daily': [],
            'recent_activity': []
        }


def get_file_size_formatted(size_bytes):
    """
    Convert file size to human readable format
    """
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
