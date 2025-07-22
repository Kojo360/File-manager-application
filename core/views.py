from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UploadedFile
from .forms import UploadForm

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def upload_file(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save()
            messages.success(request, f'File "{uploaded_file.original_filename}" uploaded successfully.')
            return redirect('upload')
    else:
        form = UploadForm()
    return render(request, 'core/upload.html', {'form': form})
