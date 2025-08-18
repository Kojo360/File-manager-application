from django.urls import path
from . import views, auth_views

app_name = 'core'

urlpatterns = [
    # Landing page and public search
    path('', views.landing_page, name='landing'),
    path('search/', views.search_results, name='search_results'),
    
    # Core functionality
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.search_files, name='search_files'),
    
    # Authentication
    path('login/', auth_views.custom_login, name='login'),
    path('logout/', auth_views.custom_logout, name='logout'),
    path('profile/', auth_views.user_profile, name='user_profile'),
    
    # Admin-only user management
    path('admin/users/', auth_views.user_management, name='user_management'),
    path('admin/users/create/', auth_views.create_user, name='create_user'),
    
    # API endpoints
    path('api/permissions/', auth_views.check_permissions, name='check_permissions'),
]