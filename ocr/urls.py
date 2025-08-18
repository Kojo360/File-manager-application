from django.urls import path
from . import views
from . import api_views

# Allow reversing as both namespaced and non-namespaced. Django will
# register the app namespace when included with namespace='ocr'.
app_name = 'ocr'

urlpatterns = [
    # Main application views
    path('', views.upload_file, name='upload_file'),
    path('test/', views.test_view, name='test_view'),
    path('debug-ocr/', views.debug_ocr, name='debug_ocr'),
    path('search/', views.search_files, name='search_files'),
    path('fully-indexed/', views.fully_indexed_files, name='fully_indexed_files'),
    path('partially-indexed/', views.partially_indexed_files, name='partially_indexed_files'),
    path('failed/', views.failed_files, name='failed_files'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('reset-statistics/', views.reset_statistics, name='reset_statistics'),
    path('file/<path:file_path>/', views.serve_processed_file, name='serve_file'),
    
    # Phase 2: Advanced Features
    path('bulk-operations/', views.bulk_operations_view, name='bulk_operations'),
    path('preview/<str:status_type>/<str:filename>/', views.file_preview_view, name='file_preview'),
    
    # User Management
    path('profile/', views.user_profile_view, name='user_profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    
    # Documentation
    path('api-docs/', views.api_documentation_view, name='api_documentation'),
    
    # API Endpoints
    path('api/status/', api_views.api_status, name='api_status'),
    path('api/statistics/', api_views.api_statistics, name='api_statistics'),
    path('api/files/', api_views.api_files_list, name='api_files_list'),
    path('api/bulk-operations/', api_views.api_bulk_operations, name='api_bulk_operations'),
    path('api/files/preview/<str:status_type>/<str:filename>/', api_views.api_file_preview, name='api_file_preview'),
]
