"""
=============================================================================
Quizfy Application Configuration
=============================================================================

This module configures the Django application for the quizzes app.

The QuizzesConfig class:
- Sets the application name
- Imports signal handlers when the app is ready

Author: Quizfy Team
=============================================================================
"""

from django.apps import AppConfig


class QuizzesConfig(AppConfig):
    """
    Django application configuration for the Quizzes app.
    
    This class is referenced in INSTALLED_APPS as 'quizzes' and handles
    app-specific initialization when Django starts up.
    """
    
    # Application identifier (used by Django)
    name = 'quizzes'
    
    # Human-readable name for the admin
    verbose_name = 'Quizfy Quiz Application'
    
    # Default primary key field type for models
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """
        Called when Django has finished loading the application.
        
        This method is used to:
        1. Import and register signal handlers
        2. Perform any other app initialization
        
        Note: Signals must be imported here (not at module level) to avoid
        import errors and ensure they're registered at the right time.
        """
        # Import signals to register the post_migrate handler
        # This ensures the Site object is created for password reset emails
        import quizzes.signals  # noqa: F401
