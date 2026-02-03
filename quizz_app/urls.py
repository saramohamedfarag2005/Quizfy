"""
=============================================================================
Quizfy Main URL Configuration
=============================================================================

This module defines the root URL configuration for the Quizfy project.

URL Structure:
--------------
/admin/          - Django admin interface
/                - All quiz app URLs (delegated to quizzes.urls)
/media/<path>    - Media file serving (user uploads)

Media File Handling:
-------------------
Media files (user uploads like quiz images and file submissions) are served
with a custom handler that returns 404 for missing files instead of 500.
This gracefully handles files that were uploaded before Cloudinary was
configured but were lost during Render redeploys.

Author: Quizfy Team
=============================================================================
"""

import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import Http404


# =============================================================================
# CUSTOM MEDIA FILE SERVER
# =============================================================================

def safe_serve_media(request, path, document_root=None):
    """
    Serve media files with proper error handling.
    
    Returns 404 (not found) instead of 500 (server error) when a file
    doesn't exist. This is important because:
    
    1. Files uploaded before Cloudinary integration may be lost after
       Render redeploys (ephemeral filesystem)
    2. A 404 is more informative than a 500 error
    3. Prevents confusing error pages for users
    
    Args:
        request: The HTTP request
        path: Path to the media file (relative to MEDIA_ROOT)
        document_root: Base directory for media files (defaults to MEDIA_ROOT)
    
    Returns:
        FileResponse for the requested file
        
    Raises:
        Http404: If the file doesn't exist
    """
    if document_root is None:
        document_root = settings.MEDIA_ROOT
    
    # Build full path and check existence
    full_path = os.path.join(document_root, path)
    if not os.path.exists(full_path):
        raise Http404(f"Media file not found: {path}")
    
    return serve(request, path, document_root=document_root)


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Django admin interface
    path('admin/', admin.site.urls),
    
    # All quiz application URLs (see quizzes/urls.py for details)
    path("", include("quizzes.urls")),
]


# =============================================================================
# MEDIA FILE URL PATTERNS
# =============================================================================

# Serve media files with safe error handling
# This handles files uploaded locally (before Cloudinary) with proper 404s
urlpatterns += [
    re_path(
        r'^media/(?P<path>.*)$', 
        safe_serve_media, 
        {'document_root': settings.MEDIA_ROOT}
    ),
]

# Additional static file serving in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
