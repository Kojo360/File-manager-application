from django.urls import path
from . import views

app_name = 'ocr'

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('test/', views.test_view, name='test_view'),  # Add test endpoint
    path('debug-ocr/', views.debug_ocr, name='debug_ocr'),  # Add OCR debug endpoint
    path('search/', views.search_files, name='search_files'),
    path('fully-indexed/', views.fully_indexed_files, name='fully_indexed_files'),
    path('partially-indexed/', views.partially_indexed_files, name='partially_indexed_files'),
    path('failed/', views.failed_files, name='failed_files'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('reset-statistics/', views.reset_statistics, name='reset_statistics'),
    path('file/<path:file_path>/', views.serve_processed_file, name='serve_file'),
]
