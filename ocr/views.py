from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import FileUploadForm
from .watcher import route_file
from .models import ScannedFile
from django.db.models import Q
import os


def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():

            # Save to top-level incoming-scan directory
            incoming_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../incoming-scan'))
            os.makedirs(incoming_dir, exist_ok=True)

            uploaded_file = request.FILES['file']
            incoming_path = os.path.join(incoming_dir, uploaded_file.name)

            with open(incoming_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            # Process it immediately
            try:
                dest_path = route_file(incoming_path)
                messages.success(request, f"File processed and moved to: {dest_path}")
            except Exception as e:
                messages.error(request, f"OCR failed: {e}")

            return redirect('upload_file')
    else:
        form = FileUploadForm()

    return render(request, 'ocr/upload.html', {'form': form})

def search_files(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = ScannedFile.objects.filter(
            Q(original_filename__icontains=query) |
            Q(renamed_filename__icontains=query) |
            Q(extracted_name__icontains=query) |
            Q(extracted_account__icontains=query)
        )

    return render(request, 'ocr/search.html', {
        'results': results,
        'query': query
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