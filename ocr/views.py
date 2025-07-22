import os
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import FileUploadForm
from django.conf import settings

def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            incoming_path = os.path.join(settings.MEDIA_ROOT, 'incoming-scan', uploaded_file.name)

            # Save the uploaded file to incoming-scan
            with open(incoming_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            messages.success(request, f"File '{uploaded_file.name}' uploaded and sent for OCR processing.")
            return redirect('upload')  # redirect to the same page

    else:
        form = FileUploadForm()

    return render(request, 'ocr/upload.html', {'form': form})
