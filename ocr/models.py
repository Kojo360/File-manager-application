from django.db import models
from django.utils import timezone
import os

def scanned_file_path(instance, filename):
    # Rename file to match the system's naming logic
    return f'scanned/{filename}'

class ScannedFile(models.Model):
    original_name = models.CharField(max_length=255)  # Keep existing field name
    renamed_file = models.CharField(max_length=255)   # Keep existing field name
    file_path = models.FileField(upload_to='scanned_files/')  # Keep existing upload path
    extracted_text = models.TextField()  # Keep existing field name
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.renamed_file

    def delete(self, *args, **kwargs):
        # Remove file from storage when record is deleted
        if self.file_path and os.path.isfile(self.file_path.path):
            os.remove(self.file_path.path)
        super().delete(*args, **kwargs)

class FileProcessingLog(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('fully_indexed', 'Fully Indexed'),
        ('partially_indexed', 'Partially Indexed'),
        ('failed', 'Failed'),
    ]
    
    original_filename = models.CharField(max_length=255)
    final_filename = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(default=0)  # Size in bytes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    extracted_name = models.CharField(max_length=255, blank=True, null=True)
    extracted_account = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-processed_at']
        
    def __str__(self):
        return f"{self.original_filename} - {self.status}"

class ProcessingStatistics(models.Model):
    """Daily processing statistics"""
    date = models.DateField(unique=True, default=timezone.now)
    total_uploaded = models.IntegerField(default=0)
    fully_indexed = models.IntegerField(default=0)
    partially_indexed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    total_file_size = models.BigIntegerField(default=0)  # Total size in bytes
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"Stats for {self.date}"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_uploaded == 0:
            return 0
        return round(((self.fully_indexed + self.partially_indexed) / self.total_uploaded) * 100, 1)


class SessionStatistics(models.Model):
    """Session-based statistics that reset for each new device/session"""
    session_key = models.CharField(max_length=40, unique=True)  # Django session key
    total_uploaded = models.IntegerField(default=0)
    fully_indexed = models.IntegerField(default=0)
    partially_indexed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    total_file_size = models.BigIntegerField(default=0)
    first_upload = models.DateTimeField(null=True, blank=True)
    last_upload = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_upload']
        
    def __str__(self):
        return f"Session stats for {self.session_key[:8]}..."
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_uploaded == 0:
            return 0
        return round(((self.fully_indexed + self.partially_indexed) / self.total_uploaded) * 100, 1)
