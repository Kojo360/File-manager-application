from django.db import models
from django.db import models

class UploadedFile(models.Model):
    original_filename = models.CharField(max_length=255)
    renamed_filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)
    image_file = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.renamed_filename

# Create your models here.
