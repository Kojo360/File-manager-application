"""
Authentication Views
===================
Custom login/logout views with role-based redirects.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from core.auth_decorators import admin_required

@csrf_protect
def custom_login(request):
    """
    Custom login view with role-based redirects.
    """
    if request.user.is_authenticated:
        # Redirect based on user role
        if request.user.is_staff or request.user.is_superuser:
            return redirect('ocr:upload_file')  # Admin goes to upload dashboard
        else:
            return redirect('ocr:search_files')  # Regular user goes to search
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Role-based redirect
            if user.is_staff or user.is_superuser:
                messages.success(request, f'Welcome, Admin {user.get_full_name() or user.username}!')
                return redirect('ocr:upload_file')  # Admin dashboard
            else:
                messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
                return redirect('ocr:search_files')  # Search interface
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

def custom_logout(request):
    """
    Custom logout view.
    """
    username = request.user.username if request.user.is_authenticated else 'User'
    logout(request)
    messages.success(request, f'Goodbye, {username}! You have been logged out.')
    return redirect('core:landing')

@admin_required
def user_management(request):
    """
    Admin-only user management view.
    """
    users = User.objects.all().order_by('username')
    
    context = {
        'users': users,
        'total_users': users.count(),
        'admin_users': users.filter(is_staff=True).count(),
        'regular_users': users.filter(is_staff=False).count(),
    }
    
    return render(request, 'core/user_management.html', context)

@admin_required
def create_user(request):
    """
    Admin-only user creation view.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        is_admin = request.POST.get('is_admin') == 'on'
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            if is_admin:
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            messages.success(request, f'User {username} created successfully!')
            return redirect('core:user_management')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'core/create_user.html')

def user_profile(request):
    """
    User profile view (accessible to all authenticated users).
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {
        'user': request.user,
        'is_admin': request.user.is_staff or request.user.is_superuser,
    }
    
    return render(request, 'core/user_profile.html', context)

def check_permissions(request):
    """
    API endpoint to check user permissions.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False})
    
    permissions = {
        'authenticated': True,
        'is_admin': request.user.is_staff or request.user.is_superuser,
        'is_superuser': request.user.is_superuser,
        'username': request.user.username,
        'full_name': request.user.get_full_name(),
        'permissions': {
            'can_upload': request.user.is_staff or request.user.is_superuser,
            'can_delete': request.user.is_staff or request.user.is_superuser,
            'can_manage_users': request.user.is_superuser,
            'can_view_statistics': request.user.is_staff or request.user.is_superuser,
            'can_search': True,  # All users can search
            'can_download': True,  # All users can download
            'can_view': True,  # All users can view
        }
    }
    
    return JsonResponse(permissions)
