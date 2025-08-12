from django.db import models
import os

def scanned_file_path(instance, filename):
    # Rename file to match the system’s naming logic
    return f'scanned/{filename}'

class ScannedFile(models.Model):
    original_filename = models.CharField(max_length=255)
    renamed_filename = models.CharField(max_length=255, unique=True)
    uploaded_file = models.FileField(upload_to=scanned_file_path)
    scanned_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.renamed_filename

    def delete(self, *args, **kwargs):
        # Remove file from storage when record is deleted
        if self.uploaded_file and os.path.isfile(self.uploaded_file.path):
            os.remove(self.uploaded_file.path)
        super().delete(*args, **kwargs)
