"""
=============================================================================
Quizfy Signals
=============================================================================

This module contains Django signal handlers for the Quizfy application.

Signals:
--------
- create_default_site : Ensures a Site object exists for password reset emails

Why Signals?
------------
Django signals allow certain actions to happen automatically in response
to events like database migrations, model saves, user creation, etc.

The Site Framework:
------------------
Django's sites framework (django.contrib.sites) is required for password
reset emails to generate correct URLs. This signal ensures a Site object
always exists after migrations run.

Author: Quizfy Team
=============================================================================
"""

import logging

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.sites.models import Site


# =============================================================================
# LOGGING SETUP
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

@receiver(post_migrate)
def create_default_site(sender, **kwargs):
    """
    Create or update the default Site object after migrations run.
    
    This signal is triggered after each migration. It ensures that:
    1. A Site object with pk=1 exists (required by SITE_ID setting)
    2. The Site has reasonable default values
    
    Why is this needed?
    - Django's password reset emails use the sites framework to generate URLs
    - Without a Site object, password reset emails will fail
    - This ensures the Site is always configured, even on fresh deployments
    
    Note:
    - Only runs for django.contrib.sites migrations
    - Uses get_or_create to avoid duplicates
    - The domain can be updated manually in the admin for production
    
    Args:
        sender: The app that triggered the migration
        **kwargs: Additional signal arguments
    """
    # Only run for the sites app to avoid running multiple times
    if sender.name == 'django.contrib.sites':
        try:
            # Get or create the default site (pk=1 matches SITE_ID)
            site, created = Site.objects.get_or_create(
                pk=1,
                defaults={
                    'domain': 'example.com',  # Update in admin for production
                    'name': 'Quizfy Platform'
                }
            )
            
            if created:
                logger.info(f"[SITE] Created default site: {site.domain}")
            else:
                logger.debug(f"[SITE] Site already exists: {site.domain} ({site.name})")
                
        except Exception as e:
            logger.error(f"[SITE] Error configuring site: {e}")
