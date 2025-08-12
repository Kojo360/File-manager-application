"""
Utility functions for tracking file processing statistics
"""
from django.utils import timezone
from django.db.models import F, Count, Sum, Q
from .models import FileProcessingLog, ProcessingStatistics
import os


def log_file_processing(original_filename, status, final_filename=None, file_size=0, 
                       extracted_name=None, extracted_account=None, file_path=None, 
                       error_message=None):
    """
    Log file processing activity
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
        
        # Update counters based on status
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


def get_processing_statistics():
    """
    Get comprehensive processing statistics
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
