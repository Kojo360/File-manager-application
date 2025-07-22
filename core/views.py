# ocr/views.py
from django.shortcuts import render
from .models import ScannedFile
from django.db.models import Q

def search_files(request):
    query = request.GET.get('q')
    results = []

    if query:
        results = ScannedFile.objects.filter(
            Q(original_filename__icontains=query) |
            Q(new_filename__icontains=query) |
            Q(content__icontains=query)
        )

    return render(request, 'search.html', {'results': results, 'query': query})
