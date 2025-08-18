"""
Authentication and Authorization Decorators
===========================================
Provides role-based access control for the file manager application.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    """
    Decorator that requires the user to be an admin (staff or superuser).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "⚠️ Admin access required. You can search and download files below.")
            return redirect('ocr:search_files')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def regular_user_allowed(view_func):
    """
    Decorator that allows both regular users and admins.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def public_access_allowed(view_func):
    """
    Decorator that allows public access (no authentication required).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_only(view_func):
    """
    Strict admin-only decorator.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        if not request.user.is_superuser:
            messages.error(request, "⚠️ Superuser access required.")
            return redirect('ocr:search_files')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def is_admin(user):
    """
    Check if user is admin (staff or superuser).
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def is_regular_user(user):
    """
    Check if user is a regular user (not admin).
    """
    return user.is_authenticated and not (user.is_staff or user.is_superuser)

# User test decorators
admin_required_test = user_passes_test(is_admin, login_url='core:login')
regular_user_test = user_passes_test(lambda u: u.is_authenticated, login_url='core:login')
